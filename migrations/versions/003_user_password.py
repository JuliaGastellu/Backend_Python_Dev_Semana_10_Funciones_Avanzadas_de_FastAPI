"""Agrego contraseña hasheada a users."""
from alembic import op
import sqlalchemy as sa

revision = "003_user_password"
down_revision = "002_comment_updated_at"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(255), nullable=True))
    op.execute("UPDATE users SET hashed_password = '$2b$12$pendiente.reemplazar.al.activar.usuario' WHERE hashed_password IS NULL")
    op.alter_column("users", "hashed_password", nullable=False)

def downgrade() -> None: op.drop_column("users", "hashed_password")
