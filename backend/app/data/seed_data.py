from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.database import engine, Base, SessionLocal
from backend.app.models.models import (
    Admin, ProdutoPrincipal, Mimo, Numero, Configuracao, HistoricoAdmin
)
from backend.app.services.auth_service import get_password_hash
from backend.app.models.models import utcnow
from backend.app.data.mimos_reais import SEED_MIMOS_REAIS
from decimal import Decimal


# ============================================================
# FRALDAS DA TALIA — DADOS REAIS da lista copiada pelo casal em
# 06/11/2026 (tabela do briefing v2). Os 5 itens somam exatamente
# 100 unidades, uma por número, em faixas contínuas:
#   RN  01-10 · RN+ 11-20 · P 21-50 · M 51-75 · G 76-100
# Preços mudam (ofertas/Black Friday); o painel é a fonte para
# atualizar preço e data. Preço ausente fica NULO (o casal informa
# manualmente — RN-08 v2): hoje só a fralda M ("Ver opções").
# ============================================================
SEED_FRALDAS_REAIS = [
    {
        "asin": "B07GQB93FT",
        "nome": "Pampers Primeiros Dias RN (até 4 kg), 36 un",
        "tamanho": "RN",
        "ordem_exibicao": 1,
        "categoria": "Fraldas",
        "descricao": "Fralda Pampers Primeiros Dias tamanho RN (até 4 kg), pacote com 36 unidades. Oferta em 06/11/2026: R$ 39,98 (antes R$ 52,83).",
        "preco_atual": 39.98,
        "preco_anterior": 52.83,
        "produto_url": "https://www.amazon.com.br/dp/B07GQB93FT",
        "quantidade_desejada": 10,
        "ativo": True,
    },
    {
        "asin": "B0GY6GG8R7",
        "nome": "Pampers Recém Nascido RN+ (até 5 kg), 36 un",
        "tamanho": "RN+",
        "ordem_exibicao": 2,
        "categoria": "Fraldas",
        "descricao": "Fralda Pampers Recém Nascido tamanho RN+ (até 5 kg), pacote com 36 unidades. Oferta em 06/11/2026: R$ 45,13 (antes R$ 52,83).",
        "preco_atual": 45.13,
        "preco_anterior": 52.83,
        "produto_url": "https://www.amazon.com.br/dp/B0GY6GG8R7",
        "quantidade_desejada": 10,
        "ativo": True,
    },
    {
        "asin": "B07GQ136TS",
        "nome": "Pampers Premium Care P, 40 un",
        "tamanho": "P",
        "ordem_exibicao": 3,
        "categoria": "Fraldas",
        "descricao": "Fralda Pampers Premium Care tamanho P, pacote com 40 unidades. Oferta em 06/11/2026: R$ 54,99 (antes R$ 71,67).",
        "preco_atual": 54.99,
        "preco_anterior": 71.67,
        "produto_url": "https://www.amazon.com.br/dp/B07GQ136TS",
        "quantidade_desejada": 30,
        "ativo": True,
    },
    {
        "asin": "B07D3SVCTZ",
        "nome": "Pampers Confort Sec M, 44 un",
        "tamanho": "M",
        "ordem_exibicao": 4,
        "categoria": "Fraldas",
        "descricao": "Fralda Pampers Confort Sec tamanho M, pacote com 44 unidades. Sem preço na lista em 06/11/2026 (Amazon mostra \"Ver opções de compra\"); informar manualmente no painel.",
        "preco_atual": None,
        "preco_anterior": None,
        "produto_url": "https://www.amazon.com.br/dp/B07D3SVCTZ",
        "quantidade_desejada": 25,
        "ativo": True,
    },
    {
        "asin": "B07X83MH7M",
        "nome": "Pampers Premium Care Pants G, 68 un",
        "tamanho": "G",
        "ordem_exibicao": 5,
        "categoria": "Fraldas",
        "descricao": "Fralda Pampers Premium Care Pants tamanho G, pacote com 68 unidades. Oferta em 06/11/2026: R$ 93,90 (antes R$ 151,59).",
        "preco_atual": 93.90,
        "preco_anterior": 151.59,
        "produto_url": "https://www.amazon.com.br/dp/B07X83MH7M",
        "quantidade_desejada": 25,
        "ativo": True,
    },
]

