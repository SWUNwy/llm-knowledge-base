from __future__ import annotations
"""JWT Token 工具"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from src.config import get_settings


def create_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """创建 JWT token

    Args:
        data: 要编码到 token 中的数据
        expires_delta: 过期时间间隔，如果不提供则默认 24 小时

    Returns:
        编码后的 JWT token 字符串
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)

    to_encode["exp"] = expire
    encoded_jwt = jwt.encode(to_encode, settings.app_secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """解码 JWT token

    Args:
        token: 要解码的 JWT token 字符串

    Returns:
        解码后的 payload 字典

    Raises:
        JWTError: 如果 token 无效或已过期
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
    return payload


def verify_token(token: str) -> dict[str, Any] | None:
    """验证 token，返回 payload 或 None

    Args:
        token: 要验证的 JWT token 字符串

    Returns:
        如果 token 有效则返回 payload 字典，否则返回 None
    """
    try:
        return decode_token(token)
    except JWTError:
        return None
