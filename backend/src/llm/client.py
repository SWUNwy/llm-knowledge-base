from __future__ import annotations
"""LLM客户端模块

使用LiteLLM提供统一的LLM调用接口，支持多种模型提供商
"""

import logging
import re
from typing import Any, AsyncGenerator

import litellm
from litellm.exceptions import (
    APIConnectionError,
    AuthenticationError,
    ContextWindowExceededError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from src.config import get_settings
from src.errors import AppError, ErrorCode
from src.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端

    提供统一的LLM调用接口，支持：
    - 多种LLM提供商（OpenAI、Anthropic、Gemini、Ollama等）
    - 自动重试和错误处理
    - 流式和非流式响应
    - 模板变量替换
    """

    def __init__(self) -> None:
        """初始化LLM客户端

        从配置中读取API密钥并设置LiteLLM
        """
        settings = get_settings()

        # 设置API密钥
        if settings.gemini_api_key:
            litellm.api_key = settings.gemini_api_key
        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key
        if settings.ollama_base_url:
            litellm.set_verbose = True

        # 保存默认模型
        self.default_model = settings.llm_default_model
        self.ollama_base_url = settings.ollama_base_url

        # 配置LiteLLM
        litellm.drop_params = True  # 移除不支持的参数
        litellm.set_verbose = settings.app_env == "development"

        logger.info(f"LLM Client initialized with default model: {self.default_model}")

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        exceptions=(
            RateLimitError,
            Timeout,
            APIConnectionError,
            ServiceUnavailableError,
        ),
    )
    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """生成LLM响应（非流式）

        Args:
            prompt: 输入提示词
            model: 模型名称，默认使用配置中的默认模型
            temperature: 生成温度，0.0-1.0，越高越随机
            max_tokens: 最大生成token数

        Returns:
            生成的文本响应

        Raises:
            RateLimitError: API请求频率限制
            Timeout: 请求超时
            APIConnectionError: API连接错误
        """
        model_name = model or self.default_model

        # 对于Ollama模型，设置base_url
        api_base = None
        if model_name.startswith("ollama/") and self.ollama_base_url:
            api_base = self.ollama_base_url

        logger.debug(f"Generating with model: {model_name}, temperature: {temperature}")

        try:
            response = await litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                api_base=api_base,
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM returned empty response")

            logger.debug(f"Generated response length: {len(content)}")
            return content

        except AuthenticationError as e:
            logger.warning("LLM authentication failed: %s", e)
            raise AppError(ErrorCode.LLM_API_KEY_INVALID, detail=str(e))
        except RateLimitError as e:
            logger.warning("LLM rate limit exceeded: %s", e)
            raise AppError(ErrorCode.LLM_RATE_LIMIT, detail=str(e))
        except Timeout as e:
            logger.warning("LLM request timed out: %s", e)
            raise AppError(ErrorCode.LLM_TIMEOUT, detail=str(e))
        except APIConnectionError as e:
            logger.warning("LLM service connection error: %s", e)
            raise AppError(ErrorCode.LLM_SERVICE_DOWN, detail=str(e))
        except ServiceUnavailableError as e:
            logger.warning("LLM service unavailable: %s", e)
            raise AppError(ErrorCode.LLM_SERVICE_DOWN, detail=str(e))
        except Exception as e:
            logger.error("Unexpected LLM error: %s", e)
            raise AppError(ErrorCode.INTERNAL_ERROR, detail=str(e))

    async def stream(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncGenerator[str, None]:
        """流式生成LLM响应

        Args:
            prompt: 输入提示词
            model: 模型名称，默认使用配置中的默认模型
            temperature: 生成温度，0.0-1.0
            max_tokens: 最大生成token数

        Yields:
            生成的文本片段
        """
        model_name = model or self.default_model

        # 对于Ollama模型，设置base_url
        api_base = None
        if model_name.startswith("ollama/") and self.ollama_base_url:
            api_base = self.ollama_base_url

        logger.debug(f"Streaming with model: {model_name}")

        try:
            response = litellm.acompletion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                api_base=api_base,
            )

            async for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content

        except AuthenticationError as e:
            logger.warning("LLM authentication failed (stream): %s", e)
            raise AppError(ErrorCode.LLM_API_KEY_INVALID, detail=str(e))
        except RateLimitError as e:
            logger.warning("LLM rate limit exceeded (stream): %s", e)
            raise AppError(ErrorCode.LLM_RATE_LIMIT, detail=str(e))
        except Timeout as e:
            logger.warning("LLM request timed out (stream): %s", e)
            raise AppError(ErrorCode.LLM_TIMEOUT, detail=str(e))
        except APIConnectionError as e:
            logger.warning("LLM service connection error (stream): %s", e)
            raise AppError(ErrorCode.LLM_SERVICE_DOWN, detail=str(e))
        except ServiceUnavailableError as e:
            logger.warning("LLM service unavailable (stream): %s", e)
            raise AppError(ErrorCode.LLM_SERVICE_DOWN, detail=str(e))
        except Exception as e:
            logger.error("Unexpected LLM error (stream): %s", e)
            raise AppError(ErrorCode.INTERNAL_ERROR, detail=str(e))

    def _build_prompt(self, template: str, variables: dict[str, Any]) -> str:
        """构建提示词

        替换模板中的变量占位符

        Args:
            template: 包含变量占位符的模板字符串
            variables: 变量字典

        Returns:
            替换后的提示词

        Raises:
            ValueError: 模板中有未提供的变量
        """
        # 找出模板中的所有变量
        pattern = r"\{(\w+)\}"
        template_vars = set(re.findall(pattern, template))

        # 检查是否有缺失的变量
        missing_vars = template_vars - set(variables.keys())
        if missing_vars:
            raise ValueError(
                f"Missing template variable: {', '.join(sorted(missing_vars))}"
            )

        # 替换变量
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))

        return result
