from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any

from backend.app.database import get_db
from backend.app.models.models import (
    Admin, Numero, ProdutoPrincipal, Mimo, Reserva,
    Comprovante, HistoricoAdmin, Configuracao
)
from backend.app.schemas.schemas import (
    DashboardStatsResponse, ReservaAdminItem, ComprovanteAdminResponse,
    ComprovanteActionRequest, EstenderPrazoRequest,
    ProdutoPrincipalCreateUpdate, MimoCreateUpdate,
    ConfiguracaoBulkUpdate, HistoricoAdminResponse
)
from backend.app.services.auth_service import get_current_admin
from backend.app.services.stock_service import get_mimo_stock_info, get_produto_principal_stock_info
from backend.app.services.reservation_service import (
    approve_or_reject_voucher, confirm_reservation,
    release_reservation, extend_reservation_deadline
)
from backend.app.services.amazon_service import manual_update_price
from backend.app.services.export_service import generate_reservations_export, generate_pix_report

router = APIRouter(prefix="/admin", tags=["Administração"])


@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Computes dashboard metrics, counts and charts data.
    """
    total_numeros = db.query(func.count(Numero.id)).scalar() or 0
    disponiveis = db.query(func.count(Numero.id)).filter(Numero.status == "disponivel").scalar() or 0
    reservados = db.query(func.count(Numero.id)).filter(Numero.status == "reservado").scalar() or 0
    confirmados = db.query(func.count(Numero.id)).filter(Numero.status == "confirmado").scalar() or 0
    expiradas = db.query(func.count(Reserva.id)).filter(Reserva.status == "expirada").scalar() or 0

    comprovantes_pendentes = (
        db.query(func.count(Comprovante.id))
        .join(Reserva, Comprovante.reserva_id == Reserva.id)
        .filter(Reserva.status == "reservada", Comprovante.status.in_(["aguardando_envio", "recebido"]))
        .scalar()
        or 0
    )

    pix_confirmado = (
        db.query(func.sum(Reserva.valor_pix_total))
        .filter(Reserva.status == "confirmada")
        .scalar()
        or 0.0
    )

    pix_pendente = (
        db.query(func.sum(Reserva.valor_pix_total))
        .filter(Reserva.status == "reservada")
        .scalar()
        or 0.0
    )

    # Top chosen main products
    top_prod_query = (
        db.query(ProdutoPrincipal.nome, func.count(Reserva.id).label("total"))
        .join(Numero, Numero.produto_principal_id == ProdutoPrincipal.id)
        .join(Reserva, Reserva.numero_id == Numero.id)
        .filter(Reserva.status.in_(["reservada", "confirmada"]))
        .group_by(ProdutoPrincipal.nome)
        .order_by(desc("total"))
        .limit(5)
        .all()
    )
    top_presentes = [{"nome": row[0], "total": row[1]} for row in top_prod_query]

    # Top chosen mimos
    top_mimo_query = (
        db.query(Mimo.nome, func.count(Reserva.id).label("total"))
        .join(Reserva, Reserva.mimo_id == Mimo.id)
        .filter(Reserva.status.in_(["reservada", "confirmada"]))
        .group_by(Mimo.nome)
        .order_by(desc("total"))
        .limit(5)
        .all()
    )
    top_mimos = [{"nome": row[0], "total": row[1]} for row in top_mimo_query]

    return DashboardStatsResponse(
        total_numeros=total_numeros,
        numeros_disponiveis=disponiveis,
        numeros_reservados=reservados,
        numeros_confirmados=confirmados,
        reservas_expiradas=expiradas,
        comprovantes_pendentes=comprovantes_pendentes,
        valor_total_pix_confirmado=round(pix_confirmado, 2),
        valor_total_pix_pendente=round(pix_pendente, 2),
        top_presentes=top_presentes,
        top_mimos=top_mimos
    )


@router.get("/reservations", response_model=List[ReservaAdminItem])
def list_reservations(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Lists reservations with optional status filter and search by name/whatsapp/number.
    """
    query = db.query(Reserva).join(Numero, Reserva.numero_id == Numero.id).order_by(Reserva.criada_em.desc())

    if status_filter:
        query = query.filter(Reserva.status == status_filter)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Reserva.nome_convidado.ilike(s)) |
            (Reserva.whatsapp.ilike(s))
        )

    reservas = query.all()
    agora = datetime.utcnow()
    result = []

    for r in reservas:
        comprovantes_list = [
            ComprovanteAdminResponse(
                id=c.id,
                reserva_id=c.reserva_id,
                tipo_item=c.tipo_item,
                forma_aquisicao=c.forma_aquisicao,
                status=c.status,
                observacao_admin=c.observacao_admin,
                recebido_em=c.recebido_em,
                aprovado_em=c.aprovado_em,
                rejeitado_em=c.rejeitado_em
            )
            for c in r.comprovantes
        ]

        # Both vouchers must be approved
        ambos_aprovados = (
            len(r.comprovantes) == 2 and
            all(c.status == "aprovado" for c in r.comprovantes)
        )
        pode_confirmar = ambos_aprovados and r.status == "reservada"

        delta = (r.expira_em - agora).total_seconds() / 3600.0
        horas_restantes = max(0.0, round(delta, 1))

        pres_nome = r.numero.produto_principal.nome if r.numero.produto_principal else "N/A"
        mimo_nome = r.mimo.nome if r.mimo else "N/A"

        result.append(ReservaAdminItem(
            id=r.id,
            numero_id=r.numero_id,
            numero=r.numero.numero,
            mimo_id=r.mimo_id,
            nome_convidado=r.nome_convidado,
            whatsapp=r.whatsapp,
            autoriza_nome_publico=r.autoriza_nome_publico,
            forma_presente=r.forma_presente,
            forma_mimo=r.forma_mimo,
            preco_presente_reserva=r.preco_presente_reserva,
            preco_mimo_reserva=r.preco_mimo_reserva,
            valor_pix_total=r.valor_pix_total,
            status=r.status,
            criada_em=r.criada_em,
            expira_em=r.expira_em,
            confirmada_em=r.confirmada_em,
            presente_nome=pres_nome,
            mimo_nome=mimo_nome,
            comprovantes=comprovantes_list,
            pode_confirmar=pode_confirmar,
            horas_restantes=horas_restantes
        ))

    return result


