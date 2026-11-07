from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import secrets
import urllib.parse
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.config import settings
from backend.app.models.models import (
    Numero, ProdutoPrincipal, Mimo, Reserva, Comprovante,
    HistoricoAdmin, Configuracao, Admin, utcnow
)
from backend.app.schemas.schemas import ReservaCreateRequest
from backend.app.services.stock_service import get_mimo_stock_info
from backend.app.services.expiration_worker import check_and_expire_reservations


def hash_tracking_token(token: str) -> str:
    """Hash SHA-256 do token de acompanhamento (o token puro NUNCA é guardado)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def money(value) -> Decimal:
    """Normaliza qualquer valor monetário para Decimal com 2 casas (nunca float puro)."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_config_value(db: Session, key: str, default: str = "") -> str:
    cfg = db.query(Configuracao).filter(Configuracao.chave == key).first()
    return cfg.valor if cfg else default


def build_whatsapp_message(
    reserva: Reserva,
    numero_val: int,
    presente_nome: str,
    mimo_nome: str,
    chave_pix: str,
    titular_pix: str,
    banco_pix: str
) -> tuple[str, str]:
    """
    Builds friendly WhatsApp message and click-to-chat URL.
    """
    forma_pres_desc = "Comprar na Amazon" if reserva.forma_presente == "amazon" else f"Pix de R$ {reserva.preco_presente_reserva:.2f}"
    forma_mimo_desc = "Comprar na Amazon" if reserva.forma_mimo == "amazon" else f"Pix de R$ {reserva.preco_mimo_reserva:.2f}"

    msg_lines = [
        "👶 *CHÁ DE RIFA DO LAEL*",
        "Olá, Talia e Lucas! Acabei de reservar meu número na rifa:",
        "",
        f"🔢 *Número:* {numero_val:02d}",
        f"👤 *Nome:* {reserva.nome_convidado}",
        "",
        "🎁 *ESCOLHAS:*",
        f"• *Presente Principal:* {presente_nome}",
        f"  Forma: {forma_pres_desc}",
        f"• *Mimo Complementar:* {mimo_nome}",
        f"  Forma: {forma_mimo_desc}",
    ]

    if reserva.valor_pix_total > 0:
        msg_lines.extend([
            "",
            f"💰 *Total a transferir via Pix:* R$ {reserva.valor_pix_total:.2f}",
            f"🔑 *Chave Pix:* {chave_pix}",
            f"🏦 *Favorecido:* {titular_pix} ({banco_pix})",
        ])

    msg_lines.extend([
        "",
        "📎 Estou enviando por aqui os comprovantes (da compra na Amazon e/ou do Pix) para a confirmação da minha reserva!",
        "Obrigado e parabéns pelo pequeno Lael! ✨",
    ])

    full_message = "\n".join(msg_lines)
    return full_message


