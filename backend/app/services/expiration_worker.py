import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.app.models.models import Reserva, Numero, HistoricoAdmin
from backend.app.config import settings

logger = logging.getLogger(__name__)


def check_and_expire_reservations(db: Session) -> int:
    """
    Checks all active reservations past expiration time and marks them as expired.
    Releases the number back to available and records audit history.
    Returns the count of expired reservations.
    """
    agora = datetime.utcnow()
    expired_reservations = (
        db.query(Reserva)
        .filter(Reserva.status == "reservada", Reserva.expira_em < agora)
        .all()
    )

    count = 0
    for res in expired_reservations:
        numero_val = res.numero.numero
        res.status = "expirada"
        res.numero.status = "disponivel"

        historico = HistoricoAdmin(
            reserva_id=res.id,
            acao="RESERVA_EXPIRADA_AUTOMATICA",
            descricao=f"Prazo de reserva expirado em {res.expira_em.strftime('%d/%m/%Y %H:%M')}. Número {numero_val:02d} liberado automaticamente pelo sistema.",
            criado_em=agora,
        )
        db.add(historico)
        count += 1

    if count > 0:
        db.commit()
        logger.info(f"[EXPIRATION_WORKER] {count} reserva(s) expirada(s) e número(s) liberado(s).")

    return count


async def start_expiration_worker():
    """
    Background worker loop that runs periodically.
    """
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
