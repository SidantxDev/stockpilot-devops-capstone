"""seed demo inventory so a fresh deployment is not an empty page

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16 10:05:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEMO_PRODUCTS = [
    # sku, name, category, qty, reorder, price, supplier, location
    ("ELEC-1001", "USB-C Charger 65W", "Electronics", 48, 15, 1899.00, "VoltEdge Traders", "A1-01"),
    ("ELEC-1002", "Wireless Mouse", "Electronics", 9, 12, 749.00, "VoltEdge Traders", "A1-04"),
    ("ELEC-1003", "27\" IPS Monitor", "Electronics", 0, 4, 15499.00, "PixelView Pvt Ltd", "A2-02"),
    ("OFFC-2001", "A4 Copier Paper (500 sheets)", "Office Supplies", 120, 40, 329.00, "PaperMill Co.", "B1-01"),
    ("OFFC-2002", "Gel Pens (Box of 10)", "Office Supplies", 35, 20, 180.00, "PaperMill Co.", "B1-03"),
    ("FURN-3001", "Ergonomic Office Chair", "Furniture", 6, 5, 8999.00, "SitRight Furnishings", "C3-01"),
    ("FURN-3002", "Standing Desk Frame", "Furniture", 3, 4, 21999.00, "SitRight Furnishings", "C3-02"),
    ("PACK-4001", "Corrugated Box 12x12x12", "Packaging", 400, 150, 42.50, "BoxCraft India", "D1-01"),
    ("PACK-4002", "Bubble Wrap Roll 50m", "Packaging", 18, 10, 899.00, "BoxCraft India", "D1-02"),
    ("SAFE-5001", "Nitrile Gloves (Box of 100)", "Safety", 0, 25, 450.00, "SafeHands Supply", "E2-01"),
]


def upgrade() -> None:
    products = sa.table(
        "products",
        sa.column("sku", sa.String),
        sa.column("name", sa.String),
        sa.column("category", sa.String),
        sa.column("quantity", sa.Integer),
        sa.column("reorder_level", sa.Integer),
        sa.column("unit_price", sa.Numeric),
        sa.column("supplier", sa.String),
        sa.column("location", sa.String),
    )
    op.bulk_insert(
        products,
        [
            dict(sku=s, name=n, category=c, quantity=q, reorder_level=r, unit_price=p, supplier=sup, location=loc)
            for s, n, c, q, r, p, sup, loc in DEMO_PRODUCTS
        ],
    )


def downgrade() -> None:
    skus = ", ".join(f"'{p[0]}'" for p in DEMO_PRODUCTS)
    op.execute(f"DELETE FROM products WHERE sku IN ({skus})")