def create_reservation(db: Session, payload: ReservaCreateRequest) -> Reserva:
    """
    Transactional creation of a reservation with row-level integrity checks.
    RN-06: a expiração é verificada também no ato da reserva — nunca depende do navegador.
    """
    # 0. Expire overdue reservations first (never depends on the browser)
    check_and_expire_reservations(db)

    # 1. Check and lock the chosen number
    numero_query = db.query(Numero).filter(Numero.id == payload.numero_id)
    if not settings.DATABASE_URL.startswith("sqlite"):
        numero_query = numero_query.with_for_update()

    numero = numero_query.first()
    if not numero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Número não encontrado no sistema"
        )

    if numero.status != "disponivel":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O número {numero.numero:02d} não está mais disponível para reserva"
        )

    # 2. Check main product
    produto = numero.produto_principal
    if not produto or not produto.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O número selecionado não possui um presente principal ativo configurado"
        )

    # 3. Check mimo stock
    mimo_query = db.query(Mimo).filter(Mimo.id == payload.mimo_id)
    if not settings.DATABASE_URL.startswith("sqlite"):
        mimo_query = mimo_query.with_for_update()

    mimo = mimo_query.first()
    if not mimo or not mimo.ativo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mimo selecionado não encontrado ou inativo"
        )

    # RN-08 v2: Pix exige preço conhecido — não é possível congelar um valor nulo
    if payload.forma_presente == "pix" and produto.preco_atual is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este presente não tem preço definido no momento (verifique na Amazon ou escolha comprar direto na Amazon)"
        )
    if payload.forma_mimo == "pix" and mimo.preco_atual is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este mimo não tem preço definido no momento (verifique na Amazon ou escolha comprar direto na Amazon)"
        )

    stock_info = get_mimo_stock_info(db, mimo)
    if stock_info["disponibilidade_restante"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"O mimo '{mimo.nome}' esgotou durante a seleção. Por favor escolha outro mimo."
        )

    # 4. Freeze prices at reservation time (RN-08, valores em Decimal)
    preco_presente_reserva = money(produto.preco_atual if produto.preco_atual is not None else 0)
    preco_mimo_reserva = money(mimo.preco_atual if mimo.preco_atual is not None else 0)

    # 5. Calculate Pix total strictly according to independent choices (RN-04)
    valor_pix_total = Decimal("0.00")
    if payload.forma_presente == "pix":
        valor_pix_total += preco_presente_reserva
    if payload.forma_mimo == "pix":
        valor_pix_total += preco_mimo_reserva

    valor_pix_total = money(valor_pix_total)

    # 6. Reservation deadline (default 72 hours)
    try:
        prazo_horas = int(get_config_value(db, "prazo_padrao_horas", str(settings.DEFAULT_RESERVATION_HOURS)))
    except ValueError:
        prazo_horas = 72

    agora = utcnow()
    expira_em = agora + timedelta(hours=prazo_horas)

    # Token de acompanhamento: gerado uma vez, apenas o hash é persistido
    tracking_token = secrets.token_urlsafe(24)

    # 7. Create Reservation
    reserva = Reserva(
        numero_id=numero.id,
        mimo_id=mimo.id,
        nome_convidado=payload.nome_convidado.strip(),
        whatsapp=payload.whatsapp,
        autoriza_nome_publico=payload.autoriza_nome_publico,
        forma_presente=payload.forma_presente,
        forma_mimo=payload.forma_mimo,
        preco_presente_reserva=preco_presente_reserva,
        preco_mimo_reserva=preco_mimo_reserva,
        valor_pix_total=valor_pix_total,
        status="reservada",
        criada_em=agora,
        expira_em=expira_em,
        token_acompanhamento_hash=hash_tracking_token(tracking_token),
    )
    db.add(reserva)
    db.flush()

    # 8. Create the TWO mandatory Comprovante records
    comp_presente = Comprovante(
        reserva_id=reserva.id,
        tipo_item="presente",
        forma_aquisicao=payload.forma_presente,
        status="aguardando_envio",
    )
    comp_mimo = Comprovante(
        reserva_id=reserva.id,
        tipo_item="mimo",
        forma_aquisicao=payload.forma_mimo,
        status="aguardando_envio",
    )
    db.add(comp_presente)
    db.add(comp_mimo)

    # 9. Update number status to 'reservado'
    numero.status = "reservado"

    # 10. Log in admin history
    historico = HistoricoAdmin(
        reserva_id=reserva.id,
        acao="RESERVA_CRIADA",
        descricao=f"Reserva criada pelo convidado {payload.nome_convidado} para o número {numero.numero:02d}. Expira em {expira_em.strftime('%d/%m/%Y %H:%M')}.",
        criado_em=agora,
    )
    db.add(historico)

    db.commit()
    db.refresh(reserva)
    return reserva, tracking_token


