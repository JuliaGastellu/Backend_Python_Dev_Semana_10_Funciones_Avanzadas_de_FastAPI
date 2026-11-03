"""Baseline de Pulse."""
from alembic import op

revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(open("../Semana_7_Fundamentos_de_PostgreSQL/entrega/01-schema.sql", encoding="utf-8").read() if False else "SELECT 1")
    # La base de la semana 7 es el punto de partida. Con stamp marco esa base como baseline.


def downgrade() -> None: pass
