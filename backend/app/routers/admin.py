from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict, Any

from backend.app.database import get_db
from backend.app.models.models import (
    utcnow,
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
from backend.app.data.seed_data import gerar_faixas_fraldas

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

    # RN-11: alerta de capacidade — mimos disponíveis × números ainda não confirmados
    mimos = db.query(Mimo).filter(Mimo.ativo == True).all()  # noqa: E712
    mimos_disponiveis_total = sum(get_mimo_stock_info(db, m)["disponibilidade_restante"] for m in mimos)
    numeros_nao_confirmados = disponiveis + reservados
    alerta_capacidade = mimos_disponiveis_total < numeros_nao_confirmados

    # RN-01 v2: totais por tamanho de fralda
    por_tamanho = []
    fraldas = (
        db.query(ProdutoPrincipal)
        .order_by(ProdutoPrincipal.ordem_exibicao.asc())
        .all()
    )
    for f in fraldas:
        nums = db.query(Numero).filter(Numero.produto_principal_id == f.id).all()
        por_tamanho.append({
            "produto_id": f.id,
            "tamanho": f.tamanho,
            "nome": f.nome,
            "ativo": f.ativo,
            "total": len(nums),
            "disponiveis": sum(1 for n in nums if n.status == "disponivel"),
            "reservados": sum(1 for n in nums if n.status == "reservado"),
            "confirmados": sum(1 for n in nums if n.status == "confirmado"),
            "compra_externa": sum(1 for n in nums if n.status == "compra_externa"),
        })

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
        top_mimos=top_mimos,
        mimos_disponiveis_total=mimos_disponiveis_total,
        numeros_nao_confirmados=numeros_nao_confirmados,
        alerta_capacidade_mimos=alerta_capacidade,
        por_tamanho=por_tamanho
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
    agora = utcnow()
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
            presente_tamanho=r.numero.produto_principal.tamanho if r.numero.produto_principal else None,
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
        preco_sincronizado_em=utcnow(),
        quantidade_desejada=payload.quantidade_desejada,
        quantidade_comprada_externa=payload.quantidade_comprada_externa,
        ativo=payload.ativo,
        criado_em=utcnow(),
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
    produto.tamanho = payload.tamanho
    produto.ordem_exibicao = payload.ordem_exibicao
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
        preco_sincronizado_em=utcnow(),
        quantidade_desejada=payload.quantidade_desejada,
        quantidade_comprada_externa=payload.quantidade_comprada_externa,
        ativo=payload.ativo,
        criado_em=utcnow(),
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
            cfg.atualizado_em = utcnow()
        else:
            new_cfg = Configuracao(chave=key, valor=str(value), atualizado_em=utcnow())
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


# --- Números (RN-01) ---

@router.get("/numeros")
def list_numeros(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    numeros = db.query(Numero).order_by(Numero.numero.asc()).all()
    return [
        {
            "id": n.id,
            "numero": n.numero,
            "status": n.status,
            "produto_principal_id": n.produto_principal_id,
            "produto_nome": n.produto_principal.nome if n.produto_principal else None,
        }
        for n in numeros
    ]


@router.put("/numeros/quantidade")
def update_total_numeros(
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    RN-01: o administrador pode alterar a quantidade total de números a qualquer momento,
    SEM afetar reservas existentes.
    - Aumentar: cria os novos números (atribuição de presente editável depois).
    - Diminuir: remove apenas números 'disponivel' fora do novo intervalo; números
      reservados/confirmados são preservados incondicionalmente.
    """
    novo_total = payload.get("total")
    if not isinstance(novo_total, int) or novo_total < 1 or novo_total > 1000:
        raise HTTPException(status_code=400, detail="Informe um total de números entre 1 e 1000")

    todos = db.query(Numero).order_by(Numero.numero.asc()).all()
    existentes = {n.numero for n in todos}

    criados = 0
    for num in range(1, novo_total + 1):
        if num not in existentes:
            db.add(Numero(numero=num, status="disponivel", criado_em=utcnow()))
            criados += 1

    removidos = 0
    preservados = 0
    for n in todos:
        if n.numero > novo_total:
            if n.status == "disponivel":
                db.delete(n)
                removidos += 1
            else:
                preservados += 1  # reservado/confirmado: nunca removido

    cfg = db.query(Configuracao).filter(Configuracao.chave == "total_numeros").first()
    if cfg:
        cfg.valor = str(novo_total)
        cfg.atualizado_em = utcnow()
    else:
        db.add(Configuracao(chave="total_numeros", valor=str(novo_total), atualizado_em=utcnow()))

    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="TOTAL_NUMEROS_ALTERADO",
        descricao=(
            f"Quantidade total de números alterada para {novo_total} por {admin.nome}. "
            f"Criados: {criados}. Removidos (disponíveis): {removidos}. "
            f"Preservados por estarem reservados/confirmados: {preservados}."
        ),
        criado_em=utcnow(),
    ))
    db.commit()

    total_final = db.query(Numero).count()
    return {
        "message": "Quantidade de números atualizada.",
        "total": total_final,
        "criados": criados,
        "removidos": removidos,
        "preservados_reservados_ou_confirmados": preservados,
    }


# --- RN-10: compra externa e reatribuição de fralda (v2) ---

@router.put("/numeros/{numero_id}")
def update_numero(
    numero_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Reatribui a fralda de um número (só quando disponível) — RN-01 v2:
    ordem/quantidades são editáveis sem afetar reservas existentes.
    """
    numero = db.query(Numero).filter(Numero.id == numero_id).first()
    if not numero:
        raise HTTPException(status_code=404, detail="Número não encontrado")
    if numero.status != "disponivel":
        raise HTTPException(status_code=400, detail="Apenas números disponíveis podem ter a fralda alterada")

    novo_produto_id = payload.get("produto_principal_id")
    if novo_produto_id is not None:
        produto = db.query(ProdutoPrincipal).filter(ProdutoPrincipal.id == novo_produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail="Fralda não encontrada")
        numero.produto_principal_id = produto.id

    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="NUMERO_REATRIBUIDO",
        descricao=f"Número {numero.numero:02d} reatribuído pelo admin {admin.nome}.",
        criado_em=utcnow(),
    ))
    db.commit()
    return {"message": "Número atualizado.", "numero": numero.numero, "produto_principal_id": numero.produto_principal_id}


@router.post("/numeros/regenerar-faixas")
def regenerar_faixas_numeros(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    RN-01 v2: reagrupar os números em faixas contínuas por fralda, na ordem
    de `ordem_exibicao`, usando as `quantidade_desejada` atuais.

    - Só números 'disponivel' são reatribuídos; 'reservado', 'confirmado' e
      'compra_externa' NUNCA são tocados (reservas existentes preservadas).
    - Números disponíveis fora das novas faixas ficam sem fralda
      (produto_principal_id = NULL) até ajuste manual.
    """
    fraldas = (
        db.query(ProdutoPrincipal)
        .filter(ProdutoPrincipal.ativo == True, ProdutoPrincipal.categoria == "Fraldas")
        .order_by(ProdutoPrincipal.ordem_exibicao.asc(), ProdutoPrincipal.id.asc())
        .all()
    )
    if not fraldas:
        raise HTTPException(status_code=400, detail="Nenhuma fralda ativa cadastrada.")

    faixas = gerar_faixas_fraldas(fraldas)
    # mapa numero -> fralda_id
    mapa = {}
    for faixa in faixas:
        for num in range(faixa["inicio"], faixa["fim"] + 1):
            mapa[num] = faixa["fralda"].id

    numeros = db.query(Numero).order_by(Numero.numero.asc()).all()
    reatribuidos = 0
    preservados = 0
    sem_fralda = 0
    for n in numeros:
        if n.status != "disponivel":
            preservados += 1
            continue
        novo_produto_id = mapa.get(n.numero)
        if n.produto_principal_id != novo_produto_id:
            n.produto_principal_id = novo_produto_id
            reatribuidos += 1
        if novo_produto_id is None:
            sem_fralda += 1

    resumo_faixas = [
        {"tamanho": f["fralda"].tamanho or f["fralda"].nome, "inicio": f["inicio"], "fim": f["fim"]}
        for f in faixas
    ]
    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="FAIXAS_REGERADAS",
        descricao=(
            f"Faixas de números regeradas por {admin.nome}: "
            f"{len(faixas)} grupos, {sum(f['fim'] - f['inicio'] + 1 for f in faixas)} posições. "
            f"Números reatribuídos: {reatribuidos}. Preservados (reservado/confirmado/compra externa): {preservados}. "
            f"Disponíveis sem fralda: {sem_fralda}."
        ),
        criado_em=utcnow(),
    ))
    db.commit()
    return {
        "message": "Faixas de números regeradas com sucesso.",
        "faixas": resumo_faixas,
        "numeros_reatribuidos": reatribuidos,
        "numeros_preservados": preservados,
        "numeros_disponiveis_sem_fralda": sem_fralda,
    }


@router.post("/numeros/{numero_id}/compra-externa")
def marcar_compra_externa(
    numero_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    RN-10: alguém comprou a fralda direto na lista da Amazon, sem passar pelo site.
    O administrador marca o número como ocupado por compra externa (fica cinza,
    com a origem registrada) ou desfaz a marcação.
    """
    numero = db.query(Numero).filter(Numero.id == numero_id).first()
    if not numero:
        raise HTTPException(status_code=404, detail="Número não encontrado")

    marcar = bool(payload.get("marcar", True))
    origem = (payload.get("origem") or "Comprada direto na lista da Amazon").strip()

    if marcar:
        if numero.status in ("reservado", "confirmado"):
            raise HTTPException(
                status_code=400,
                detail="Este número tem reserva ativa. Libere a reserva antes de marcar como compra externa."
            )
        numero.status = "compra_externa"
        numero.origem_ocupacao = origem
        acao_desc = f"Número {numero.numero:02d} marcado como COMPRADO EXTERNAMENTE por {admin.nome}. Origem: {origem}."
        acao = "NUMERO_COMPRA_EXTERNA"
    else:
        if numero.status != "compra_externa":
            raise HTTPException(status_code=400, detail="Este número não está marcado como compra externa.")
        numero.status = "disponivel"
        numero.origem_ocupacao = None
        acao_desc = f"Marcação de compra externa removida do número {numero.numero:02d} por {admin.nome}."
        acao = "NUMERO_COMPRA_EXTERNA_REMOVIDA"

    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao=acao,
        descricao=acao_desc,
        criado_em=utcnow(),
    ))
    db.commit()
    return {"message": acao_desc, "numero": numero.numero, "status": numero.status}


