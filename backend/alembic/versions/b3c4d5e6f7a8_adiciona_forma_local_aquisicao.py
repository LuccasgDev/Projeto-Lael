"""adiciona opcao local para forma de aquisicao

Revision ID: b3c4d5e6f7a8
Revises: a1f2c3d4e5f6
Create Date: 2026-11-07

Permite a escolha de 'local' (compra presencial/loja física)
além de 'amazon' e 'pix' para forma_presente, forma_mimo e forma_aquisicao.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a1f2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_reserva_checks = {c["name"] for c in insp.get_check_constraints("reservas") if c.get("name")}
    existing_comp_checks = {c["name"] for c in insp.get_check_constraints("comprovantes") if c.get("name")}

    # reservas
    with op.batch_alter_table("reservas") as batch:
        if "ck_reserva_forma_presente" in existing_reserva_checks:
            batch.drop_constraint("ck_reserva_forma_presente", type_="check")
        if "ck_reserva_forma_mimo" in existing_reserva_checks:
            batch.drop_constraint("ck_reserva_forma_mimo", type_="check")
        batch.create_check_constraint(
            "ck_reserva_forma_presente",
            "forma_presente IN ('amazon','pix','local')"
        )
        batch.create_check_constraint(
            "ck_reserva_forma_mimo",
            "forma_mimo IN ('amazon','pix','local')"
        )

    # comprovantes
    with op.batch_alter_table("comprovantes") as batch:
        if "ck_comprovante_forma" in existing_comp_checks:
            batch.drop_constraint("ck_comprovante_forma", type_="check")
        batch.create_check_constraint(
            "ck_comprovante_forma",
            "forma_aquisicao IN ('amazon','pix','local')"
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_reserva_checks = {c["name"] for c in insp.get_check_constraints("reservas") if c.get("name")}
    existing_comp_checks = {c["name"] for c in insp.get_check_constraints("comprovantes") if c.get("name")}

    with op.batch_alter_table("comprovantes") as batch:
        if "ck_comprovante_forma" in existing_comp_checks:
            batch.drop_constraint("ck_comprovante_forma", type_="check")
        batch.create_check_constraint(
            "ck_comprovante_forma",
            "forma_aquisicao IN ('amazon','pix')"
        )

    with op.batch_alter_table("reservas") as batch:
        if "ck_reserva_forma_mimo" in existing_reserva_checks:
            batch.drop_constraint("ck_reserva_forma_mimo", type_="check")
        if "ck_reserva_forma_presente" in existing_reserva_checks:
            batch.drop_constraint("ck_reserva_forma_presente", type_="check")
        batch.create_check_constraint(
            "ck_reserva_forma_mimo",
            "forma_mimo IN ('amazon','pix')"
        )
        batch.create_check_constraint(
            "ck_reserva_forma_presente",
            "forma_presente IN ('amazon','pix')"
        )
