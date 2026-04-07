"""密码哈希和验证"""

import bcrypt


def hash_password(password: str) -> str:
    """哈希密码"""
    # 将密码转换为字节
    password_bytes = password.encode("utf-8")
    # 生成盐并哈希密码
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # 返回字符串形式的哈希
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 将密码和哈希转换为字节
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    # 验证密码
    return bcrypt.checkpw(password_bytes, hashed_bytes)
