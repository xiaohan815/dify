import enum
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import TypeBase
from .engine import db
from .types import EnumText, StringUUID


class SsoProvider(enum.StrEnum):
    CUSTOM = "custom"
    OIDC = "oidc"
    SAML = "saml"


class SsoConfigStatus(enum.StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class SsoConfig(TypeBase):
    __tablename__ = "sso_configs"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id", name="sso_config_pkey"),
        sa.Index("sso_configs_tenant_id_idx", "tenant_id"),
        sa.Index("sso_configs_provider_idx", "provider"),
    )

    id: Mapped[str] = mapped_column(
        StringUUID,
        insert_default=lambda: str(uuid4()),
        default_factory=lambda: str(uuid4()),
        init=False,
    )
    tenant_id: Mapped[str] = mapped_column(StringUUID, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    secret_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[str] = mapped_column(StringUUID, nullable=False)
    provider: Mapped[SsoProvider] = mapped_column(
        EnumText(SsoProvider, length=16),
        server_default=sa.text("'custom'"),
        default=SsoProvider.CUSTOM,
    )
    status: Mapped[SsoConfigStatus] = mapped_column(
        EnumText(SsoConfigStatus, length=16),
        server_default=sa.text("'active'"),
        default=SsoConfigStatus.ACTIVE,
    )
    token_expire_minutes: Mapped[int] = mapped_column(
        sa.Integer,
        server_default=sa.text("60"),
        default=60,
    )
    default_role: Mapped[str] = mapped_column(
        String(32),
        server_default=sa.text("'editor'"),
        default="editor",
    )
    config: Mapped[str | None] = mapped_column(sa.Text, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        init=False,
    )
    updated_by: Mapped[str | None] = mapped_column(StringUUID, nullable=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        init=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "provider": self.provider,
            "status": self.status,
            "token_expire_minutes": self.token_expire_minutes,
            "default_role": self.default_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
