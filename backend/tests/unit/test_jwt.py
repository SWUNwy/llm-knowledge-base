"""JWT Token 工具测试"""

from datetime import timedelta

import pytest

from src.auth.jwt import create_token, decode_token, verify_token


class TestCreateToken:
    """测试创建 JWT token"""

    def test_create_and_decode_token(self) -> None:
        """创建 token 并解码，验证数据匹配"""
        data = {"sub": "user123", "role": "admin"}
        token = create_token(data)

        # token 应该是字符串
        assert isinstance(token, str)
        # token 应该是非空字符串
        assert len(token) > 0

        # 解码 token
        payload = decode_token(token)

        # 验证数据匹配
        assert payload["sub"] == data["sub"]
        assert payload["role"] == data["role"]

    def test_token_contains_exp(self) -> None:
        """验证 token 包含过期时间"""
        data = {"sub": "user123"}
        token = create_token(data)

        payload = decode_token(token)

        # 验证 token 包含 exp 字段
        assert "exp" in payload
        # exp 应该是整数（时间戳）
        assert isinstance(payload["exp"], int)

    def test_create_token_with_custom_expiry(self) -> None:
        """测试自定义过期时间"""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=1)
        token = create_token(data, expires_delta=expires_delta)

        payload = decode_token(token)

        # 验证 token 有效
        assert payload["sub"] == data["sub"]


class TestVerifyToken:
    """测试验证 token"""

    def test_verify_token_valid(self) -> None:
        """验证有效 token 返回 payload"""
        data = {"sub": "user123", "email": "user@example.com"}
        token = create_token(data)

        result = verify_token(token)

        # 验证返回 payload
        assert result is not None
        assert result["sub"] == data["sub"]
        assert result["email"] == data["email"]

    def test_verify_token_invalid(self) -> None:
        """验证无效 token 返回 None"""
        invalid_token = "invalid.token.string"

        result = verify_token(invalid_token)

        # 验证返回 None
        assert result is None

    def test_verify_token_malformed(self) -> None:
        """验证格式错误的 token 返回 None"""
        malformed_token = "not-a-valid-jwt-token"

        result = verify_token(malformed_token)

        # 验证返回 None
        assert result is None

    def test_verify_token_empty_string(self) -> None:
        """验证空字符串 token 返回 None"""
        result = verify_token("")

        # 验证返回 None
        assert result is None
