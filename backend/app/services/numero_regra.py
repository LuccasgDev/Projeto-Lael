"""
REGRA CENTRAL E FIXA do Chá Rifa do Lael: cada número da rifa representa
um TAMANHO DE FRALDA e um MIMO correspondente.

Distribuição fixa (nunca depende de digitação do usuário nem de configurações
editáveis de quantidade):

    01–05  → RN  + Sabonete líquido para recém-nascido (mimo fixo)
    06–35  → P   + Pomada antiassadura (mimo fixo)
    36–65  → M   + mimo à escolha do participante
    66–100 → G   + Lenços umedecidos (mimo fixo)

Frontend e backend DEVEM usar esta mesma classificação — nunca duplicar
as faixas em outro lugar.
"""
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.models import Mimo, ProdutoPrincipal

# Faixas fixas: (inicio, fim, tamanho da fralda)
FAIXAS_NUMEROS = [
    {"inicio": 1, "fim": 5, "tamanho": "RN"},
    {"inicio": 6, "fim": 35, "tamanho": "P"},
    {"inicio": 36, "fim": 65, "tamanho": "M"},
    {"inicio": 66, "fim": 100, "tamanho": "G"},
]

TOTAL_NUMEROS_RIFA = 100

# Mimo fixo padrão por tamanho (RN/P/G). O valor é o NOME do mimo cadastrado;
# o admin pode ajustar via configurações (mimo_fixo_rn / mimo_fixo_p / mimo_fixo_g).
MIMO_FIXO_PADRAO = {
    "RN": "Sabonete Líquido Johnson's Baby Recém-Nascidos, 200ml",
    "P": "Bepantol Baby Pomada Assadura Bebe, Hipoalergênica, 30g",
    "G": "Lenços Umedecidos Pampers Aroma de Aloe Vera 192 Unidades",
}

# Chaves de configuração que permitem ao admin apontar outro mimo cadastrado
CONFIG_MIMO_FIXO = {
    "RN": "mimo_fixo_rn",
    "P": "mimo_fixo_p",
    "G": "mimo_fixo_g",
}


def classificar_numero(numero: int) -> dict:
    """
    Classificação fixa de um número da rifa.

    Retorna:
        tamanho: 'RN' | 'P' | 'M' | 'G'
        mimo_modo: 'fixo' (mimo definido pela regra) | 'escolha' (participante escolhe)
        mimo_nome_padrao: nome canônico do mimo fixo (somente quando modo='fixo')
    """
    if not isinstance(numero, int) or numero < 1 or numero > TOTAL_NUMEROS_RIFA:
        raise ValueError(f"Número fora da faixa válida da rifa: {numero}")

    for faixa in FAIXAS_NUMEROS:
        if faixa["inicio"] <= numero <= faixa["fim"]:
            tamanho = faixa["tamanho"]
            if tamanho == "M":
                return {"tamanho": tamanho, "mimo_modo": "escolha", "mimo_nome_padrao": None}
            return {
                "tamanho": tamanho,
                "mimo_modo": "fixo",
                "mimo_nome_padrao": MIMO_FIXO_PADRAO[tamanho],
            }
    raise ValueError(f"Número sem faixa definida: {numero}")


def tamanho_para_numero(numero: int) -> str:
    """Atalho: retorna apenas o tamanho da fralda do número."""
    return classificar_numero(numero)["tamanho"]


def faixa_para_numero(numero: int) -> dict:
    """Retorna a faixa (inicio/fim/tamanho) à qual o número pertence."""
    classificar_numero(numero)  # valida faixa
    for faixa in FAIXAS_NUMEROS:
        if faixa["inicio"] <= numero <= faixa["fim"]:
            return dict(faixa)
    raise ValueError(f"Número sem faixa definida: {numero}")


def tamanho_para_faixa(tamanho: str) -> dict:
    """Retorna a faixa fixa de um tamanho de fralda."""
    for faixa in FAIXAS_NUMEROS:
        if faixa["tamanho"] == tamanho:
            return dict(faixa)
    raise ValueError(f"Tamanho de fralda sem faixa definida: {tamanho}")


def _get_config_value(db: Session, key: str, default: str = "") -> str:
    from backend.app.models.models import Configuracao
    cfg = db.query(Configuracao).filter(Configuracao.chave == key).first()
    return cfg.valor if cfg and cfg.valor else default


def nome_mimo_fixo(db: Session, tamanho: str) -> Optional[str]:
    """
    Nome configurado do mimo fixo do tamanho (config mimo_fixo_*),
    com fallback para o padrão da regra.
    """
    chave = CONFIG_MIMO_FIXO.get(tamanho)
    if not chave:
        return None
    return _get_config_value(db, chave, MIMO_FIXO_PADRAO.get(tamanho, "")) or None


def resolver_mimo_fixo(db: Session, tamanho: str) -> Optional[Mimo]:
    """
    Resolve o Mimo cadastrado correspondente ao mimo fixo do tamanho.
    Casa por nome exato (case-insensitive); se não houver, tenta correspondência
    parcial. Retorna None se nenhum mimo cadastrado corresponder.
    """
    nome = nome_mimo_fixo(db, tamanho)
    if not nome:
        return None

    alvo = nome.strip().lower()
    mimos = db.query(Mimo).filter(Mimo.ativo == True).all()  # noqa: E712

    for m in mimos:
        if (m.nome or "").strip().lower() == alvo:
            return m
    # Fallback: nome configurado contém o nome do mimo ou vice-versa
    for m in mimos:
        nome_mimo = (m.nome or "").strip().lower()
        if nome_mimo and (nome_mimo in alvo or alvo in nome_mimo):
            return m
    return None


def fralda_para_tamanho(db: Session, tamanho: str) -> Optional[ProdutoPrincipal]:
    """
    Retorna a fralda ativa (categoria 'Fraldas') cujo campo `tamanho`
    corresponde ao tamanho da faixa fixa.
    """
    return (
        db.query(ProdutoPrincipal)
        .filter(
            ProdutoPrincipal.ativo == True,  # noqa: E712
            ProdutoPrincipal.categoria == "Fraldas",
            ProdutoPrincipal.tamanho == tamanho,
        )
        .order_by(ProdutoPrincipal.ordem_exibicao.asc(), ProdutoPrincipal.id.asc())
        .first()
    )
