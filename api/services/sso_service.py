import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from sqlalchemy import select

from configs import dify_config
from extensions.ext_database import db
from libs.datetime_utils import naive_utc_now
from libs.passport import PassportService
from models.account import Account, TenantAccountRole
from models.sso import SsoConfig, SsoConfigStatus, SsoProvider
from services.account_service import AccountService, RegisterService, TenantService
from services.errors.account import AccountRegisterError

logger = logging.getLogger(__name__)


class SsoService:
    SSO_TOKEN_TYPE = "sso_auth"

    @staticmethod
    def get_sso_config(sso_config_id: str) -> SsoConfig | None:
        return db.session.query(SsoConfig).filter_by(id=sso_config_id).first()

    @staticmethod
    def get_sso_configs_by_tenant(tenant_id: str) -> list[SsoConfig]:
        return (
            db.session.query(SsoConfig)
            .filter_by(tenant_id=tenant_id, status=SsoConfigStatus.ACTIVE)
            .order_by(SsoConfig.created_at.desc())
            .all()
        )

    @staticmethod
    def create_sso_config(
        tenant_id: str,
        name: str,
        secret_key: str,
        created_by: str,
        provider: SsoProvider = SsoProvider.CUSTOM,
        token_expire_minutes: int = 60,
        default_role: str = "editor",
        config: dict[str, Any] | None = None,
    ) -> SsoConfig:
        sso_config = SsoConfig(
            tenant_id=tenant_id,
            name=name,
            provider=provider,
            secret_key=secret_key,
            token_expire_minutes=token_expire_minutes,
            default_role=default_role,
            config=json.dumps(config) if config else None,
            created_by=created_by,
        )
        db.session.add(sso_config)
        db.session.commit()
        return sso_config

    @staticmethod
    def update_sso_config(
        sso_config_id: str,
        tenant_id: str,
        **kwargs,
    ) -> SsoConfig:
        sso_config = db.session.query(SsoConfig).filter_by(id=sso_config_id, tenant_id=tenant_id).first()
        if not sso_config:
            raise ValueError("SSO config not found")

        for key, value in kwargs.items():
            if hasattr(sso_config, key):
                if key == "config" and isinstance(value, dict):
                    value = json.dumps(value)
                setattr(sso_config, key, value)

        sso_config.updated_at = naive_utc_now()
        db.session.commit()
        return sso_config

    @staticmethod
    def delete_sso_config(sso_config_id: str, tenant_id: str) -> None:
        sso_config = db.session.query(SsoConfig).filter_by(id=sso_config_id, tenant_id=tenant_id).first()
        if not sso_config:
            raise ValueError("SSO config not found")

        db.session.delete(sso_config)
        db.session.commit()

    @staticmethod
    def generate_sso_token(
        sso_config: SsoConfig,
        user_identifier: str,
        email: str,
        name: str | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> str:
        expire_dt = datetime.now(UTC) + timedelta(minutes=sso_config.token_expire_minutes)
        payload = {
            "iss": f"dify_sso:{sso_config.id}",
            "sub": user_identifier,
            "email": email,
            "name": name or email.split("@")[0],
            "exp": expire_dt,
            "iat": datetime.now(UTC),
            "type": SsoService.SSO_TOKEN_TYPE,
        }
        if additional_data:
            payload["data"] = additional_data

        token = jwt.encode(payload, sso_config.secret_key, algorithm="HS256")
        return token

    @staticmethod
    def verify_sso_token(token: str, sso_config: SsoConfig) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, sso_config.secret_key, algorithms=["HS256"])
            if payload.get("type") != SsoService.SSO_TOKEN_TYPE:
                raise ValueError("Invalid token type")
            if payload.get("iss") != f"dify_sso:{sso_config.id}":
                raise ValueError("Invalid token issuer")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

    @staticmethod
    def authenticate_with_sso(
        sso_config: SsoConfig,
        token: str,
        ip_address: str | None = None,
    ) -> tuple[Account, bool]:
        payload = SsoService.verify_sso_token(token, sso_config)

        email = payload.get("email")
        if not email:
            raise ValueError("Email is required in SSO token")

        email = email.lower()
        name = payload.get("name", email.split("@")[0])
        user_identifier = payload.get("sub")

        account = db.session.query(Account).filter_by(email=email).first()
        is_new_user = False

        if not account:
            if not dify_config.SSO_ALLOW_REGISTER:
                raise AccountRegisterError("SSO registration is not allowed")

            default_role = sso_config.default_role
            if not TenantAccountRole.is_valid_role(default_role):
                default_role = TenantAccountRole.EDITOR.value

            account = RegisterService.register_from_sso(
                email=email,
                name=name,
                default_role=default_role,
                sso_provider=f"sso_{sso_config.provider}",
                sso_identifier=user_identifier,
                language=dify_config.SSO_DEFAULT_LANGUAGE,
                timezone=dify_config.SSO_DEFAULT_TIMEZONE,
            )
            is_new_user = True

            tenant = TenantService.create_tenant(f"{account.name}'s Workspace", is_setup=True)
            TenantService.create_tenant_member(tenant, account, role="owner")
            account.current_tenant = tenant
        else:
            if account.status == "banned":
                raise ValueError("Account is banned")

            if name and account.name != name:
                account.name = name
                db.session.commit()

        token_pair = AccountService.login(account=account, ip_address=ip_address)

        return account, is_new_user, token_pair

    @staticmethod
    def get_access_token_for_account(account: Account) -> str:
        return AccountService.get_account_jwt_token(account)
