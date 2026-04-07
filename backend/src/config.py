# backend/src/config.py
"""应用配置管理"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_port: int = 8000

    # Vault 配置
    vault_path: str

    # LLM 配置
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None
    llm_default_model: str = "gemini/gemini-pro"

    # Embedding 配置
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # 编译配置
    auto_compile: bool = True
    compile_batch_size: int = 5

    # 并发配置
    max_concurrent_tasks: int = 3

    # 日志配置
    log_level: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
