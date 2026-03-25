"""add_sso_configs_table

Revision ID: a1b2c3d4e5f6
Revises: 0ec65df55790
Create Date: 2026-03-16 10:00:00.000000

"""

from alembic import op
import models as models
import sqlalchemy as sa


def _is_pg(conn):
    return conn.dialect.name == "postgresql"


revision = "a1b2c3d4e5f6"
down_revision = "6b5f9f8b1a2c"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    if _is_pg(conn):
        op.create_table(
            "sso_configs",
            sa.Column("id", models.types.StringUUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
            sa.Column("tenant_id", models.types.StringUUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("provider", sa.String(length=16), server_default="custom", nullable=False),
            sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
            sa.Column("secret_key", sa.String(length=255), nullable=False),
            sa.Column("token_expire_minutes", sa.Integer(), server_default=sa.text("60"), nullable=False),
            sa.Column("default_role", sa.String(length=32), server_default=sa.text("'editor'"), nullable=False),
            sa.Column("config", sa.Text(), nullable=True),
            sa.Column("created_by", models.types.StringUUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_by", models.types.StringUUID(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id", name="sso_config_pkey"),
        )
    else:
        op.create_table(
            "sso_configs",
            sa.Column("id", models.types.StringUUID(), nullable=False),
            sa.Column("tenant_id", models.types.StringUUID(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("provider", sa.String(length=16), server_default="custom", nullable=False),
            sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
            sa.Column("secret_key", sa.String(length=255), nullable=False),
            sa.Column("token_expire_minutes", sa.Integer(), server_default="60", nullable=False),
            sa.Column("default_role", sa.String(length=32), server_default="editor", nullable=False),
            sa.Column("config", sa.Text(), nullable=True),
            sa.Column("created_by", models.types.StringUUID(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_by", models.types.StringUUID(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id", name="sso_config_pkey"),
        )

    with op.batch_alter_table("sso_configs", schema=None) as batch_op:
        batch_op.create_index("sso_configs_tenant_id_idx", ["tenant_id"], unique=False)
        batch_op.create_index("sso_configs_provider_idx", ["provider"], unique=False)


def downgrade():
    with op.batch_alter_table("sso_configs", schema=None) as batch_op:
        batch_op.drop_index("sso_configs_provider_idx")
        batch_op.drop_index("sso_configs_tenant_id_idx")

    op.drop_table("sso_configs")
