"""FastAPI 认证依赖模块"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import verify_token
from src.auth.service import AuthService
from src.database import Database
from src.models.user import User

# Bearer token scheme for extracting Authorization header
security = HTTPBearer(auto_error=False)


async def get_db() -> Database:
    """获取数据库连接。

    此函数应在 FastAPI 应用启动时通过 app.state.db 设置数据库实例。
    在路由中通过依赖注入使用。

    注意：实际使用时需要在 main.py 中通过 app.dependency_overrides
    或自定义包装来提供数据库实例。
    """
    raise NotImplementedError("Database dependency must be overridden in main.py")


async def get_current_user(
    db: Database = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """提取并验证 JWT token，返回当前用户

    Args:
        db: 数据库连接
        credentials: HTTP Bearer credentials

    Returns:
        当前认证用户

    Raises:
        HTTPException: 如果未提供 token 或 token 无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证 token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从 token 中获取用户 ID
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 从数据库获取用户
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
