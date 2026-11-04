import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.database import get_db
from backend.app.models.models import Numero, ProdutoPrincipal, Mimo, Reserva, Comprovante
from backend.app.schemas.schemas import (
    NumeroGridItem, NumeroDetailResponse, MimoPublic,
    ReservaCreateRequest, ReservaPublicResponse,
    PublicConfigResponse, ProdutoPrincipalPublic, ComprovantePublic
)
from backend.app.services.reservation_service import (
    create_reservation, get_config_value, build_whatsapp_message
)
from backend.app.services.stock_service import get_mimo_stock_info, get_produto_principal_stock_info

router = APIRouter(prefix="/public", tags=["Público"])


@router.get("/config", response_model=PublicConfigResponse)
def get_public_config(db: Session = Depends(get_db)):
    """
    Returns public event configuration (Pix details, couple contact, event date).
    """
    return PublicConfigResponse(
        nome_evento=get_config_value(db, "nome_evento", "Chá de Rifa do Lael"),
        data_evento=get_config_value(db, "data_evento", "Março de 2027"),
        whatsapp_casal=get_config_value(db, "whatsapp_casal", "85999998888"),
        chave_pix=get_config_value(db, "chave_pix", "lael2027@chaderifa.com.br"),
        tipo_chave_pix=get_config_value(db, "tipo_chave_pix", "E-mail"),
        titular_pix=get_config_value(db, "titular_pix", "Talia Vitória / Lucas Gabriel"),
        banco_pix=get_config_value(db, "banco_pix", "Nubank"),
        prazo_padrao_horas=int(get_config_value(db, "prazo_padrao_horas", "72")),
        total_numeros=int(get_config_value(db, "total_numeros", "100")),
        mensagem_inicial=get_config_value(db, "mensagem_inicial", "Sejam muito bem-vindos ao Chá de Rifa do Lael!"),
        mensagem_confirmacao=get_config_value(db, "mensagem_confirmacao", "Obrigado por celebrar esse momento conosco!"),
    )


@router.get("/numbers", response_model=List[NumeroGridItem])
def get_numbers_grid(db: Session = Depends(get_db)):
    """
    Returns the public 01-100 numbers grid with availability and privacy-safe display names.
    """
    numeros = db.query(Numero).order_by(Numero.numero.asc()).all()
    result = []

    for n in numeros:
        nome_pub = None
        if n.status in ["reservado", "confirmado"]:
            # Check latest active or confirmed reservation
            res = (
                db.query(Reserva)
                .filter(Reserva.numero_id == n.id, Reserva.status.in_(["reservada", "confirmada"]))
                .order_by(Reserva.id.desc())
                .first()
            )
            if res and res.autoriza_nome_publico:
                # LGPD safe: Show first name or sanitized name, never full sensitive details
                nome_parts = res.nome_convidado.strip().split()
                nome_pub = f"{nome_parts[0]} {nome_parts[-1][0]}." if len(nome_parts) > 1 else nome_parts[0]

        prod_nome = n.produto_principal.nome if n.produto_principal else None
        prod_img = n.produto_principal.imagem_url if n.produto_principal else None

        result.append(NumeroGridItem(
            id=n.id,
            numero=n.numero,
            status=n.status,
            nome_publico=nome_pub,
            produto_nome=prod_nome,
            produto_imagem=prod_img
        ))

    return result


@router.get("/numbers/{num}", response_model=NumeroDetailResponse)
def get_number_detail(num: int, db: Session = Depends(get_db)):
    """
    Returns full details for a chosen number, including associated main product.
    """
    numero = db.query(Numero).filter(Numero.numero == num).first()
    if not numero:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    prod_public = None
    if numero.produto_principal:
        stock = get_produto_principal_stock_info(db, numero.produto_principal)
        prod_public = ProdutoPrincipalPublic(
            id=numero.produto_principal.id,
            asin=numero.produto_principal.asin,
            nome=numero.produto_principal.nome,
            descricao=numero.produto_principal.descricao,
            imagem_url=numero.produto_principal.imagem_url,
            produto_url=numero.produto_principal.produto_url,
            categoria=numero.produto_principal.categoria,
            preco_atual=numero.produto_principal.preco_atual,
            preco_anterior=numero.produto_principal.preco_anterior,
            preco_sincronizado_em=numero.produto_principal.preco_sincronizado_em,
            quantidade_desejada=numero.produto_principal.quantidade_desejada,
            disponibilidade_restante=stock["disponibilidade_restante"]
        )

    return NumeroDetailResponse(
        id=numero.id,
        numero=numero.numero,
        status=numero.status,
        produto_principal=prod_public
    )


@router.get("/mimos", response_model=List[MimoPublic])
def get_available_mimos(db: Session = Depends(get_db)):
    """
    Returns all active mimos with calculated remaining availability.
    """
    mimos = db.query(Mimo).filter(Mimo.ativo == True).order_by(Mimo.nome.asc()).all()
    result = []

    for m in mimos:
        stock = get_mimo_stock_info(db, m)
        result.append(MimoPublic(
            id=m.id,
            asin=m.asin,
            nome=m.nome,
            descricao=m.descricao,
            imagem_url=m.imagem_url,
            produto_url=m.produto_url,
            categoria=m.categoria,
            preco_atual=m.preco_atual,
            preco_anterior=m.preco_anterior,
            preco_sincronizado_em=m.preco_sincronizado_em,
            disponibilidade_restante=stock["disponibilidade_restante"]
        ))

    return result


