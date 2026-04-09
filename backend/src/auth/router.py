from __future__ import annotations
"""认证路由模块"""

from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_user, get_db
from src.auth.service import AuthService
from src.database import Database
from src.models.user import Token, User, UserCreate, UserLogin

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/setup", response_model=Token)
async def setup_account(
    user_create: UserCreate,
    db: Database = Depends(get_db),
) -> Token:
    """初始账户设置

    创建第一个管理员账户。只有当系统中不存在任何用户时才能调用。

    Args:
        user_create: 用户创建请求（包含用户名和密码）
        db: 数据库连接

    Returns:
        JWT Token

    Raises:
        HTTPException: 400 如果账户已存在
    """
    auth_service = AuthService(db)
    try:
        token = await auth_service.setup(user_create)
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    db: Database = Depends(get_db),
) -> Token:
    """用户登录

    验证用户名和密码，返回 JWT token。

    Args:
        user_login: 登录请求（包含用户名和密码）
        db: 数据库连接

    Returns:
        JWT Token

    Raises:
        HTTPException: 401 如果用户名或密码无效
    """
    auth_service = AuthService(db)
    try:
        token = await auth_service.login(user_login)
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """用户登出

    登出操作在客户端完成（删除 token），服务端仅返回确认消息。

    Returns:
        成功消息
    """
    return {"message": "Successfully logged out"}