def approve_or_reject_voucher(
    db: Session,
    comprovante_id: int,
    novo_status: str,
    observacao: str,
    admin: Admin
) -> Comprovante:
    comp = db.query(Comprovante).filter(Comprovante.id == comprovante_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Comprovante não encontrado")

    agora = utcnow()
    comp.status = novo_status
    comp.observacao_admin = observacao

    if novo_status == "aprovado":
        comp.aprovado_em = agora
        comp.rejeitado_em = None
    elif novo_status == "rejeitado":
        comp.rejeitado_em = agora
        comp.aprovado_em = None
    elif novo_status == "recebido":
        comp.recebido_em = agora

    historico = HistoricoAdmin(
        administrador_id=admin.id,
        reserva_id=comp.reserva_id,
        acao=f"COMPROVANTE_{comp.tipo_item.upper()}_{novo_status.upper()}",
        descricao=f"Comprovante do {comp.tipo_item} alterado para '{novo_status}' por {admin.nome}. Obs: {observacao or 'Sem observação'}",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()
    db.refresh(comp)
    return comp


def confirm_reservation(db: Session, reserva_id: int, admin: Admin) -> Reserva:
    """
    Enforces that BOTH vouchers (presente AND mimo) must be 'aprovado' before confirmation.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    if reserva.status == "confirmada":
        raise HTTPException(status_code=400, detail="Esta reserva já se encontra confirmada")

    if reserva.status != "reservada":
        raise HTTPException(status_code=400, detail=f"Não é possível confirmar uma reserva com status '{reserva.status}'")

    # Verify both vouchers
    comprovantes = db.query(Comprovante).filter(Comprovante.reserva_id == reserva.id).all()
    if len(comprovantes) < 2:
        raise HTTPException(status_code=400, detail="A reserva não possui os 2 comprovantes cadastrados")

    pendentes = [c.tipo_item for c in comprovantes if c.status != "aprovado"]
    if pendentes:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível confirmar: os seguintes comprovantes ainda não foram aprovados: {', '.join(pendentes)}"
        )

    agora = utcnow()
    reserva.status = "confirmada"
    reserva.confirmada_em = agora

    # Update number status to 'confirmado'
    reserva.numero.status = "confirmado"

    historico = HistoricoAdmin(
        administrador_id=admin.id,
        reserva_id=reserva.id,
        acao="RESERVA_CONFIRMADA",
        descricao=f"Reserva do número {reserva.numero.numero:02d} confirmada com sucesso por {admin.nome}.",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()
    db.refresh(reserva)
    return reserva


def release_reservation(db: Session, reserva_id: int, admin: Admin, motivo: str = "") -> Reserva:
    """
    Manually releases a reservation. Number returns to 'disponivel', stock is returned.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    agora = utcnow()
    numero_val = reserva.numero.numero
    reserva.status = "cancelada"
    reserva.numero.status = "disponivel"

    historico = HistoricoAdmin(
        administrador_id=admin.id,
        reserva_id=reserva.id,
        acao="RESERVA_LIBERADA",
        descricao=f"Reserva do número {numero_val:02d} liberada por {admin.nome}. Motivo: {motivo or 'Liberação manual'}. Número voltou a ficar disponível.",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()
    db.refresh(reserva)
    return reserva


def extend_reservation_deadline(db: Session, reserva_id: int, admin: Admin, horas_adicionais: int) -> Reserva:
    """
    Extends the reservation deadline by given hours.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    if reserva.status != "reservada":
        raise HTTPException(status_code=400, detail="Apenas reservas com status 'reservada' podem ter seu prazo estendido")

    agora = utcnow()
    # If already past expiration, extend from now
    base_time = reserva.expira_em if reserva.expira_em > agora else agora
    nova_expiracao = base_time + timedelta(hours=horas_adicionais)
    reserva.expira_em = nova_expiracao

    historico = HistoricoAdmin(
        administrador_id=admin.id,
        reserva_id=reserva.id,
        acao="PRAZO_ESTENDIDO",
        descricao=f"Prazo da reserva do número {reserva.numero.numero:02d} estendido em +{horas_adicionais} horas por {admin.nome}. Novo vencimento: {nova_expiracao.strftime('%d/%m/%Y %H:%M')}.",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()
    db.refresh(reserva)
    return reserva