@router.post("/reserve", response_model=ReservaPublicResponse)
def make_reservation(payload: ReservaCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a new reservation with independent choices and generates WhatsApp action URL.
    """
    reserva = create_reservation(db, payload)

    # Prepare WhatsApp data
    whatsapp_casal = get_config_value(db, "whatsapp_casal", "85999998888")
    chave_pix = get_config_value(db, "chave_pix", "")
    titular_pix = get_config_value(db, "titular_pix", "")
    banco_pix = get_config_value(db, "banco_pix", "")

    presente_nome = reserva.numero.produto_principal.nome if reserva.numero.produto_principal else "Presente"
    mimo_nome = reserva.mimo.nome if reserva.mimo else "Mimo"

    msg = build_whatsapp_message(
        reserva=reserva,
        numero_val=reserva.numero.numero,
        presente_nome=presente_nome,
        mimo_nome=mimo_nome,
        chave_pix=chave_pix,
        titular_pix=titular_pix,
        banco_pix=banco_pix
    )

    clean_phone = "".join(filter(str.isdigit, whatsapp_casal))
    if not clean_phone.startswith("55") and len(clean_phone) in [10, 11]:
        clean_phone = f"55{clean_phone}"

    encoded_msg = urllib.parse.quote(msg)
    wa_link = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

    comprovantes_pub = [
        ComprovantePublic(
            id=c.id,
            tipo_item=c.tipo_item,
            forma_aquisicao=c.forma_aquisicao,
            status=c.status,
            observacao_admin=c.observacao_admin
        )
        for c in reserva.comprovantes
    ]

    return ReservaPublicResponse(
        id=reserva.id,
        numero=reserva.numero.numero,
        nome_convidado=reserva.nome_convidado,
        whatsapp=reserva.whatsapp,
        forma_presente=reserva.forma_presente,
        forma_mimo=reserva.forma_mimo,
        presente_nome=presente_nome,
        presente_imagem=reserva.numero.produto_principal.imagem_url if reserva.numero.produto_principal else None,
        presente_url=reserva.numero.produto_principal.produto_url if reserva.numero.produto_principal else None,
        preco_presente_reserva=reserva.preco_presente_reserva,
        mimo_nome=mimo_nome,
        mimo_imagem=reserva.mimo.imagem_url if reserva.mimo else None,
        mimo_url=reserva.mimo.produto_url if reserva.mimo else None,
        preco_mimo_reserva=reserva.preco_mimo_reserva,
        valor_pix_total=reserva.valor_pix_total,
        status=reserva.status,
        criada_em=reserva.criada_em,
        expira_em=reserva.expira_em,
        whatsapp_link=wa_link,
        whatsapp_mensagem=msg,
        comprovantes=comprovantes_pub
    )


@router.get("/reserve/{reserva_id}", response_model=ReservaPublicResponse)
def get_reservation_status(reserva_id: int, db: Session = Depends(get_db)):
    """
    Returns public reservation view for guest confirmation tracking.
    """
    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva não encontrada")

    whatsapp_casal = get_config_value(db, "whatsapp_casal", "85999998888")
    chave_pix = get_config_value(db, "chave_pix", "")
    titular_pix = get_config_value(db, "titular_pix", "")
    banco_pix = get_config_value(db, "banco_pix", "")

    presente_nome = reserva.numero.produto_principal.nome if reserva.numero.produto_principal else "Presente"
    mimo_nome = reserva.mimo.nome if reserva.mimo else "Mimo"

    msg = build_whatsapp_message(
        reserva=reserva,
        numero_val=reserva.numero.numero,
        presente_nome=presente_nome,
        mimo_nome=mimo_nome,
        chave_pix=chave_pix,
        titular_pix=titular_pix,
        banco_pix=banco_pix
    )

    clean_phone = "".join(filter(str.isdigit, whatsapp_casal))
    if not clean_phone.startswith("55") and len(clean_phone) in [10, 11]:
        clean_phone = f"55{clean_phone}"

    encoded_msg = urllib.parse.quote(msg)
    wa_link = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

    comprovantes_pub = [
        ComprovantePublic(
            id=c.id,
            tipo_item=c.tipo_item,
            forma_aquisicao=c.forma_aquisicao,
            status=c.status,
            observacao_admin=c.observacao_admin
        )
        for c in reserva.comprovantes
    ]

    return ReservaPublicResponse(
        id=reserva.id,
        numero=reserva.numero.numero,
        nome_convidado=reserva.nome_convidado,
        whatsapp=reserva.whatsapp,
        forma_presente=reserva.forma_presente,
        forma_mimo=reserva.forma_mimo,
        presente_nome=presente_nome,
        presente_imagem=reserva.numero.produto_principal.imagem_url if reserva.numero.produto_principal else None,
        presente_url=reserva.numero.produto_principal.produto_url if reserva.numero.produto_principal else None,
        preco_presente_reserva=reserva.preco_presente_reserva,
        mimo_nome=mimo_nome,
        mimo_imagem=reserva.mimo.imagem_url if reserva.mimo else None,
        mimo_url=reserva.mimo.produto_url if reserva.mimo else None,
        preco_mimo_reserva=reserva.preco_mimo_reserva,
        valor_pix_total=reserva.valor_pix_total,
        status=reserva.status,
        criada_em=reserva.criada_em,
        expira_em=reserva.expira_em,
        whatsapp_link=wa_link,
        whatsapp_mensagem=msg,
        comprovantes=comprovantes_pub
    )
