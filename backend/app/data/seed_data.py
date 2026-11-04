import json
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.database import engine, Base, SessionLocal
from backend.app.models.models import (
    Admin, ProdutoPrincipal, Mimo, Numero, Configuracao, HistoricoAdmin
)
from backend.app.services.auth_service import get_password_hash


SEED_PRODUTOS_PRINCIPAIS = [
    {
        "asin": "B08N5M7S6L",
        "nome": "Berço Portátil com Mosquiteiro e Trocador",
        "categoria": "Mobiliário e Quarto",
        "descricao": "Berço versátil dobrável com 2 alturas, trocador acoplado, bolsa de transporte e mosquiteiro.",
        "preco_atual": 489.90,
        "imagem_url": "https://m.media-amazon.com/images/I/71Y8w4E1c7L._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08N5M7S6L",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B0912K8J7P",
        "nome": "Carrinho de Bebê com Bebê Conforto Voyage",
        "categoria": "Passeio",
        "descricao": "Conjunto Travel System completo, reclinável em modo berço, cinto de 5 pontos e capota retrátil.",
        "preco_atual": 799.00,
        "imagem_url": "https://m.media-amazon.com/images/I/61kM56gBfGL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B0912K8J7P",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B07P7J9L2B",
        "nome": "Cadeira de Alimentação Portátil Chicco Pocket Snack",
        "categoria": "Alimentação",
        "descricao": "Compacta, leve e ajustável em 3 alturas. Bandeja removível e alça para transporte.",
        "preco_atual": 249.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61b7Lh8w2tL._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07P7J9L2B",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B089K8T4W9",
        "nome": "Kit Banheira Ergonômica com Suporte e Termômetro",
        "categoria": "Banho e Higiene",
        "descricao": "Banheira com suporte elevado, assento redutor ergonômico e mangueira de escoamento rápido.",
        "preco_atual": 199.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61G4w92T5fL._AC_SL1000_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B089K8T4W9",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B07XQ8N65V",
        "nome": "Babá Eletrônica Digital com Câmera e Visão Noturna",
        "categoria": "Segurança e Conforto",
        "descricao": "Tela LCD 3.2 polegadas, áudio bidirecional, sensor de temperatura e canções de ninar integradas.",
        "preco_atual": 329.00,
        "imagem_url": "https://m.media-amazon.com/images/I/61Q6qQ4W4CL._AC_SL1200_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07XQ8N65V",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B08H9Q3W7P",
        "nome": "Esterilizador e Aquecedor de Mamadeiras Digital",
        "categoria": "Alimentação",
        "descricao": "Esteriliza a vapor em 8 minutos e aquece leite materno ou fórmulas na temperatura ideal com display touch.",
        "preco_atual": 179.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61Vl+K8rZ4L._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08H9Q3W7P",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B07Z8L3K9Q",
        "nome": "Mochila Maternidade Multifunção Térmica Impermeável",
        "categoria": "Passeio e Cuidados",
        "descricao": "Amplo espaço interno, bolsos térmicos para mamadeiras, compartimento impermeável para roupas úmidas e porta USB.",
        "preco_atual": 159.90,
        "imagem_url": "https://m.media-amazon.com/images/I/71uV4j5o0iL._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B07Z8L3K9Q",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B08C7P3R8M",
        "nome": "Almofada de Amamentação Anatômica 100% Algodão",
        "categoria": "Conforto",
        "descricao": "Proporciona apoio perfeito para os braços da mãe e postura correta para o bebê durante as mamadas.",
        "preco_atual": 129.90,
        "imagem_url": "https://m.media-amazon.com/images/I/61q3kY4c0sL._AC_SL1000_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08C7P3R8M",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B0947X2N1L",
        "nome": "Kit Berço 100% Algodão 180 Fios Nuvem Celeste",
        "categoria": "Enxoval",
        "descricao": "Conjunto com protetores laterais almofadados, lençol com elástico, fronha e edredom antialérgico.",
        "preco_atual": 269.90,
        "imagem_url": "https://m.media-amazon.com/images/I/71M3n0c0q0L._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B0947X2N1L",
        "quantidade_desejada": 10,
    },
    {
        "asin": "B08K9M3X5P",
        "nome": "Tapete de Atividades com Arco de Brinquedos e Piano Musical",
        "categoria": "Brinquedos e Desenvolvimento",
        "descricao": "Estimula o desenvolvimento sensorial e motor com músicas interativas, chocalhos e cores suaves.",
        "preco_atual": 189.90,
        "imagem_url": "https://m.media-amazon.com/images/I/71kC3lZ7FzL._AC_SL1500_.jpg",
        "produto_url": "https://www.amazon.com.br/dp/B08K9M3X5P",
        "quantidade_desejada": 10,
    },
]

