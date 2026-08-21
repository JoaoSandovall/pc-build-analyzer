"""add indexes used by budget and market-price queries

Revision ID: 7b3a1d9c2e45
Revises: 961b326eb910
"""

from alembic import op


revision = "7b3a1d9c2e45"
down_revision = "961b326eb910"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_budgets_s3_key", "budgets", ["s3_key"])
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_items_budget_id", "items", ["budget_id"])
    op.create_index("ix_market_prices_item_id", "market_prices", ["item_id"])
    op.create_index(
        "ix_market_prices_item_coletado_em",
        "market_prices",
        ["item_id", "coletado_em"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_prices_item_coletado_em", table_name="market_prices")
    op.drop_index("ix_market_prices_item_id", table_name="market_prices")
    op.drop_index("ix_items_budget_id", table_name="items")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_constraint("uq_budgets_s3_key", "budgets", type_="unique")