# Data da cópia da lista pelo casal (usada como preco_sincronizado_em inicial)
# ============================================================
# MIMOS DEMO — dados EXEMPLIFICATIVOS (NÃO são a lista real do Lucas).
# Criados apenas em desenvolvimento (SEED_DEMO). A lista real do
# Lucas (cerca de 58 itens, ~113 unidades) deve ser IMPORTADA via
# texto/CSV/JSON no painel (aba Mimos → Importar lista por texto).
# ============================================================
SEED_MIMOS_DEMO = [
    {
        "asin": "B07P8N9B1V",
        "nome": "Kit 3 Paninhos de Boca Papi Soft 100% Algodão",
        "categoria": "Cuidados Diários",
        "descricao": "Panos de boca macios com acabamento delicado em crochê, tecido felpudo absorvente.",
        "preco_atual": 29.90,
        "imagem_url": "https://m.media-amazon.com/images/I/71Yv3w1PqAL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07P8N9B1V",
        "quantidade_desejada": 15,
    },
    {
        "asin": "B083Q7L2K9",
        "nome": "Mordedor Massageador de Gengiva com Água Chicco",
        "categoria": "Conforto e Dentição",
        "descricao": "Alivia as gengivas no período de dentição. Pode ser refrigerado para efeito calmante.",
        "preco_atual": 34.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61H4h2f6Y1L._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B083Q7L2K9",
        "quantidade_desejada": 12,
    },
    {
        "asin": "B0912P7X3M",
        "nome": "Kit Pente e Escova de Cerdas Naturais Macias",
        "categoria": "Higiene",
        "descricao": "Escova ultra macia indicada para recém-nascidos e pente com pontas arredondadas.",
        "preco_atual": 39.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61k1qP5s8rL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B0912P7X3M",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B08B5Q2N8L",
        "nome": "Kit Cortador de Unha e Tesourinha de Ponta Redonda",
        "categoria": "Higiene e Segurança",
        "descricao": "Conjunto seguro e preciso com tesoura de lâmina curva, cortador e lixa especial para bebê.",
        "preco_atual": 45.00,
        "imagem_url": "https://m.media-amazon.com/images/I/61xR4w5s9pL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08B5Q2N8L",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B07K9Q3W2P",
        "nome": "Naninha Aconchego com Pelúcia Ursinho Lael",
        "categoria": "Sono e Conforto",
        "descricao": "Naninha macia antialérgica com carinha de ursinho para transmitir calma e segurança na hora de dormir.",
        "preco_atual": 49.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61jC8y1P4hL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07K9Q3W2P",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B094K8X5N2",
        "nome": "Kit 3 Pares de Meias Recém-Nascido Algodão Pima",
        "categoria": "Vestuário",
        "descricao": "Meias anatômicas que não apertam o tornozelo do bebê, tecido respirável e toque aveludado.",
        "preco_atual": 35.00,
        "imagem_url": "https://m.media-amazon.com/images/I/71oD4w5y8hL._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B094K8X5N2",
        "quantidade_desejada": 15,
    },
    {
        "asin": "B089X2Q4P1",
        "nome": "Termômetro Digital Clínico Flexível à Prova d'Água",
        "categoria": "Saúde",
        "descricao": "Leitura rápida em 10 segundos com ponta macia flexível e alarme sonoro de febre.",
        "preco_atual": 42.90,
        "imagem_url": "https://m.media-amazon.com/images/I/51w7rZ4M8sL._AC_SL1000_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B089X2Q4P1",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B07Y7M4K9Q",
        "nome": "Kit 2 Chupetas Ortodônticas Philips Avent Ultra Air",
        "categoria": "Conforto",
        "descricao": "Bico de silicone macio com escudo leve e 4 orifícios de ventilação para pele sensível.",
        "preco_atual": 59.90,
        "imagem_url": "https://m.media-amazon.com/images/I/616mWS8YBLL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07Y7M4K9Q",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B08L7Q3X1P",
        "nome": "Porta Chupeta Higiênico com Alça de Silicone",
        "categoria": "Acessórios",
        "descricao": "Mantém as chupetas limpas e protegidas de bactérias durante os passeios com fecho fácil.",
        "preco_atual": 24.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61Gq8m4y3jL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08L7Q3X1P",
        "quantidade_desejada": 12,
    },
    {
        "asin": "B092K7P4N8",
        "nome": "Aspirador Nasal com Filtro de Proteção Lillo",
        "categoria": "Saúde e Respiração",
        "descricao": "Desobstrui suavemente o nariz do bebê, facilitando a respiração e a alimentação.",
        "preco_atual": 38.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61tC8y1K5oL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B092K7P4N8",
        "quantidade_desejada": 10,
    },
]

