"""Creo la tabla de refresh tokens rotativos."""
from alembic import op
import sqlalchemy as sa

revision = "004_refresh_tokens"
down_revision = "003_user_password"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("refresh_tokens", sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True), sa.Column("jti_hash", sa.String(64), nullable=False, unique=True), sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False), sa.Column("revoked_at", sa.TIMESTAMP(timezone=True)), sa.Column("replaced_by_hash", sa.String(64)), sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

def downgrade() -> None: op.drop_table("refresh_tokens")
