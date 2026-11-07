"""
Sanidade dos dados REAIS semeados (briefing v2, seção 3):
- 58 mimos em exatamente 7 categorias, totalizando 113 unidades desejadas.
- Nenhum produto fictício: nomes/categories vêm da lista copiada do Lucas.
- Fraldas: 5 itens, 100 unidades, faixas contíguas RN/RN+/P/M/G.
"""
from backend.app.data.mimos_reais import SEED_MIMOS_REAIS
from backend.app.data.seed_data import SEED_FRALDAS_REAIS

CATEGORIAS_ESPERADAS = {
    "Roupas de bebê": 3,
    "Produtos de banho": 10,
    "Troca de fraldas": 9,
    "Alimentação": 4,
    "Saúde e cuidados com o bebê": 11,
    "Quarto de bebê": 8,
    "Brinquedos, livros e presentes": 13,
}


def test_mimos_reais_58_produtos_113_unidades_7_categorias():
    assert len(SEED_MIMOS_REAIS) == 58
    assert sum(m["quantidade_desejada"] for m in SEED_MIMOS_REAIS) == 113

    por_categoria = {}
    for m in SEED_MIMOS_REAIS:
        por_categoria[m["categoria"]] = por_categoria.get(m["categoria"], 0) + 1
    assert por_categoria == CATEGORIAS_ESPERADAS


def test_mimos_reais_sem_duplicados_e_com_nome():
    nomes = [m["nome"].strip() for m in SEED_MIMOS_REAIS]
    assert len(set(nomes)) == len(nomes)
    assert all(nomes)
    for m in SEED_MIMOS_REAIS:
        assert m["quantidade_desejada"] >= 1
        # preço nulo é permitido ("Ver opções"), mas nunca negativo/zero disfarçado
        assert m["preco_atual"] is None or m["preco_atual"] > 0


def test_fraldas_reais_5_itens_100_unidades():
    assert len(SEED_FRALDAS_REAIS) == 5
    assert sum(f["quantidade_desejada"] for f in SEED_FRALDAS_REAIS) == 100
    assert all(f["asin"] for f in SEED_FRALDAS_REAIS)
    # M é o único sem preço na lista ("Ver opções de compra")
    sem_preco = [f["tamanho"] for f in SEED_FRALDAS_REAIS if f["preco_atual"] is None]
    assert sem_preco == ["M"]
