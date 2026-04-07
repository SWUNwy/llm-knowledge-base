"""密码工具测试"""

import pytest

from src.auth.password import hash_password, verify_password


class TestHashPassword:
    """测试密码哈希"""

    def test_hash_password(self) -> None:
        """验证哈希与原始密码不同"""
        password = "test_password_123"
        hashed = hash_password(password)

        # 哈希值应该与原始密码不同
        assert hashed != password
        # 哈希值应该是字符串
        assert isinstance(hashed, str)
        # 哈希值应该有合理的长度 (bcrypt 哈希通常为 60 个字符)
        assert len(hashed) == 60

    def test_hash_password_different_each_time(self) -> None:
        """验证同一密码每次哈希结果不同（由于盐值）"""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # 两次哈希结果应该不同（因为盐值不同）
        assert hash1 != hash2


class TestVerifyPassword:
    """测试密码验证"""

    def test_verify_password_correct(self) -> None:
        """验证正确密码通过验证"""
        password = "correct_password_456"
        hashed = hash_password(password)

        # 正确密码应该通过验证
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """验证错误密码失败"""
        password = "correct_password_456"
        wrong_password = "wrong_password_789"
        hashed = hash_password(password)

        # 错误密码应该验证失败
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self) -> None:
        """验证空密码"""
        password = "some_password"
        hashed = hash_password(password)

        # 空密码应该验证失败
        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self) -> None:
        """验证密码区分大小写"""
        password = "Password123"
        hashed = hash_password(password)

        # 大小写不同应该验证失败
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False
        # 正确大小写应该通过
        assert verify_password("Password123", hashed) is True
