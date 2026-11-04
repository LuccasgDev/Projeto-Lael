from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.models import ProdutoPrincipal, Mimo, Reserva, Numero


def get_mimo_stock_info(db: Session, mimo: Mimo) -> dict:
    """
    Calculates availability of a Mimo considering:
    - quantidade_desejada
    - quantidade_comprada_externa (comprada na Amazon)
    - quantidade_reservada (reservas ativas)
    - quantidade_confirmada (confirmadas pelo casal)
    """
    reservadas_count = (
        db.query(func.count(Reserva.id))
        .filter(Reserva.mimo_id == mimo.id, Reserva.status == "reservada")
        .scalar()
        or 0
    )

    confirmadas_count = (
        db.query(func.count(Reserva.id))
        .filter(Reserva.mimo_id == mimo.id, Reserva.status == "confirmada")
        .scalar()
        or 0
    )

    comprometidas = reservadas_count + confirmadas_count + mimo.quantidade_comprada_externa
    restante = max(0, mimo.quantidade_desejada - comprometidas)

    return {
        "mimo_id": mimo.id,
        "quantidade_desejada": mimo.quantidade_desejada,
        "quantidade_comprada_externa": mimo.quantidade_comprada_externa,
        "quantidade_reservada": reservadas_count,
        "quantidade_confirmada": confirmadas_count,
        "comprometidas_total": comprometidas,
        "disponibilidade_restante": restante,
        "disponivel": restante > 0 and mimo.ativo,
    }


def get_produto_principal_stock_info(db: Session, produto: ProdutoPrincipal) -> dict:
    """
    Calculates availability of a ProdutoPrincipal.
    In the raffle system, each number 01-100 is assigned to a ProdutoPrincipal.
    A product can be associated with numbers up to its desired quantity.
    """
    # Count how many numbers currently have active or confirmed reservations for this product
    active_reservations = (
        db.query(func.count(Reserva.id))
        .join(Numero, Reserva.numero_id == Numero.id)
        .filter(
            Numero.produto_principal_id == produto.id,
            Reserva.status.in_(["reservada", "confirmada"])
        )
        .scalar()
        or 0
    )

    comprometidas = active_reservations + produto.quantidade_comprada_externa
    restante = max(0, produto.quantidade_desejada - comprometidas)

    return {
        "produto_id": produto.id,
        "quantidade_desejada": produto.quantidade_desejada,
        "quantidade_comprada_externa": produto.quantidade_comprada_externa,
        "quantidade_reservada_ou_confirmada": active_reservations,
        "disponibilidade_restante": restante,
        "disponivel": restante > 0 and produto.ativo,
    }
