"""
Centralized site settings schema for the Chá Rifa do Lael CMS.

Settings are stored in the existing `configuracoes` table (chave/valor) with
keys prefixed by `site.`. This module defines:

- The schema (categories, fields, types, defaults, public visibility).
- Typed getters used by backend services.
- Validation + bulk update used by the admin API.

Infrastructure secrets (SECRET_KEY, DATABASE_URL, SCAVIO_API_KEY, tunnel
token, etc.) are intentionally NOT part of this schema — they stay in env.
"""

import re
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.app.models.models import Configuracao

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
# Each field: key, label, type, category, default, public (safe for anon),
# optional options (for select) and help text.

FIELD_TYPES = ("text", "textarea", "number", "integer", "boolean", "select", "color", "url")

SETTINGS_SCHEMA: List[Dict[str, Any]] = [
    # ---------------- GERAL / EVENTO ----------------
    {"key": "site.evento.nome", "label": "Nome do evento", "type": "text", "category": "evento", "default": "Chá Rifa do Lael", "public": True},
    {"key": "site.evento.bebe", "label": "Nome do bebê", "type": "text", "category": "evento", "default": "Lael", "public": True},
    {"key": "site.evento.titulo", "label": "Título principal (hero)", "type": "text", "category": "evento", "default": "Com o coração transbordando de amor, estamos preparando a chegada do nosso tão esperado menininho.", "public": True},
    {"key": "site.evento.subtitulo", "label": "Subtítulo", "type": "textarea", "category": "evento", "default": "Escolha seu número da sorte, presenteie o Lael e comemore essa bênção com a gente!", "public": True},
    {"key": "site.evento.data", "label": "Data do chá", "type": "text", "category": "evento", "default": "Março de 2027", "public": True},
    {"key": "site.evento.horario", "label": "Horário", "type": "text", "category": "evento", "default": "", "public": True},
    {"key": "site.evento.cidade", "label": "Cidade", "type": "text", "category": "evento", "default": "Fortaleza", "public": True},
    {"key": "site.evento.estado", "label": "Estado (UF)", "type": "text", "category": "evento", "default": "CE", "public": True},
    {"key": "site.evento.pais", "label": "País", "type": "text", "category": "evento", "default": "Brasil", "public": True},
    {"key": "site.evento.local", "label": "Local do evento", "type": "text", "category": "evento", "default": "", "public": True},
    {"key": "site.evento.responsaveis", "label": "Nomes dos responsáveis", "type": "text", "category": "evento", "default": "Talia Vitória & Lucas Gabriel", "public": True},
    {"key": "site.evento.mensagem_boas_vindas", "label": "Mensagem de boas-vindas", "type": "textarea", "category": "evento", "default": "Sejam muito bem-vindos ao Chá Rifa do Lael!", "public": True},
    {"key": "site.evento.mensagem_encerramento", "label": "Mensagem de encerramento", "type": "textarea", "category": "evento", "default": "Agradecemos de coração a cada um de vocês por fazer parte da história do nosso filho. Sua presença, oração e carinho são o nosso maior presente!", "public": True},
    {"key": "site.evento.rifa_ativa", "label": "Rifa ativa (aceitando participantes)", "type": "boolean", "category": "evento", "default": True, "public": True},
    {"key": "site.evento.exibir_dados_evento", "label": "Exibir dados do evento no site", "type": "boolean", "category": "evento", "default": True, "public": True},

    # ---------------- RIFA ----------------
    {"key": "site.rifa.valor_numero", "label": "Valor por número (R$)", "type": "text", "category": "rifa", "default": "", "public": True, "help": "Deixe vazio se a rifa for por presente/mimo sem cobrança direta."},
    {"key": "site.rifa.mensagem_regras", "label": "Mensagem de regras", "type": "textarea", "category": "rifa", "default": "Cada número corresponde a um tamanho de fralda (RN, P, M ou G) e já inclui um mimo especial correspondente. Nos números de tamanho M, você poderá escolher o mimo que desejar.", "public": True},
    {"key": "site.rifa.mensagem_instrucoes", "label": "Mensagem de instruções", "type": "textarea", "category": "rifa", "default": "É muito fácil e rápido garantir seu número e demonstrar seu carinho pelo Lael.", "public": True},
    {"key": "site.rifa.exibir_disponiveis", "label": "Destacar números disponíveis", "type": "boolean", "category": "rifa", "default": True, "public": True},
    {"key": "site.rifa.aviso_confirmacao", "label": "Aviso de confirmação", "type": "textarea", "category": "rifa", "default": "Para confirmar seu número, será necessário comprovar a aquisição do presente e do mimo escolhidos.", "public": True},

    # ---------------- PRÊMIO ----------------
    {"key": "site.premio.ativo", "label": "Prêmio ativado", "type": "boolean", "category": "premio", "default": True, "public": True},
    {"key": "site.premio.valor", "label": "Valor do prêmio (ex: R$ 250,00)", "type": "text", "category": "premio", "default": "R$ 250,00", "public": True},
    {"key": "site.premio.titulo", "label": "Título do prêmio", "type": "text", "category": "premio", "default": "Concorra a um prêmio especial!", "public": True},
    {"key": "site.premio.texto_destaque", "label": "Texto de destaque", "type": "text", "category": "premio", "default": "CONCORRA A", "public": True},
    {"key": "site.premio.descricao", "label": "Descrição do prêmio", "type": "textarea", "category": "premio", "default": "Participe do Chá Rifa do Lael e concorra a um prêmio em dinheiro!", "public": True},
    {"key": "site.premio.texto_antes_valor", "label": "Texto antes do valor", "type": "text", "category": "premio", "default": "Prêmio principal:", "public": True},
    {"key": "site.premio.regras", "label": "Regras do prêmio", "type": "textarea", "category": "premio", "default": "", "public": True},
    {"key": "site.premio.data_sorteio", "label": "Data do sorteio", "type": "text", "category": "premio", "default": "", "public": True},
    {"key": "site.premio.exibir_home", "label": "Exibir prêmio na página inicial", "type": "boolean", "category": "premio", "default": True, "public": True},
    {"key": "site.premio.exibir_popup", "label": "Exibir prêmio no popup", "type": "boolean", "category": "premio", "default": True, "public": True},
    {"key": "site.premio.exibir_banner_home", "label": "Exibir banner do prêmio na home", "type": "boolean", "category": "premio", "default": True, "public": True},
    {"key": "site.premio.mostrar_valor", "label": "Mostrar o valor do prêmio", "type": "boolean", "category": "premio", "default": True, "public": True},

    # ---------------- POPUP ----------------
    {"key": "site.popup.ativo", "label": "Popup ativado", "type": "boolean", "category": "popup", "default": True, "public": True},
    {"key": "site.popup.frequencia", "label": "Frequência de exibição", "type": "select", "category": "popup", "default": "sessao", "public": True, "options": ["sessao", "uma_vez", "sempre"]},
    {"key": "site.popup.titulo", "label": "Título", "type": "text", "category": "popup", "default": "CHÁ RIFA DO LAEL", "public": True},
    {"key": "site.popup.subtitulo", "label": "Subtítulo", "type": "text", "category": "popup", "default": "CONCORRA A", "public": True},
    {"key": "site.popup.valor_destaque", "label": "Valor em destaque", "type": "text", "category": "popup", "default": "R$ 250,00", "public": True},
    {"key": "site.popup.texto", "label": "Texto descritivo", "type": "textarea", "category": "popup", "default": "Escolha seu número, presenteie o Lael e concorra a um prêmio especial!", "public": True},
    {"key": "site.popup.texto_botao", "label": "Texto do botão principal", "type": "text", "category": "popup", "default": "QUERO PARTICIPAR", "public": True},
    {"key": "site.popup.texto_botao_secundario", "label": "Texto do botão secundário", "type": "text", "category": "popup", "default": "VER OS PRESENTES", "public": True},
    {"key": "site.popup.destino_botao", "label": "Destino do botão principal (seletor/âncora)", "type": "text", "category": "popup", "default": "#numeros", "public": True},
    {"key": "site.popup.destino_botao_secundario", "label": "Destino do botão secundário", "type": "text", "category": "popup", "default": "#regras", "public": True},
    {"key": "site.popup.exibir_botao_secundario", "label": "Exibir botão secundário", "type": "boolean", "category": "popup", "default": True, "public": True},
    {"key": "site.popup.exibir_fechar", "label": "Exibir botão de fechar", "type": "boolean", "category": "popup", "default": True, "public": True},
    {"key": "site.popup.atraso_segundos", "label": "Atraso para aparecer (segundos)", "type": "integer", "category": "popup", "default": 0, "public": True},
    {"key": "site.popup.confetes", "label": "Exibir animação de confetes", "type": "boolean", "category": "popup", "default": True, "public": True},
    {"key": "site.popup.cor_fundo", "label": "Cor de fundo do popup", "type": "color", "category": "popup", "default": "#FFF8F0", "public": True},
    {"key": "site.popup.cor_texto", "label": "Cor do texto", "type": "color", "category": "popup", "default": "#29343A", "public": True},
    {"key": "site.popup.cor_botao", "label": "Cor do botão principal", "type": "color", "category": "popup", "default": "#42677D", "public": True},
    {"key": "site.popup.mostrar_desktop", "label": "Mostrar em desktop", "type": "boolean", "category": "popup", "default": True, "public": True},
    {"key": "site.popup.mostrar_mobile", "label": "Mostrar em mobile", "type": "boolean", "category": "popup", "default": True, "public": True},

    # ---------------- RESERVA ----------------
    {"key": "site.reserva.ativa", "label": "Reservas ativas", "type": "boolean", "category": "reserva", "default": True, "public": True},
    {"key": "site.reserva.prazo_padrao_horas", "label": "Prazo padrão da reserva (horas)", "type": "integer", "category": "reserva", "default": 72, "public": True, "help": "Vale para novas reservas. Reservas existentes mantêm o prazo original."},
    {"key": "site.reserva.permitir_renovacao", "label": "Permitir renovação", "type": "boolean", "category": "reserva", "default": True, "public": True},
    {"key": "site.reserva.permitir_cancelamento", "label": "Permitir cancelamento pelo participante", "type": "boolean", "category": "reserva", "default": False, "public": False},
    {"key": "site.reserva.texto_expiracao", "label": "Texto de aviso de expiração", "type": "textarea", "category": "reserva", "default": "Sua reserva expira em {horas} horas. Confirme enviando o comprovante pelo WhatsApp.", "public": True},
    {"key": "site.reserva.texto_concluida", "label": "Texto de reserva concluída", "type": "textarea", "category": "reserva", "default": "Reserva criada com sucesso! Envie o comprovante para confirmar seu número.", "public": True},
    {"key": "site.reserva.texto_expirada", "label": "Texto de reserva expirada", "type": "textarea", "category": "reserva", "default": "Este número já não está mais reservado. Escolha outro número.", "public": True},
    {"key": "site.reserva.alerta_horas", "label": "Horas antes do vencimento para exibir alerta", "type": "integer", "category": "reserva", "default": 24, "public": True},

    # ---------------- PRODUTOS / MIMOS ----------------
    {"key": "site.produtos.mostrar_imagens", "label": "Mostrar imagens dos produtos", "type": "boolean", "category": "produtos", "default": True, "public": True},
    {"key": "site.produtos.mostrar_precos", "label": "Mostrar preços", "type": "boolean", "category": "produtos", "default": True, "public": True},
    {"key": "site.produtos.mostrar_descricao", "label": "Mostrar descrições", "type": "boolean", "category": "produtos", "default": True, "public": True},
    {"key": "site.produtos.mostrar_links_amazon", "label": "Mostrar links da Amazon", "type": "boolean", "category": "produtos", "default": True, "public": True},
    {"key": "site.produtos.mensagem_vazio", "label": "Mensagem quando não houver produtos", "type": "text", "category": "produtos", "default": "Os produtos do enxoval serão anunciados em breve.", "public": True},
    {"key": "site.produtos.modo_preco", "label": "Preço exibido", "type": "select", "category": "produtos", "default": "auto", "public": True, "options": ["auto", "manual", "oculto"], "help": "auto = usa o preço registrado (sincronizado ou manual)."},

    # ---------------- APARÊNCIA ----------------
    {"key": "site.aparencia.cor_primaria", "label": "Cor primária (azul)", "type": "color", "category": "aparencia", "default": "#42677D", "public": True},
    {"key": "site.aparencia.cor_fundo", "label": "Cor de fundo (creme)", "type": "color", "category": "aparencia", "default": "#FFF8F0", "public": True},
    {"key": "site.aparencia.cor_destaque", "label": "Cor de destaque (laranja)", "type": "color", "category": "aparencia", "default": "#E69B78", "public": True},
    {"key": "site.aparencia.cor_texto", "label": "Cor dos textos", "type": "color", "category": "aparencia", "default": "#29343A", "public": True},
    {"key": "site.aparencia.cor_verde", "label": "Cor verde (sucesso/disponível)", "type": "color", "category": "aparencia", "default": "#94A98C", "public": True},
    {"key": "site.aparencia.logo_url", "label": "URL da logo (opcional)", "type": "url", "category": "aparencia", "default": "", "public": True},
    {"key": "site.aparencia.arredondamento", "label": "Arredondamento dos cards (px)", "type": "integer", "category": "aparencia", "default": 16, "public": True},
    {"key": "site.aparencia.ativo", "label": "Personalização visual ativa", "type": "boolean", "category": "aparencia", "default": True, "public": True},

    # ---------------- TEXTOS / CONTEÚDO ----------------
    {"key": "site.textos.como_funciona_titulo", "label": "Título 'Como funciona'", "type": "text", "category": "textos", "default": "Como Funciona a Participação", "public": True},
    {"key": "site.textos.produtos_titulo", "label": "Título da seção de produtos", "type": "text", "category": "textos", "default": "O Enxoval do Lael", "public": True},
    {"key": "site.textos.regras_titulo", "label": "Título da seção de regras", "type": "text", "category": "textos", "default": "Regras da Rifa", "public": True},
    {"key": "site.textos.botao_participar", "label": "Texto do botão 'Escolher meu número'", "type": "text", "category": "textos", "default": "Escolher meu número", "public": True},
    {"key": "site.textos.aviso_importante", "label": "Texto do aviso importante", "type": "textarea", "category": "textos", "default": "Para confirmar seu número, será necessário comprovar a aquisição do presente e do mimo escolhidos.", "public": True},

    # ---------------- CONTATO ----------------
    {"key": "site.contato.whatsapp", "label": "WhatsApp (DDI+DDD+número)", "type": "text", "category": "contato", "default": "", "public": True, "help": "Sobrescreve o whatsapp_casal quando preenchido."},
    {"key": "site.contato.mensagem_whatsapp", "label": "Mensagem padrão do WhatsApp", "type": "textarea", "category": "contato", "default": "Olá! Vim pelo site do Chá Rifa do Lael e gostaria de mais informações.", "public": True},
    {"key": "site.contato.instagram", "label": "Instagram (URL ou @usuário)", "type": "text", "category": "contato", "default": "", "public": True},
    {"key": "site.contato.facebook", "label": "Facebook (URL)", "type": "text", "category": "contato", "default": "", "public": True},
    {"key": "site.contato.tiktok", "label": "TikTok (URL)", "type": "text", "category": "contato", "default": "", "public": True},
    {"key": "site.contato.email", "label": "E-mail de contato", "type": "text", "category": "contato", "default": "", "public": True},
    {"key": "site.contato.exibir_redes", "label": "Exibir redes sociais no rodapé", "type": "boolean", "category": "contato", "default": True, "public": True},

    # ---------------- PIX / PAGAMENTO ----------------
    {"key": "site.pix.ativo", "label": "Pix ativado", "type": "boolean", "category": "pix", "default": True, "public": True},
    {"key": "site.pix.chave", "label": "Chave Pix", "type": "text", "category": "pix", "default": "", "public": False, "help": "Use os campos legados 'chave_pix' se preferir — este campo é público se ativado."},
    {"key": "site.pix.beneficiario", "label": "Nome do beneficiário", "type": "text", "category": "pix", "default": "Talia Vitória / Lucas Gabriel", "public": True},
    {"key": "site.pix.tipo_chave", "label": "Tipo da chave", "type": "select", "category": "pix", "default": "E-mail", "public": True, "options": ["E-mail", "CPF", "CNPJ", "Telefone", "Aleatória"]},
    {"key": "site.pix.instrucao", "label": "Texto de instruções do Pix", "type": "textarea", "category": "pix", "default": "Após o pagamento, envie o comprovante pelo WhatsApp com seu nome e número escolhido.", "public": True},
    {"key": "site.pix.mensagem_apos_envio", "label": "Mensagem após envio do comprovante", "type": "textarea", "category": "pix", "default": "Comprovante recebido! Em breve confirmaremos seu número. Obrigado!", "public": True},
    {"key": "site.pix.prazo_horas", "label": "Prazo para pagamento/confirmação (horas)", "type": "integer", "category": "pix", "default": 72, "public": True},

    # ---------------- SORTEIO ----------------
    {"key": "site.sorteio.ativo", "label": "Divulgação do sorteio ativa", "type": "boolean", "category": "sorteio", "default": True, "public": True},
    {"key": "site.sorteio.data", "label": "Data do sorteio", "type": "text", "category": "sorteio", "default": "", "public": True},
    {"key": "site.sorteio.horario", "label": "Horário do sorteio", "type": "text", "category": "sorteio", "default": "", "public": True},
    {"key": "site.sorteio.texto", "label": "Texto explicativo", "type": "textarea", "category": "sorteio", "default": "O sorteio do prêmio será realizado entre os participantes confirmados.", "public": True},
    {"key": "site.sorteio.exibir_data", "label": "Exibir data do sorteio", "type": "boolean", "category": "sorteio", "default": True, "public": True},
    {"key": "site.sorteio.mensagem_antes", "label": "Mensagem antes do sorteio", "type": "textarea", "category": "sorteio", "default": "", "public": True},
    {"key": "site.sorteio.mensagem_depois", "label": "Mensagem depois do sorteio", "type": "textarea", "category": "sorteio", "default": "", "public": True},

    # ---------------- SEO ----------------
    {"key": "site.seo.titulo_pagina", "label": "Título da página", "type": "text", "category": "seo", "default": "Chá de Bebê do Lael • Março de 2027 • Fortaleza/CE", "public": True},
    {"key": "site.seo.descricao", "label": "Meta description", "type": "textarea", "category": "seo", "default": "Concorra a um prêmio especial no Chá Rifa do Lael! Escolha seu número da sorte e presenteie o Lael.", "public": True},
    {"key": "site.seo.imagem", "label": "Imagem de compartilhamento (URL)", "type": "url", "category": "seo", "default": "", "public": True},
    {"key": "site.seo.titulo_whatsapp", "label": "Título ao compartilhar no WhatsApp", "type": "text", "category": "seo", "default": "", "public": True},

    # ---------------- SISTEMA ----------------
    {"key": "site.sistema.modo_manutencao", "label": "Modo de manutenção", "type": "boolean", "category": "sistema", "default": False, "public": True},
    {"key": "site.sistema.mensagem_manutencao", "label": "Mensagem de manutenção", "type": "textarea", "category": "sistema", "default": "Estamos em manutenção. Voltamos em breve!", "public": True},
]

