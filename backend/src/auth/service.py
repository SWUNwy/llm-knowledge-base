from __future__ import annotations
"""认证服务模块 - 支持 SaaS 云端认证"""

from pathlib import Path
from src.auth.cloud_auth import CloudAuthClient
from src.auth.jwt import create_token
from src.auth.password import hash_password, verify_password
from src.database import Database
from src.models.user import Token, User, UserCreate, UserLogin, create_user_id


class AuthService:
    """认证服务，处理用户注册、登录等业务逻辑"""

    def __init__(self, db: Database, vault_path: Path | None = None):
        """初始化认证服务

        Args:
            db: 数据库连接实例
            vault_path: Vault 路径（用于 SaaS 模式下保存 license token）
        """
        self.db = db
        self.vault_path = vault_path or Path('.')
        self.cloud_client = CloudAuthClient()

    async def is_setup_complete(self) -> bool:
        """检查是否已完成初始账户设置

        Returns:
            如果已存在用户则返回 True
        """
        count = await self.db.count_users()
        return count > 0

    async def setup(self, user_create: UserCreate) -> Token:
        """创建初始管理员账户（仅本地模式）

        Args:
            user_create: 用户创建请求

        Returns:
            Token 包含 JWT access token

        Raises:
            ValueError: 如果账户已存在
        """
        # 检查是否已有用户存在
        if await self.is_setup_complete():
            raise ValueError("Setup already complete. An account already exists.")

        # 生成用户 ID 并哈希密码
        user_id = create_user_id()
        password_hash = hash_password(user_create.password)

        # 创建用户
        await self.db.create_user(user_id, user_create.username, password_hash)

        # 生成 JWT token
        token = create_token({"sub": user_id, "username": user_create.username})

        return Token(access_token=token)

    async def login(self, user_login: UserLogin, device_id: str | None = None) -> dict:
        """用户登录 - 支持 SaaS 云端认证

        Args:
            user_login: 登录请求（email/password for SaaS）
            device_id: 设备 ID（SaaS 模式）

        Returns:
            Dict with access_token and optional license_token

        Raises:
            ValueError: 如果用户名或密码无效
        """
        # Try cloud login first
        try:
            result = await self.cloud_client.login(
                email=user_login.username,  # Using username field as email
                password=user_login.password,
                device_id=device_id
            )

            # Save license token locally
            license_token = result.get('license_token')
            if license_token:
                from src.license.manager import LicenseManager
                mgr = LicenseManager(self.vault_path)
                mgr.save_token(license_token, result.get('user', {}))

            return {
                'access_token': result.get('access_token'),
                'license_token': license_token,
                'tier': result.get('tier'),
                'user': result.get('user')
            }

        except Exception as cloud_error:
            # Fall back to local auth for backward compatibility
            user_dict = await self.db.get_user_by_username(user_login.username)
            if not user_dict:
                raise ValueError("Invalid username or password")

            if not verify_password(user_login.password, user_dict["password_hash"]):
                raise ValueError("Invalid username or password")

            token = create_token({
                "sub": user_dict["id"],
                "username": user_dict["username"]
            })

            return {'access_token': token}

    async def get_user_by_id(self, user_id: str) -> User | None:
        """通过 ID 获取用户

        Args:
            user_id: 用户 ID

        Returns:
            User 对象，如果未找到则返回 None
        """
        user_dict = await self.db.get_user_by_id(user_id)
        if not user_dict:
            return None

        return User(
            id=user_dict["id"],
            username=user_dict["username"],
            password_hash=user_dict["password_hash"],
            created_at=user_dict["created_at"],
        )