SEED_MIMOS = [
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
        "imagem_url": "https://m.media-amazon.com/images/I/61kM58uP2wL._AC_SL1500_.jpg",
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
    "mensagem_inicial": "Sejam muito bem-vindos ao Chá de Rifa do Lael! Cada número representa uma bênção e o carinho da nossa família e amigos para a chegada do nosso menino em março de 2027, em Fortaleza — CE.",
    "mensagem_confirmacao": "Recebemos sua reserva com muito carinho! Para confirmar seu número, por favor nos envie os comprovantes da compra na Amazon e/ou do Pix pelo WhatsApp.",
    "mensagem_expiracao": "O prazo da sua reserva expirou e o número voltou a ficar disponível. Caso deseje contribuir, sinta-se à vontade para escolher um novo número!",
}


def init_database_seed():
    """
    Creates tables and seeds default admin, settings, products, mimos and 100 raffle numbers.
    """
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        agora = datetime.utcnow()

        # 1. Admin
        admin = db.query(Admin).filter(Admin.email == "admin@chaderifa.com.br").first()
        if not admin:
            admin = Admin(
                nome="Talia e Lucas",
                email="admin@chaderifa.com.br",
                senha_hash=get_password_hash("admin123"),
                ativo=True,
                criado_em=agora,
            )
            db.add(admin)
            db.flush()

        # 2. Configurations
        for k, v in DEFAULT_CONFIGS.items():
            cfg = db.query(Configuracao).filter(Configuracao.chave == k).first()
            if not cfg:
                db.add(Configuracao(chave=k, valor=v, atualizado_em=agora))

        # 3. Produtos Principais
        produtos_map = []
        for p_data in SEED_PRODUTOS_PRINCIPAIS:
            existing = db.query(ProdutoPrincipal).filter(ProdutoPrincipal.asin == p_data["asin"]).first()
            if not existing:
                prod = ProdutoPrincipal(
                    asin=p_data["asin"],
                    nome=p_data["nome"],
                    categoria=p_data["categoria"],
                    descricao=p_data["descricao"],
                    preco_atual=p_data["preco_atual"],
                    preco_anterior=p_data["preco_atual"] * 1.15,
                    preco_sincronizado_em=agora,
                    imagem_url=p_data["imagem_url"],
                    produto_url=p_data["produto_url"],
                    quantidade_desejada=p_data["quantidade_desejada"],
                    quantidade_comprada_externa=0,
                    ativo=True,
                    criado_em=agora,
                )
                db.add(prod)
                db.flush()
                produtos_map.append(prod)
            else:
                produtos_map.append(existing)

        # 4. Mimos
        for m_data in SEED_MIMOS:
            existing_mimo = db.query(Mimo).filter(Mimo.asin == m_data["asin"]).first()
            if not existing_mimo:
                mimo = Mimo(
                    asin=m_data["asin"],
                    nome=m_data["nome"],
                    categoria=m_data["categoria"],
                    descricao=m_data["descricao"],
                    preco_atual=m_data["preco_atual"],
                    preco_anterior=m_data["preco_atual"] * 1.12,
                    preco_sincronizado_em=agora,
                    imagem_url=m_data["imagem_url"],
                    produto_url=m_data["produto_url"],
                    quantidade_desejada=m_data["quantidade_desejada"],
                    quantidade_comprada_externa=0,
                    ativo=True,
                    criado_em=agora,
                )
                db.add(mimo)

        # 5. 100 Raffle Numbers (01 to 100)
        existing_numbers_count = db.query(Numero).count()
        if existing_numbers_count < 100:
            for num in range(1, 101):
                existing_num = db.query(Numero).filter(Numero.numero == num).first()
                if not existing_num:
                    # Distribute products across numbers cyclically
                    prod_for_num = produtos_map[(num - 1) % len(produtos_map)]
                    numero = Numero(
                        numero=num,
                        produto_principal_id=prod_for_num.id,
                        status="disponivel",
                        criado_em=agora,
                    )
                    db.add(numero)

        db.commit()
        print("[SEED] Banco de dados inicializado com sucesso (Admin, Configs, 100 Números, Presentes e Mimos).")
    except Exception as e:
        db.rollback()
        print(f"[SEED] Erro ao inicializar seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_database_seed()
