import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest

from models.account import TenantAccountRole
from models.sso import SsoConfig, SsoConfigStatus, SsoProvider
from services.errors.account import AccountRegisterError
from services.sso_service import SsoService


class TestSsoService:
    def test_generate_sso_token(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"
        sso_config.token_expire_minutes = 60

        token = SsoService.generate_sso_token(
            sso_config=sso_config,
            user_identifier="user123",
            email="test@example.com",
            name="Test User",
        )

        assert token is not None
        assert isinstance(token, str)

        payload = jwt.decode(token, sso_config.secret_key, algorithms=["HS256"])
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Test User"
        assert payload["type"] == "sso_auth"
        assert payload["iss"] == f"dify_sso:{sso_config.id}"

    def test_generate_sso_token_with_additional_data(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"
        sso_config.token_expire_minutes = 60

        additional_data = {"department": "engineering", "role": "developer"}
        token = SsoService.generate_sso_token(
            sso_config=sso_config,
            user_identifier="user123",
            email="test@example.com",
            name="Test User",
            additional_data=additional_data,
        )

        payload = jwt.decode(token, sso_config.secret_key, algorithms=["HS256"])
        assert payload["data"] == additional_data

    def test_verify_sso_token_valid(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "sso_auth",
        }
        token = jwt.encode(payload_data, sso_config.secret_key, algorithm="HS256")

        result = SsoService.verify_sso_token(token, sso_config)

        assert result["sub"] == "user123"
        assert result["email"] == "test@example.com"
        assert result["name"] == "Test User"

    def test_verify_sso_token_expired(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "iat": datetime.now(UTC) - timedelta(hours=2),
            "type": "sso_auth",
        }
        token = jwt.encode(payload_data, sso_config.secret_key, algorithm="HS256")

        with pytest.raises(ValueError, match="Token has expired"):
            SsoService.verify_sso_token(token, sso_config)

    def test_verify_sso_token_invalid_type(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "invalid_type",
        }
        token = jwt.encode(payload_data, sso_config.secret_key, algorithm="HS256")

        with pytest.raises(ValueError, match="Invalid token type"):
            SsoService.verify_sso_token(token, sso_config)

    def test_verify_sso_token_invalid_issuer(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": "dify_sso:different-config-id",
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "sso_auth",
        }
        token = jwt.encode(payload_data, sso_config.secret_key, algorithm="HS256")

        with pytest.raises(ValueError, match="Invalid token issuer"):
            SsoService.verify_sso_token(token, sso_config)

    def test_verify_sso_token_invalid_signature(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "sso_auth",
        }
        token = jwt.encode(payload_data, "wrong-secret-key", algorithm="HS256")

        with pytest.raises(ValueError, match="Invalid token"):
            SsoService.verify_sso_token(token, sso_config)

    def test_verify_sso_token_missing_email(self):
        sso_config = MagicMock(spec=SsoConfig)
        sso_config.id = "test-sso-config-id"
        sso_config.secret_key = "test-secret-key-for-sso-token-generation"

        payload_data = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": "user123",
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "iat": datetime.now(UTC),
            "type": "sso_auth",
        }
        token = jwt.encode(payload_data, sso_config.secret_key, algorithm="HS256")

        with pytest.raises(ValueError, match="Email is required"):
            SsoService.verify_sso_token(token, sso_config)