@router.post("/comprovantes/{comprovante_id}/action", response_model=ComprovanteAdminResponse)
def handle_comprovante_action(
    comprovante_id: int,
    payload: ComprovanteActionRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Approves or rejects an individual voucher.
    """
    comp = approve_or_reject_voucher(
        db=db,
        comprovante_id=comprovante_id,
        novo_status=payload.status,
        observacao=payload.observacao or "",
        admin=admin
    )
    return comp


@router.post("/reservations/{reserva_id}/confirm")
def confirm_reservation_endpoint(
    reserva_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Confirms a reservation (strictly requires BOTH vouchers approved).
    """
    reserva = confirm_reservation(db=db, reserva_id=reserva_id, admin=admin)
    return {"message": "Reserva confirmada com sucesso!", "reserva_id": reserva.id, "status": reserva.status}


@router.post("/reservations/{reserva_id}/release")
def release_reservation_endpoint(
    reserva_id: int,
    motivo: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Releases a reservation, freeing the number back to available.
    """
    reserva = release_reservation(db=db, reserva_id=reserva_id, admin=admin, motivo=motivo or "")
    return {"message": "Reserva liberada e número colocado novamente disponível.", "reserva_id": reserva.id}


@router.post("/reservations/{reserva_id}/extend")
def extend_reservation_endpoint(
    reserva_id: int,
    payload: EstenderPrazoRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Extends the reservation deadline by X hours.
    """
    reserva = extend_reservation_deadline(
        db=db,
        reserva_id=reserva_id,
        admin=admin,
        horas_adicionais=payload.horas_adicionais
    )
    return {
        "message": f"Prazo estendido em +{payload.horas_adicionais} horas.",
        "nova_expiracao": reserva.expira_em.isoformat()
    }


# --- Produtos Principais Management ---

@router.get("/produtos")
def list_produtos_principais(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    produtos = db.query(ProdutoPrincipal).order_by(ProdutoPrincipal.nome.asc()).all()
    result = []
    for p in produtos:
        stock = get_produto_principal_stock_info(db, p)
        result.append({
            "id": p.id,
            "asin": p.asin,
            "nome": p.nome,
            "descricao": p.descricao,
            "imagem_url": p.imagem_url,
            "produto_url": p.produto_url,
            "categoria": p.categoria,
            "preco_atual": p.preco_atual,
            "preco_anterior": p.preco_anterior,
            "preco_sincronizado_em": p.preco_sincronizado_em,
            "quantidade_desejada": p.quantidade_desejada,
            "quantidade_comprada_externa": p.quantidade_comprada_externa,
            "ativo": p.ativo,
            "numeros_associados": [n.numero for n in p.numeros],
            "stock_info": stock
        })
    return result


@router.post("/produtos")
def create_produto_principal(
    payload: ProdutoPrincipalCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    novo = ProdutoPrincipal(
        asin=payload.asin,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        imagem_url=payload.imagem_url,
        produto_url=payload.produto_url,
        categoria=payload.categoria,
        preco_atual=payload.preco_atual,
        preco_anterior=payload.preco_anterior,
        preco_sincronizado_em=datetime.utcnow(),
        quantidade_desejada=payload.quantidade_desejada,
        quantidade_comprada_externa=payload.quantidade_comprada_externa,
        ativo=payload.ativo,
        criado_em=datetime.utcnow(),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/produtos/{produto_id}")
def update_produto_principal(
    produto_id: int,
    payload: ProdutoPrincipalCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    produto = db.query(ProdutoPrincipal).filter(ProdutoPrincipal.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    produto.asin = payload.asin
    produto.nome = payload.nome.strip()
    produto.descricao = payload.descricao
    produto.imagem_url = payload.imagem_url
    produto.produto_url = payload.produto_url
    produto.categoria = payload.categoria
    produto.preco_atual = payload.preco_atual
    if payload.preco_anterior:
        produto.preco_anterior = payload.preco_anterior
    produto.quantidade_desejada = payload.quantidade_desejada
    produto.quantidade_comprada_externa = payload.quantidade_comprada_externa
    produto.ativo = payload.ativo

    db.commit()
    db.refresh(produto)
    return produto


@router.post("/produtos/{produto_id}/price")
def update_produto_price(
    produto_id: int,
    novo_preco: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    item = manual_update_price(db, produto_id, "principal", novo_preco, admin)
    return {"message": "Preço atualizado com sucesso", "preco_atual": item.preco_atual}


# --- Mimos Management ---

@router.get("/mimos")
def list_mimos(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    mimos = db.query(Mimo).order_by(Mimo.nome.asc()).all()
    result = []
    for m in mimos:
        stock = get_mimo_stock_info(db, m)
        result.append({
            "id": m.id,
            "asin": m.asin,
            "nome": m.nome,
            "descricao": m.descricao,
            "imagem_url": m.imagem_url,
            "produto_url": m.produto_url,
            "categoria": m.categoria,
            "preco_atual": m.preco_atual,
            "preco_anterior": m.preco_anterior,
            "preco_sincronizado_em": m.preco_sincronizado_em,
            "quantidade_desejada": m.quantidade_desejada,
            "quantidade_comprada_externa": m.quantidade_comprada_externa,
            "ativo": m.ativo,
            "stock_info": stock
        })
    return result


@router.post("/mimos")
def create_mimo(
    payload: MimoCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    novo = Mimo(
        asin=payload.asin,
        nome=payload.nome.strip(),
        descricao=payload.descricao,
        imagem_url=payload.imagem_url,
        produto_url=payload.produto_url,
        categoria=payload.categoria,
        preco_atual=payload.preco_atual,
        preco_anterior=payload.preco_anterior,
        preco_sincronizado_em=datetime.utcnow(),
        quantidade_desejada=payload.quantidade_desejada,
        quantidade_comprada_externa=payload.quantidade_comprada_externa,
        ativo=payload.ativo,
        criado_em=datetime.utcnow(),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.put("/mimos/{mimo_id}")
def update_mimo(
    mimo_id: int,
    payload: MimoCreateUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    mimo = db.query(Mimo).filter(Mimo.id == mimo_id).first()
    if not mimo:
        raise HTTPException(status_code=404, detail="Mimo não encontrado")

    mimo.asin = payload.asin
    mimo.nome = payload.nome.strip()
    mimo.descricao = payload.descricao
    mimo.imagem_url = payload.imagem_url
    mimo.produto_url = payload.produto_url
    mimo.categoria = payload.categoria
    mimo.preco_atual = payload.preco_atual
    if payload.preco_anterior:
        mimo.preco_anterior = payload.preco_anterior
    mimo.quantidade_desejada = payload.quantidade_desejada
    mimo.quantidade_comprada_externa = payload.quantidade_comprada_externa
    mimo.ativo = payload.ativo

    db.commit()
    db.refresh(mimo)
    return mimo


@router.post("/mimos/{mimo_id}/price")
def update_mimo_price(
    mimo_id: int,
    novo_preco: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    item = manual_update_price(db, mimo_id, "mimo", novo_preco, admin)
    return {"message": "Preço atualizado com sucesso", "preco_atual": item.preco_atual}


# --- Settings ---

@router.get("/config")
def get_all_settings(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    configs = db.query(Configuracao).all()
    return {c.chave: c.valor for c in configs}


@router.put("/config")
def update_settings(
    payload: ConfiguracaoBulkUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    for key, value in payload.configuracoes.items():
        cfg = db.query(Configuracao).filter(Configuracao.chave == key).first()
        if cfg:
            cfg.valor = str(value)
            cfg.atualizado_em = datetime.utcnow()
        else:
            new_cfg = Configuracao(chave=key, valor=str(value), atualizado_em=datetime.utcnow())
            db.add(new_cfg)

    db.commit()
    return {"message": "Configurações atualizadas com sucesso!"}


# --- Exports ---

@router.get("/export/reservations")
def export_reservations(
    status_filter: Optional[str] = Query(None, alias="status"),
    format_type: str = Query("csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    data, filename, content_type = generate_reservations_export(db, status_filter, format_type)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/pix")
def export_pix(
    format_type: str = Query("csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    data, filename, content_type = generate_pix_report(db, format_type)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# --- Audit Logs ---

@router.get("/audit-logs", response_model=List[HistoricoAdminResponse])
def get_audit_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    logs = (
        db.query(HistoricoAdmin)
        .order_by(HistoricoAdmin.criado_em.desc())
        .limit(limit)
        .all()
    )
    result = []
    for log in logs:
        result.append(HistoricoAdminResponse(
            id=log.id,
            administrador_nome=log.administrador.nome if log.administrador else "Sistema Automático",
            reserva_id=log.reserva_id,
            acao=log.acao,
            descricao=log.descricao,
            criado_em=log.criado_em
        ))
    return result
