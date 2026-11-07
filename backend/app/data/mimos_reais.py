# ============================================================
# MIMOS DO LUCAS — DADOS REAIS copiados da lista da Amazon pelo
# casal em 06/11/2026 (texto colado no chat, formato de página
# de lista de presentes). 58 produtos, 113 unidades no total,
# em 7 categorias reais.
#
# Regras de leitura do texto colado:
# - "Comprado: 0 de N"  -> quantidade_desejada = N
# - "De: R$ X"          -> preco_anterior
# - "R$ A R$ B" (sem "De:") -> A = preço atual (Pix/oferta), B = anterior
# - "Ver opções de compra" -> preco_atual = None (admin informa)
# - "Somente N em estoque" -> estoque da Amazon, NÃO é a quantidade
#   desejada da lista; ignorado.
# - Sufixo " | ..." do título Amazon (variantes) foi removido do nome.
# - ASIN/imagem/link não vieram no texto -> ficam nulos; o casal
#   pode completar no painel (Mimos → Editar).
# ============================================================

SEED_MIMOS_REAIS = [
    # ---------- Roupas de bebê (3 produtos / 3 unidades) ----------
    {"nome": "Body Bebê Kit 5 Peças Manga Curta Liso Masculino", "categoria": "Roupas de bebê", "quantidade_desejada": 1, "preco_atual": 62.98, "preco_anterior": 69.99},
    {"nome": "Combo 3 Macacão Minimalista para Bebês de 0 a 12 Meses - Tecido Respirável de Algodão, Abertura em Zíper", "categoria": "Roupas de bebê", "quantidade_desejada": 1, "preco_atual": 64.16, "preco_anterior": 78.99},
    {"nome": "Body Bebe Kit 6 Peças Menina Ou Menino INVERNO Enxoval Recém Nascido", "categoria": "Roupas de bebê", "quantidade_desejada": 1, "preco_atual": 80.65, "preco_anterior": 84.90},

    # ---------- Produtos de banho (10 produtos / 14 unidades) ----------
    {"nome": "Giby e Gaby Deo Colônia Amarelo 200ml", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 16.42, "preco_anterior": 21.98},
    {"nome": "Toalha de Banho com Capuz Karinho Soft Especial, Estampada", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 31.84, "preco_anterior": None},
    {"nome": "Toalha de Banho Papi Textil C/Capuz, Contem 01 Un", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 29.19, "preco_anterior": 33.63},
    {"nome": "Toalha de Banho com Capuz Karinho, Estampada, Soft", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 32.80, "preco_anterior": 41.26},
    {"nome": "Óleo Hidratante de Amêndoas para Bebê Johnson's Baby, 200ml", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 56.59, "preco_anterior": 72.99},
    {"nome": "Buba Rede De Proteção Para Banheira Cinza", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 38.14, "preco_anterior": 44.40},
    {"nome": "Sabonete Líquido Johnson's Baby Recém-Nascidos, 200ml", "categoria": "Produtos de banho", "quantidade_desejada": 3, "preco_atual": 23.42, "preco_anterior": 34.49},
    {"nome": "Loção Hidratante Corporal Johnson's Baby Recém-Nascidos, 200ml", "categoria": "Produtos de banho", "quantidade_desejada": 3, "preco_atual": 41.85, "preco_anterior": 62.99},
    {"nome": "Toalha de Banho Soft Bamboo Mami com Capuz", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 86.70, "preco_anterior": 120.61},
    {"nome": "Toalha de Banho Soft Papi Friends com Capuz, Branco/Cinza", "categoria": "Produtos de banho", "quantidade_desejada": 1, "preco_atual": 73.99, "preco_anterior": None},

    # ---------- Troca de fraldas (9 produtos / 47 unidades) ----------
    {"nome": "Lenços Umedecidos Johnson's Baby Recém-Nascido, 48 Unidades", "categoria": "Troca de fraldas", "quantidade_desejada": 10, "preco_atual": 13.90, "preco_anterior": 22.29},
    {"nome": "Algodão Em Disco Duo Face York 50 Unidades", "categoria": "Troca de fraldas", "quantidade_desejada": 10, "preco_atual": 8.79, "preco_anterior": None},
    {"nome": "Algodão Quadrado para Bebê Bellacotton, 100% Algodão, 100 Unidades", "categoria": "Troca de fraldas", "quantidade_desejada": 10, "preco_atual": 26.00, "preco_anterior": 29.90},
    {"nome": "Trocador de Fraldas Portátil Papi Friends, Branco, Espuma e PVC", "categoria": "Troca de fraldas", "quantidade_desejada": 1, "preco_atual": 41.32, "preco_anterior": 43.50},
    {"nome": "Bepantol Baby Pomada Assadura Bebe, Hipoalergênica, 30g", "categoria": "Troca de fraldas", "quantidade_desejada": 10, "preco_atual": 18.74, "preco_anterior": 23.52},
    {"nome": "Lenços Umedecidos Pampers Aroma de Aloe Vera 192 Unidades", "categoria": "Troca de fraldas", "quantidade_desejada": 3, "preco_atual": 40.46, "preco_anterior": 46.70},
    {"nome": "Toalha de Fralda Papi 100cm x 70cm Contem 03 Un", "categoria": "Troca de fraldas", "quantidade_desejada": 1, "preco_atual": 21.78, "preco_anterior": 28.18},
    {"nome": "Fralda Pano de Bebê Mami 70 cm x 70 cm Pacote com 5 Unidades, Azul", "categoria": "Troca de fraldas", "quantidade_desejada": 1, "preco_atual": 52.00, "preco_anterior": None},
    {"nome": "Fralda Soft Papi Textil Papi Friends", "categoria": "Troca de fraldas", "quantidade_desejada": 1, "preco_atual": 90.06, "preco_anterior": None},

    # ---------- Alimentação (4 produtos / 4 unidades) ----------
    {"nome": "Bicos Pétala 3.0 Philips Avent com válvula anticólicas, fluxo extra rápido (Flow 5), pacote com 2, SCY965/02", "categoria": "Alimentação", "quantidade_desejada": 1, "preco_atual": 38.21, "preco_anterior": None},
    {"nome": "Mamadeira Philips Avent Pétala 3.0, Bico de Fluxo Médio, 260ml", "categoria": "Alimentação", "quantidade_desejada": 1, "preco_atual": 59.91, "preco_anterior": None},
    {"nome": "Mamadeiras Philips Avent, 125ml e 260ml, Kit com 2 Unidades", "categoria": "Alimentação", "quantidade_desejada": 1, "preco_atual": 113.00, "preco_anterior": None},
    {"nome": "Paninho De Boca Papi Textil Soft", "categoria": "Alimentação", "quantidade_desejada": 1, "preco_atual": 44.50, "preco_anterior": None},

    # ---------- Saúde e cuidados com o bebê (11 produtos / 24 unidades) ----------
    {"nome": "Rosquinhas Para Amamentação - kit 4 Un", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 29.80, "preco_anterior": None},
    {"nome": "Buba Escova E Pente Baby Cerdas Naturais Branco", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 23.00, "preco_anterior": 45.90},
    {"nome": "Aspirador Nasal Likluc Aspirar Baby", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 54.77, "preco_anterior": 89.90},
    {"nome": "Buba Kit Cuidados Baby Cinza Tamanho Único", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 27.58, "preco_anterior": 47.90},
    {"nome": "Hastes Flexíveis Clingo - Branco", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 5, "preco_atual": 9.90, "preco_anterior": None},
    {"nome": "2 TERMO FRIENDS - ADESIVO MEDIDOR DE TEMPERATURA - BABYDEAS", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 42.65, "preco_anterior": 44.90},
    {"nome": "Termômetro de Ponta Flexível G-Tech Fun Sapo", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 26.98, "preco_anterior": 38.19},
    {"nome": "Termômetro para Banheira Adoleta, Verde Bebê", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 1, "preco_atual": 36.52, "preco_anterior": None},
    {"nome": "Likluc Pikluc Aparelho Para Alivio Da Dor Na Hora Da Injeção Verde Tamanho Único", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 2, "preco_atual": 21.00, "preco_anterior": 29.90},
    {"nome": "Likluc Xô Febre - compressas refrescantes para alivio da febre, Azul Oceano, Tamanho Único", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 5, "preco_atual": 31.28, "preco_anterior": 42.90},
    {"nome": "Abs. P/Seios Ultimate Protection Lansinoh - Leve 3 Pague 2", "categoria": "Saúde e cuidados com o bebê", "quantidade_desejada": 5, "preco_atual": 74.95, "preco_anterior": 78.90},

    # ---------- Quarto de bebê (8 produtos / 8 unidades) ----------
    {"nome": "Papi Textil Lençol Papi C/Elástico Tam Padrão Liso 1,30M X 60Cm X 10Cm Contem 01 Un", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 20.38, "preco_anterior": None},
    {"nome": "Lençol Avulso Papi Textil C/Elástico Liso", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 24.28, "preco_anterior": 26.59},
    {"nome": "Lençol Papi C/Elástico Liso", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 20.38, "preco_anterior": None},
    {"nome": "Naninha Para Bebê Paninho Bichinho com Prendedor de Chupeta (Ovelhinha)", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 18.90, "preco_anterior": None},
    {"nome": "Buba Naninha Ovelhinha", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 48.99, "preco_anterior": 75.90},
    {"nome": "Mantinha Buba, Ovelhinha, Azul", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 54.99, "preco_anterior": 64.90},
    {"nome": "Cobertor Donna Laço Bebê Plush com Sherpa Hearts (Branco)", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 136.70, "preco_anterior": 143.90},
    {"nome": "Cueiro Papi Flanelado Estampado 100Cm X 80Cm, Contém 03 Un", "categoria": "Quarto de bebê", "quantidade_desejada": 1, "preco_atual": 30.40, "preco_anterior": 46.86},

    # ---------- Brinquedos, livros e presentes (13 produtos / 13 unidades) ----------
    {"nome": "Mordedor Sensorial em Silicone, Tiny Love, Estrela, Magical Skies", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 42.18, "preco_anterior": None},
    {"nome": "Tiny Love, Brinquedo Chocalho Koala, Boho Chic", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": None, "preco_anterior": None},  # "Ver opções de compra" na lista
    {"nome": "Tiny Love, Chocalho mordedor Teether Rattle, Leonardo", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 33.41, "preco_anterior": 49.90},
    {"nome": "Escolinha Baby Montessori - Contrastes! Grande ou Pequeno?", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 19.85, "preco_anterior": 29.90},
    {"nome": "Olá, Bebê! Um livrinho Contraste de Banho: Meus Sentimentos", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 11.80, "preco_anterior": 16.90},
    {"nome": "Olá, Bebê! Um livrinho Contraste de Banho: Meus Momentos", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 11.21, "preco_anterior": 16.90},
    {"nome": "Olá, Bebê! Um livrinho Contraste de Banho: Primeiras Palavras", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 11.21, "preco_anterior": 16.90},
    {"nome": "Olá, Bebê! Um livrinho Contraste de Banho: Números", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 11.21, "preco_anterior": 16.90},
    {"nome": "Buba Mordedor Coala Colorido", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 24.46, "preco_anterior": None},
    {"nome": "Brinquedo de Banho BUBA, Pescaria de Tubarão, Multicor", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 37.89, "preco_anterior": 77.90},
    {"nome": "Buba Livrinho De Banho - Conhecendo O Fundo Do Mar Colorido", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 22.05, "preco_anterior": 27.90},
    {"nome": "Buba Livrinho De Banho - Conhecendo As Frutas Colorido", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 23.99, "preco_anterior": 27.90},
    {"nome": "Buba Livrinho De Banho Animais Da Floresta Colorido", "categoria": "Brinquedos, livros e presentes", "quantidade_desejada": 1, "preco_atual": 23.99, "preco_anterior": None},
]
