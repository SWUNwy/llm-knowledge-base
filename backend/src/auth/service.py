from __future__ import annotations
"""认证服务模块"""

from src.auth.jwt import create_token
from src.auth.password import hash_password, verify_password
from src.database import Database
from src.models.user import Token, User, UserCreate, UserLogin, create_user_id


class AuthService:
    """认证服务，处理用户注册、登录等业务逻辑"""

    def __init__(self, db: Database):
        """初始化认证服务

        Args:
            db: 数据库连接实例
        """
        self.db = db

    async def is_setup_complete(self) -> bool:
        """检查是否已完成初始账户设置

        Returns:
            如果已存在用户则返回 True
        """
        count = await self.db.count_users()
        return count > 0

    async def setup(self, user_create: UserCreate) -> Token:
        """创建初始管理员账户

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

    async def login(self, user_login: UserLogin) -> Token:
        """用户登录

        Args:
            user_login: 登录请求

        Returns:
            Token 包含 JWT access token

        Raises:
            ValueError: 如果用户名或密码无效
        """
        # 查找用户
        user_dict = await self.db.get_user_by_username(user_login.username)
        if not user_dict:
            raise ValueError("Invalid username or password")

        # 验证密码
        if not verify_password(user_login.password, user_dict["password_hash"]):
            raise ValueError("Invalid username or password")

        # 生成 JWT token
        token = create_token({"sub": user_dict["id"], "username": user_dict["username"]})

        return Token(access_token=token)

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
