"""Agrego notificaciones e imagen por post."""
from alembic import op
import sqlalchemy as sa
revision = "005_realtime"
down_revision = "004_refresh_tokens"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("posts", sa.Column("image_filename", sa.String(100)))
    op.create_table("notifications",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("post_id", sa.BigInteger(), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

def downgrade():
    op.drop_table("notifications")
    op.drop_column("posts", "image_filename")