DEFAULT_CONFIGS = {
    "nome_evento": "Chá de Rifa do Lael",
    "data_evento": "Março de 2027",
    "whatsapp_casal": "85999998888",
    "chave_pix": "lael2027@chaderifa.com.br",
    "tipo_chave_pix": "E-mail",
    "titular_pix": "Talia Vitória e Lucas Gabriel",
    "banco_pix": "Nubank",
    "prazo_padrao_horas": "72",
    "total_numeros": "100",
    "mensagem_inicial": "Sejam muito bem-vindos ao Chá de Rifa do Lael! Cada número representa uma fralda da lista da nossa família e amigos para a chegada do nosso menino em março de 2027, em Fortaleza — CE.",
    "mensagem_confirmacao": "Recebemos sua reserva com muito carinho! Para confirmar seu número, por favor nos envie os comprovantes da compra na Amazon e/ou do Pix pelo WhatsApp.",
    "mensagem_expiracao": "O prazo da sua reserva expirou e o número voltou a ficar disponível. Caso deseje contribuir, sinta-se à vontade para escolher um novo número!",
    # LGPD: retenção de dados pessoais (dias) após a criação da reserva
    "retencao_dias_preservacao": "180",
}


def _demo_enabled() -> bool:
    """
    Mimos DEMO (lista exemplificativa, NÃO é a lista real do Lucas):
    criados apenas fora de produção. Em produção os mimos reais entram
    por importação (texto/CSV/JSON) ou cadastro manual no painel.
    """
    import os
    env = os.getenv("ENVIRONMENT", "development").lower()
    seed_demo = os.getenv("SEED_DEMO", "").lower()
    if env == "production" or seed_demo == "false":
        return False
    return env != "production" or seed_demo == "true"


def gerar_faixas_fraldas(fraldas_ordenadas):
    """
    RN-01 v2: gera as FAIXAS CONTÍNUAS de números por fralda, em ordem crescente.
    Nunca intercala tamanhos. Ex.: RN 01-10, P 11-40, M 41-65, G 66-90, 5º 91-100.
    """
    faixas = []
    numero_atual = 1
    for fralda in fraldas_ordenadas:
        faixas.append({
            "fralda": fralda,
            "inicio": numero_atual,
            "fim": numero_atual + fralda.quantidade_desejada - 1,
        })
        numero_atual += fralda.quantidade_desejada
    return faixas


