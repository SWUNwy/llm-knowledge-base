"""LLM Client 测试"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from litellm.exceptions import RateLimitError, Timeout

from src.llm.client import LLMClient
from src.utils.retry import retry_with_backoff


class TestRetryWithBackoff:
    """测试指数退避重试装饰器"""

    def test_retry_success_on_first_try(self) -> None:
        """验证第一次就成功时不重试"""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_success_after_failures(self) -> None:
        """验证失败后重试成功"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def eventually_successful_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("temporary error")
            return "success"

        result = eventually_successful_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self) -> None:
        """验证重试次数耗尽后抛出异常"""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_failing_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ValueError("persistent error")

        with pytest.raises(ValueError, match="persistent error"):
            always_failing_func()

        assert call_count == 3  # initial + 2 retries

    def test_retry_specific_exceptions(self) -> None:
        """验证只重试指定异常"""
        call_count = 0

        @retry_with_backoff(
            max_retries=3, base_delay=0.01, exceptions=(ValueError,)
        )
        def raise_type_error() -> None:
            nonlocal call_count
            call_count += 1
            raise TypeError("not a ValueError")

        with pytest.raises(TypeError, match="not a ValueError"):
            raise_type_error()

        assert call_count == 1  # No retry for TypeError

    @pytest.mark.asyncio
    async def test_retry_async_success(self) -> None:
        """验证异步函数重试"""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        async def async_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("temporary error")
            return "async success"

        result = await async_func()
        assert result == "async success"
        assert call_count == 2


class TestBuildPrompt:
    """测试模板变量替换"""

    def test_build_prompt_simple(self) -> None:
        """验证简单变量替换"""
        client = LLMClient.__new__(LLMClient)
        template = "Hello, {name}!"
        variables = {"name": "World"}

        result = client._build_prompt(template, variables)

        assert result == "Hello, World!"

    def test_build_prompt_multiple_variables(self) -> None:
        """验证多个变量替换"""
        client = LLMClient.__new__(LLMClient)
        template = "{greeting}, {name}! Today is {day}."
        variables = {"greeting": "Hello", "name": "Alice", "day": "Monday"}

        result = client._build_prompt(template, variables)

        assert result == "Hello, Alice! Today is Monday."

    def test_build_prompt_missing_variable(self) -> None:
        """验证缺少变量时抛出异常"""
        client = LLMClient.__new__(LLMClient)
        template = "Hello, {name}! You are {age} years old."
        variables = {"name": "Bob"}  # Missing 'age'

        with pytest.raises(ValueError, match="Missing template variable: age"):
            client._build_prompt(template, variables)

    def test_build_prompt_no_variables(self) -> None:
        """验证没有变量的模板"""
        client = LLMClient.__new__(LLMClient)
        template = "This is a static message."
        variables: dict = {}

        result = client._build_prompt(template, variables)

        assert result == "This is a static message."

    def test_build_prompt_extra_variables(self) -> None:
        """验证多余变量被忽略"""
        client = LLMClient.__new__(LLMClient)
        template = "Hello, {name}!"
        variables = {"name": "Charlie", "unused": "value"}

        result = client._build_prompt(template, variables)

        assert result == "Hello, Charlie!"


class TestLLMClientGenerate:
    """测试LLM Client生成方法"""

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """验证成功生成响应"""
        with patch("src.llm.client.litellm") as mock_litellm:
            # Setup mock
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Generated response"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            client = LLMClient()
            result = await client.generate("Test prompt")

            assert result == "Generated response"
            mock_litellm.acompletion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_custom_model(self) -> None:
        """验证自定义模型参数"""
        with patch("src.llm.client.litellm") as mock_litellm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            client = LLMClient()
            await client.generate("Test prompt", model="gpt-4")

            call_args = mock_litellm.acompletion.call_args
            assert call_args[1]["model"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_generate_with_temperature(self) -> None:
        """验证temperature参数"""
        with patch("src.llm.client.litellm") as mock_litellm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            client = LLMClient()
            await client.generate("Test prompt", temperature=0.3)

            call_args = mock_litellm.acompletion.call_args
            assert call_args[1]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_generate_with_max_tokens(self) -> None:
        """验证max_tokens参数"""
        with patch("src.llm.client.litellm") as mock_litellm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            client = LLMClient()
            await client.generate("Test prompt", max_tokens=2000)

            call_args = mock_litellm.acompletion.call_args
            assert call_args[1]["max_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_generate_with_template(self) -> None:
        """验证模板构建"""
        with patch("src.llm.client.litellm") as mock_litellm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Response"
            mock_litellm.acompletion = AsyncMock(return_value=mock_response)

            client = LLMClient()
            template = "Summarize: {content}"
            variables = {"content": "Some text"}

            # Test with template (need to call _build_prompt first)
            prompt = client._build_prompt(template, variables)
            await client.generate(prompt)

            call_args = mock_litellm.acompletion.call_args
            assert "Summarize: Some text" in call_args[1]["messages"][0]["content"]


class TestLLMClientStream:
    """测试LLM Client流式生成方法"""

    @pytest.mark.asyncio
    async def test_stream_success(self) -> None:
        """验证流式生成"""
        with patch("src.llm.client.litellm") as mock_litellm:
            # Setup mock for streaming - acompletion returns async generator directly
            async def mock_stream(*args: object, **kwargs: object) -> object:
                chunks = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
                ]
                for chunk in chunks:
                    yield chunk

            mock_litellm.acompletion = MagicMock(return_value=mock_stream())

            client = LLMClient()
            chunks = []
            async for chunk in client.stream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello", " World", "!"]

    @pytest.mark.asyncio
    async def test_stream_empty_chunk(self) -> None:
        """验证空chunk被跳过"""
        with patch("src.llm.client.litellm") as mock_litellm:
            async def mock_stream(*args: object, **kwargs: object) -> object:
                chunks = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="World"))]),
                ]
                for chunk in chunks:
                    yield chunk

            mock_litellm.acompletion = MagicMock(return_value=mock_stream())

            client = LLMClient()
            chunks = []
            async for chunk in client.stream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello", "World"]


class TestLLMClientRetry:
    """测试LLM Client重试机制"""

    @pytest.mark.asyncio
    async def test_generate_retry_on_rate_limit(self) -> None:
        """验证Rate limit时重试"""
        with patch("src.llm.client.litellm") as mock_litellm:
            call_count = 0

            async def mock_completion(*args: object, **kwargs: object) -> object:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise RateLimitError(
                        message="Rate limit exceeded",
                        llm_provider="test",
                        model="test-model",
                    )
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = "Success"
                return mock_response

            mock_litellm.acompletion = mock_completion

            client = LLMClient()
            result = await client.generate("Test prompt")

            assert result == "Success"
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_generate_retry_on_timeout(self) -> None:
        """验证超时时重试"""
        with patch("src.llm.client.litellm") as mock_litellm:
            call_count = 0

            async def mock_completion(*args: object, **kwargs: object) -> object:
                nonlocal call_count
                call_count += 1
                if call_count < 2:
                    raise Timeout(
                        message="Request timeout",
                        llm_provider="test",
                        model="test-model",
                    )
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = "Success"
                return mock_response

            mock_litellm.acompletion = mock_completion

            client = LLMClient()
            result = await client.generate("Test prompt")

            assert result == "Success"
            assert call_count == 2
