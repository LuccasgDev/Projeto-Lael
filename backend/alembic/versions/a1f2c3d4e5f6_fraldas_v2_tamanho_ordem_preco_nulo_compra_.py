"""fraldas v2: tamanho/ordem dos grupos, preco nulo, compra externa

Revision ID: a1f2c3d4e5f6
Revises: 924d4a3ff1ee
Create Date: 2026-11-06

RN-01 v2: os 100 números são fraldas agrupadas por tamanho (ordem editável).
RN-08 v2: preço pode ser nulo (Amazon mostra "Ver opções"); admin informa manual.
RN-10: número pode ser ocupado por compra externa (status + origem registrada).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '924d4a3ff1ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona colunas novas; torna preco_atual anulável nas duas tabelas de produto."""
    # produtos_principais (fraldas)
    op.add_column("produtos_principais", sa.Column("tamanho", sa.String(length=30), nullable=True))
    op.add_column("produtos_principais", sa.Column("ordem_exibicao", sa.Integer(), nullable=False, server_default="0"))
    with op.batch_alter_table("produtos_principais") as batch:
        batch.alter_column("preco_atual", existing_type=sa.Numeric(10, 2), nullable=True)

    # mimos
    with op.batch_alter_table("mimos") as batch:
        batch.alter_column("preco_atual", existing_type=sa.Numeric(10, 2), nullable=True)

    # numeros — origem da compra externa (RN-10)
    op.add_column("numeros", sa.Column("origem_ocupacao", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("numeros", "origem_ocupacao")
    with op.batch_alter_table("mimos") as batch:
        batch.alter_column("preco_atual", existing_type=sa.Numeric(10, 2), nullable=False)
    with op.batch_alter_table("produtos_principais") as batch:
        batch.alter_column("preco_atual", existing_type=sa.Numeric(10, 2), nullable=False)
    op.drop_column("produtos_principais", "ordem_exibicao")
    op.drop_column("produtos_principais", "tamanho")