def init_database_seed():
    """
    Cria tabelas e popula o banco.

    - FRALDAS: dados REAIS da lista da Talia (tabela do briefing v2), sempre
      criados. Os 100 números são gerados a partir das quantidades desejadas,
      agrupados por tamanho em ordem crescente (RN-01 v2).
    - MIMOS: dados REAIS da lista do Lucas (58 itens / 113 unidades) sempre
      semeados; a lista DEMO só é criada em desenvolvimento quando NÃO há
      nenhum mimo cadastrado, e DEMO remanescentes são desativados.
    - Administrador: criado SOMENTE via ADMIN_EMAIL/ADMIN_PASSWORD ou
      `python -m backend.app.create_admin`. NUNCA há senha padrão.
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        import os

        # 1. Admin — somente via variáveis de ambiente (sem senha padrão)
        admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
        if admin_email and admin_password:
            admin = db.query(Admin).filter(Admin.email == admin_email.lower()).first()
            if not admin:
                admin = Admin(
                    nome="Talia e Lucas",
                    email=admin_email.lower(),
                    senha_hash=get_password_hash(admin_password),
                    ativo=True,
                    criado_em=utcnow(),
                )
                db.add(admin)
                db.flush()
                print(f"[SEED] Administrador '{admin_email}' criado a partir de variáveis de ambiente.")

        # 2. Configurations
        for k, v in DEFAULT_CONFIGS.items():
            cfg = db.query(Configuracao).filter(Configuracao.chave == k).first()
            if not cfg:
                db.add(Configuracao(chave=k, valor=v, atualizado_em=utcnow()))

        # 3. FRALDAS REAIS (RN-01 v2) — casa pelo TAMANHO do grupo;
        #    atualiza apenas campos vazios (NUNCA sobrescreve preço ou link
        #    informados manualmente pelo casal no painel — RN-08).
        fraldas_map = []
        for f_data in SEED_FRALDAS_REAIS:
            existing = db.query(ProdutoPrincipal).filter(ProdutoPrincipal.tamanho == f_data["tamanho"]).first()
            if not existing:
                preco = None
                if f_data["preco_atual"] is not None:
                    preco = Decimal(str(f_data["preco_atual"]))
                preco_anterior = None
                if f_data.get("preco_anterior") is not None:
                    preco_anterior = Decimal(str(f_data["preco_anterior"]))
                prod = ProdutoPrincipal(
                    asin=f_data["asin"],
                    nome=f_data["nome"],
                    tamanho=f_data["tamanho"],
                    ordem_exibicao=f_data["ordem_exibicao"],
                    categoria=f_data["categoria"],
                    descricao=f_data["descricao"],
                    preco_atual=preco,
                    preco_anterior=preco_anterior,
                    preco_sincronizado_em=utcnow(),
                    imagem_url=f_data.get("imagem_url"),
                    produto_url=f_data["produto_url"],
                    quantidade_desejada=f_data["quantidade_desejada"],
                    quantidade_comprada_externa=0,
                    ativo=f_data["ativo"],
                    criado_em=utcnow(),
                )
                db.add(prod)
                db.flush()
                fraldas_map.append(prod)
            else:
                # Preenche só o que estiver vazio — edição manual do casal prevalece
                if not existing.nome:
                    existing.nome = f_data["nome"]
                if existing.preco_atual is None and f_data["preco_atual"] is not None:
                    existing.preco_atual = Decimal(str(f_data["preco_atual"]))
                    existing.preco_sincronizado_em = utcnow()
                if not existing.produto_url and f_data["produto_url"]:
                    existing.produto_url = f_data["produto_url"]
                if not existing.asin and f_data["asin"]:
                    existing.asin = f_data["asin"]
                fraldas_map.append(existing)

        # 4a. MIMOS REAIS do Lucas (58 itens / 113 unidades, lista copiada em
        #     06/11/2026) — sempre semeados, inclusive em produção. Casa pelo
        #     NOME; atualiza apenas campos vazios (edição manual prevalece).
        mimos_reais_criados = 0
        for m_data in SEED_MIMOS_REAIS:
            existing_mimo = db.query(Mimo).filter(Mimo.nome == m_data["nome"]).first()
            if not existing_mimo:
                preco = Decimal(str(m_data["preco_atual"])) if m_data["preco_atual"] is not None else None
                preco_ant = Decimal(str(m_data["preco_anterior"])) if m_data.get("preco_anterior") is not None else None
                db.add(Mimo(
                    asin=None,
                    nome=m_data["nome"],
                    categoria=m_data["categoria"],
                    descricao=m_data.get("descricao"),
                    preco_atual=preco,
                    preco_anterior=preco_ant,
                    preco_sincronizado_em=utcnow(),
                    imagem_url=None,
                    produto_url=None,
                    quantidade_desejada=m_data["quantidade_desejada"],
                    quantidade_comprada_externa=0,
                    ativo=True,
                    criado_em=utcnow(),
                ))
                mimos_reais_criados += 1
            else:
                # Preenche só o que estiver vazio — edição manual do casal prevalece
                if existing_mimo.preco_atual is None and m_data["preco_atual"] is not None:
                    existing_mimo.preco_atual = Decimal(str(m_data["preco_atual"]))
                    existing_mimo.preco_sincronizado_em = utcnow()
                if existing_mimo.preco_anterior is None and m_data.get("preco_anterior") is not None:
                    existing_mimo.preco_anterior = Decimal(str(m_data["preco_anterior"]))
                if not existing_mimo.categoria and m_data["categoria"]:
                    existing_mimo.categoria = m_data["categoria"]
                if not existing_mimo.ativo:
                    existing_mimo.ativo = True

        # 4b. Mimos DEMO — apenas em desenvolvimento E somente se ainda não
        #     houver mimos reais cadastrados (evita produto fictício no site).
        #     Também desativa DEMO remanescentes de bancos antigos.
        demo_asins = {m["asin"] for m in SEED_MIMOS_DEMO}
        if _demo_enabled():
            if db.query(Mimo).filter(Mimo.categoria.in_({m["categoria"] for m in SEED_MIMOS_REAIS})).count() == 0 \
                    and db.query(Mimo).count() == 0:
                for m_data in SEED_MIMOS_DEMO:
                    existing_mimo = db.query(Mimo).filter(Mimo.asin == m_data["asin"]).first()
                    if not existing_mimo:
                        db.add(Mimo(
                            asin=m_data["asin"],
                            nome=m_data["nome"],
                            categoria=m_data["categoria"],
                            descricao=m_data["descricao"],
                            preco_atual=Decimal(str(m_data["preco_atual"])),
                            preco_sincronizado_em=utcnow(),
                            imagem_url=m_data["imagem_url"],
                            produto_url=m_data["produto_url"],
                            quantidade_desejada=m_data["quantidade_desejada"],
                            quantidade_comprada_externa=0,
                            ativo=True,
                            criado_em=utcnow(),
                        ))
        # Desativa mimos DEMO remanescentes (bancos de dev antigos) —
        # nunca devem aparecer para convidados junto aos dados reais.
        db.query(Mimo).filter(Mimo.asin.in_(demo_asins), Mimo.ativo == True).update(
            {Mimo.ativo: False}, synchronize_session=False
        )

        # 5. Números gerados a partir das fraldas, em FAIXAS CONTÍNUAS por tamanho (RN-01 v2)
        #    10 RN + 10 RN+ + 30 P + 25 M + 25 G = 100 — nunca intercalados
        #    Faixas: RN 01-10 · RN+ 11-20 · P 21-50 · M 51-75 · G 76-100
        fraldas_ordenadas = sorted(fraldas_map, key=lambda f: f.ordem_exibicao)
        criados = 0
        for faixa in gerar_faixas_fraldas(fraldas_ordenadas):
            fralda = faixa["fralda"]
            for num in range(faixa["inicio"], faixa["fim"] + 1):
                existing_num = db.query(Numero).filter(Numero.numero == num).first()
                if not existing_num:
                    db.add(Numero(
                        numero=num,
                        produto_principal_id=fralda.id,
                        status="disponivel",
                        criado_em=utcnow(),
                    ))
                    criados += 1
                elif existing_num.produto_principal_id is None:
                    existing_num.produto_principal_id = fralda.id

        total_fraldas = sum(f.quantidade_desejada for f in fraldas_ordenadas)
        cfg_total = db.query(Configuracao).filter(Configuracao.chave == "total_numeros").first()
        if cfg_total and cfg_total.valor != str(total_fraldas):
            cfg_total.valor = str(total_fraldas)
            cfg_total.atualizado_em = utcnow()

        db.commit()
        total_mimos = db.query(Mimo).filter(Mimo.ativo == True).count()
        print(f"[SEED] Banco inicializado: fraldas REAIS da Talia + {total_mimos} mimos ativos "
              f"({mimos_reais_criados} da lista real do Lucas recém-importados).")
        if not admin_email or not admin_password:
            print("[SEED] Nenhum administrador criado. Use ADMIN_EMAIL/ADMIN_PASSWORD no ambiente "
                  "ou execute: python -m backend.app.create_admin <email> <senha>")
    except Exception as e:
        db.rollback()
        print(f"[SEED] Erro ao inicializar seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_database_seed()
