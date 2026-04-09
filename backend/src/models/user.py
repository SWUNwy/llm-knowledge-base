from __future__ import annotations
"""用户模型"""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field


class User(BaseModel):
    """用户"""

    id: str
    username: str
    password_hash: str
    created_at: datetime


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str = Field(..., min_length=1, description="用户名不能为空")
    password: str = Field(..., min_length=1, description="密码不能为空")


class UserLogin(BaseModel):
    """登录请求"""

    username: str = Field(..., min_length=1, description="用户名不能为空")
    password: str = Field(..., min_length=1, description="密码不能为空")


class Token(BaseModel):
    """Token 响应"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400


def create_user_id() -> str:
    """生成用户 ID"""
    return f"user-{uuid4().hex[:12]}"
