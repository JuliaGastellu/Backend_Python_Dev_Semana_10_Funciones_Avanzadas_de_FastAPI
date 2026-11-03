"""Agrego updated_at a comments."""
from alembic import op
import sqlalchemy as sa

revision = "002_comment_updated_at"
down_revision = "001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("comments", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False))


def downgrade() -> None: op.drop_column("comments", "updated_at")