@router.put("/mimos/{mimo_id}/estoque-externo")
def ajustar_estoque_externo_mimo(
    mimo_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    RN-10: informa quantas unidades de um mimo já foram compradas fora do site
    (descontadas do estoque disponível; o ajuste manual prevalece — RN-09).
    """
    mimo = db.query(Mimo).filter(Mimo.id == mimo_id).first()
    if not mimo:
        raise HTTPException(status_code=404, detail="Mimo não encontrado")

    quantidade = payload.get("quantidade_comprada_externa")
    if not isinstance(quantidade, int) or quantidade < 0:
        raise HTTPException(status_code=400, detail="Informe uma quantidade externa inteira maior ou igual a zero")
    if quantidade > mimo.quantidade_desejada:
        raise HTTPException(status_code=400, detail="A quantidade externa não pode ser maior que a quantidade desejada")

    mimo.quantidade_comprada_externa = quantidade
    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="MIMO_ESTOQUE_EXTERNO",
        descricao=f"Estoque externo do mimo '{mimo.nome}' ajustado para {quantidade} por {admin.nome}.",
        criado_em=utcnow(),
    ))
    db.commit()
    info = get_mimo_stock_info(db, mimo)
    return {"message": "Estoque externo atualizado.", "disponibilidade_restante": info["disponibilidade_restante"]}