SCHEMA_BY_KEY: Dict[str, Dict[str, Any]] = {f["key"]: f for f in SETTINGS_SCHEMA}
SCHEMA_BY_CATEGORY: Dict[str, List[Dict[str, Any]]] = {}
for _f in SETTINGS_SCHEMA:
    SCHEMA_BY_CATEGORY.setdefault(_f["category"], []).append(_f)

CATEGORY_LABELS = {
    "evento": "Geral / Evento",
    "rifa": "Rifa",
    "premio": "Prêmio",
    "popup": "Popup",
    "reserva": "Reservas",
    "produtos": "Produtos e Mimos",
    "aparencia": "Aparência",
    "textos": "Textos e Conteúdo",
    "contato": "Contato",
    "pix": "Pix / Pagamento",
    "sorteio": "Sorteio",
    "seo": "SEO",
    "sistema": "Sistema",
}

# Legacy keys that remain authoritative for some backend behavior — the site
# settings layer falls back to them (and writes-through when needed).
LEGACY_ALIASES = {
    "site.evento.nome": "nome_evento",
    "site.evento.data": "data_evento",
    "site.contato.whatsapp": "whatsapp_casal",
    "site.pix.chave": "chave_pix",
    "site.pix.beneficiario": "titular_pix",
    "site.pix.tipo_chave": "tipo_chave_pix",
    "site.pix.instrucao": "banco_pix",
    "site.reserva.prazo_padrao_horas": "prazo_padrao_horas",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce(field: Dict[str, Any], raw: Any) -> Any:
    """Coerce a raw value to the field's declared type. Raises ValueError."""
    t = field["type"]
    if t == "boolean":
        if isinstance(raw, bool):
            return raw
        s = str(raw).strip().lower()
        if s in ("true", "1", "sim", "yes", "on"):
            return True
        if s in ("false", "0", "nao", "não", "no", "off", ""):
            return False
        raise ValueError(f"{field['key']}: valor booleano inválido '{raw}'")
    if t in ("integer", "number"):
        try:
            v = float(str(raw).strip())
        except (TypeError, ValueError):
            raise ValueError(f"{field['key']}: número inválido '{raw}'")
        if t == "integer":
            if not v.is_integer():
                raise ValueError(f"{field['key']}: deve ser inteiro")
            v = int(v)
        return v
    s = "" if raw is None else str(raw).strip()
    if t == "color" and s:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", s):
            raise ValueError(f"{field['key']}: cor deve estar no formato #RRGGBB")
        return s.lower()
    if t == "url" and s and not re.match(r"^(https?://|/|#)", s):
        raise ValueError(f"{field['key']}: URL inválida '{s}'")
    if t == "select" and field.get("options") and s not in field["options"]:
        raise ValueError(f"{field['key']}: opção inválida '{s}'")
    max_len = 4000 if t == "textarea" else 500
    if len(s) > max_len:
        raise ValueError(f"{field['key']}: excede {max_len} caracteres")
    return s


def _serialize(field: Dict[str, Any], value: Any) -> str:
    if field["type"] == "boolean":
        return "true" if bool(value) else "false"
    if value is None:
        return ""
    return str(value)


def get_setting(db: Session, key: str, default: Any = None) -> Any:
    """Read a site setting with schema coercion + fallback chain."""
    field = SCHEMA_BY_KEY.get(key)
    cfg = db.query(Configuracao).filter(Configuracao.chave == key).first()
    raw = cfg.valor if cfg else None
    if raw is None and field is not None:
        raw = field["default"]
    # Fallback to legacy alias for a few keys (keeps existing admin UI working)
    if (raw is None or raw == "") and key in LEGACY_ALIASES:
        legacy = db.query(Configuracao).filter(Configuracao.chave == LEGACY_ALIASES[key]).first()
        raw = legacy.valor if legacy else (field["default"] if field else default)
    if field is None:
        return raw if raw is not None else default
    try:
        return _coerce(field, raw)
    except ValueError:
        return field["default"]


def get_setting_str(db: Session, key: str, default: str = "") -> str:
    v = get_setting(db, key, default)
    return "" if v is None else str(v)


def get_public_settings(db: Session) -> Dict[str, Any]:
    """Return only fields marked public, grouped by category."""
    result: Dict[str, Any] = {}
    for cat, fields in SCHEMA_BY_CATEGORY.items():
        cat_data = {}
        for f in fields:
            if f.get("public"):
                key_suffix = f["key"].rsplit(".", 1)[-1]  # last segment only
                cat_data[key_suffix] = get_setting(db, f["key"])
        if cat_data:
            result[cat] = cat_data
    return result


def get_admin_settings(db: Session) -> Dict[str, Any]:
    """Return full schema with current values + metadata (admin only)."""
    result = {"categories": [], "fields": {}}
    for cat, fields in SCHEMA_BY_CATEGORY.items():
        result["categories"].append({"id": cat, "label": CATEGORY_LABELS.get(cat, cat)})
        for f in fields:
            entry = {k: f[k] for k in ("key", "label", "type", "category", "public") if k in f}
            if "options" in f:
                entry["options"] = f["options"]
            if "help" in f:
                entry["help"] = f["help"]
            entry["value"] = get_setting(db, f["key"])
            result["fields"][f["key"]] = entry
    return result


def update_settings(db: Session, updates: Dict[str, Any], admin_nome: str = "") -> Dict[str, Any]:
    """
    Validate + persist site settings. Returns {updated, errors}.
    Writes through to legacy alias keys when they exist in configuracoes so
    the legacy public /config endpoint stays consistent.
    """
    updated, errors = [], []
    for key, raw in updates.items():
        field = SCHEMA_BY_KEY.get(key)
        if field is None:
            errors.append({"key": key, "error": "Configuração desconhecida"})
            continue
        try:
            value = _coerce(field, raw)
        except ValueError as e:
            errors.append({"key": key, "error": str(e)})
            continue

        cfg = db.query(Configuracao).filter(Configuracao.chave == key).first()
        if cfg:
            cfg.valor = _serialize(field, value)
            cfg.atualizado_em = _utcnow()
        else:
            db.add(Configuracao(chave=key, valor=_serialize(field, value), atualizado_em=_utcnow()))

        # Write-through to legacy aliases so /public/config stays in sync
        legacy = LEGACY_ALIASES.get(key)
        if legacy:
            lcfg = db.query(Configuracao).filter(Configuracao.chave == legacy).first()
            sval = _serialize(field, value)
            if lcfg:
                lcfg.valor = sval
                lcfg.atualizado_em = _utcnow()
            else:
                db.add(Configuracao(chave=legacy, valor=sval, atualizado_em=_utcnow()))

        updated.append(key)

    if updated:
        db.commit()
    return {"updated": updated, "errors": errors}


def reset_category(db: Session, category: str) -> int:
    """Reset all fields of a category to schema defaults. Returns count."""
    fields = SCHEMA_BY_CATEGORY.get(category, [])
    count = 0
    for f in fields:
        cfg = db.query(Configuracao).filter(Configuracao.chave == f["key"]).first()
        if cfg:
            db.delete(cfg)
            count += 1
        legacy = LEGACY_ALIASES.get(f["key"])
        if legacy:
            lcfg = db.query(Configuracao).filter(Configuracao.chave == legacy).first()
            if lcfg:
                db.delete(lcfg)
    db.commit()
    return count


def _utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
