"""merge HRW SSO and Dify 1.14.2 migration heads

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6, a4f2d8c9b731
Create Date: 2026-07-14 10:00:00.000000

"""


# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = ("a1b2c3d4e5f6", "a4f2d8c9b731")
branch_labels = None
depends_on = None


def upgrade():
    # 仅合并 HRW SSO 与官方迁移分支，不执行额外数据库变更。
    pass


def downgrade():
    pass
