"""
Rotina LGPD de anonimização (§7): anonimiza dados pessoais de reservas cujo evento
já ocorreu (ou acima do período de retenção configurável `retencao_dias_preservacao`).

Substitui nome e WhatsApp por valores irreversíveis, preservando os dados
financeiros/operacionais agregados. Pode ser executada manualmente ou agendada:

    python -m backend.app.anonymize_data

A configuração `retencao_dias_preservacao` (padrão: 180 dias após a data do evento)
fica no painel administrativo (Configurações).
"""
from datetime import timedelta

from backend.app.database import SessionLocal
from backend.app.models.models import Reserva, Comprovante, utcnow, HistoricoAdmin


def anonymize_old_reservations() -> int:
    db = SessionLocal()
    try:
        from backend.app.models.models import Configuracao

        cfg = db.query(Configuracao).filter(Configuracao.chave == "retencao_dias_preservacao").first()
        try:
            dias = int(cfg.valor) if cfg else 180
        except ValueError:
            dias = 180

        limite = utcnow() - timedelta(days=dias)
        antigas = (
            db.query(Reserva)
            .filter(Reserva.status.in_(["confirmada", "expirada", "cancelada"]))
            .filter(Reserva.criada_em < limite)
            .all()
        )
        count = 0
        for r in antigas:
            r.nome_convidado = f"Convidado anonimizado #{r.id}"
            r.whatsapp = "00000000000"
            r.autoriza_nome_publico = False
            count += 1

        if count:
            db.add(HistoricoAdmin(
                acao="LGPD_ANONIMIZACAO",
                descricao=f"{count} reserva(s) com dados pessoais anonimizados conforme retenção de {dias} dias.",
                criado_em=utcnow(),
            ))
        db.commit()
        print(f"[LGPD] {count} reserva(s) anonimizada(s).")
        return count
    finally:
        db.close()


if __name__ == "__main__":
    anonymize_old_reservations()
