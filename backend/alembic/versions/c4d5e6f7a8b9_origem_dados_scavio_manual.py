"""adiciona colunas de origem (MANUAL/SCAVIO) em produtos e mimos

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def _add_cols(table):
    with op.batch_alter_table(table) as batch:
        batch.add_column(sa.Column("preco_origem", sa.String(10), nullable=False, server_default="SCAVIO"))
        batch.add_column(sa.Column("imagem_origem", sa.String(10), nullable=False, server_default="SCAVIO"))


def upgrade() -> None:
    _add_cols("produtos_principais")
    _add_cols("mimos")


def downgrade() -> None:
    for table in ("produtos_principais", "mimos"):
        with op.batch_alter_table(table) as batch:
            batch.drop_column("imagem_origem")
            batch.drop_column("preco_origem")
