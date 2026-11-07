import logging

from sqlalchemy.orm import Session

from backend.app.models.models import Reserva, Numero, utcnow, HistoricoAdmin

logger = logging.getLogger(__name__)


def check_and_expire_reservations(db: Session) -> int:
    """
    Verifica todas as reservas ativas (status 'reservada') cujo prazo venceu e as marca
    como 'expirada', devolvendo o número para 'disponivel' (RN-06/07).
    O histórico é preservado. Usada pelo worker agendado E também nas leituras públicas
    e no ato de reserva, para que a expiração nunca dependa do navegador.
    """
    agora = utcnow()
    expired_reservations = (
        db.query(Reserva)
        .filter(Reserva.status == "reservada", Reserva.expira_em < agora)
        .all()
    )

    if not expired_reservations:
        return 0

    for res in expired_reservations:
        res.status = "expirada"
        numero_val = res.numero.numero
        res.numero.status = "disponivel"

        historico = HistoricoAdmin(
            reserva_id=res.id,
            acao="RESERVA_EXPIRADA",
            descricao=(
                f"Prazo de reserva expirado em {res.expira_em.strftime('%d/%m/%Y %H:%M')}. "
                f"Número {numero_val:02d} liberado automaticamente pelo sistema. "
                f"Histórico da reserva preservado."
            ),
            criado_em=agora,
        )
        db.add(historico)

    db.commit()
    logger.info(f"[EXPIRATION_WORKER] {len(expired_reservations)} reserva(s) expirada(s) e número(s) liberado(s).")
    return len(expired_reservations)


async def start_expiration_worker():
    """Worker agendado que executa a expiração periodicamente no backend."""
    import asyncio
    from backend.app.config import settings
    from backend.app.database import SessionLocal

    logger.info("[EXPIRATION_WORKER] Iniciando worker de expiração automática de reservas...")
    while True:
        try:
            db = SessionLocal()
            try:
                check_and_expire_reservations(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[EXPIRATION_WORKER] Erro no ciclo de expiração: {e}")
        await asyncio.sleep(settings.EXPIRATION_WORKER_INTERVAL)
