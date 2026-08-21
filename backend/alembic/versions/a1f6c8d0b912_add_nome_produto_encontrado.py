"""add nome_produto_encontrado to market_prices

Revision ID: a1f6c8d0b912
Revises: 7b3a1d9c2e45
"""

from alembic import op
import sqlalchemy as sa

revision = "a1f6c8d0b912"
down_revision = "7b3a1d9c2e45"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "market_prices",
        sa.Column("nome_produto_encontrado", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("market_prices", "nome_produto_encontrado")