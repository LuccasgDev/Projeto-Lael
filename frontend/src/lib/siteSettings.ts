/**
 * Site settings — tipos, fetch e defaults de fallback.
 * O backend (/api/public/site-settings) é a fonte de verdade;
 * estes defaults garantem que o site funcione se a API falhar.
 */

export interface SiteSettings {
  evento?: {
    nome?: string; bebe?: string; titulo?: string; subtitulo?: string;
    data?: string; horario?: string; cidade?: string; estado?: string; pais?: string;
    local?: string; responsaveis?: string; mensagem_boas_vindas?: string;
    mensagem_encerramento?: string; rifa_ativa?: boolean; exibir_dados_evento?: boolean;
  };
  rifa?: {
    valor_numero?: string; mensagem_regras?: string; mensagem_instrucoes?: string;
    exibir_disponiveis?: boolean; aviso_confirmacao?: string;
  };
  premio?: {
    ativo?: boolean; valor?: string; titulo?: string; texto_destaque?: string;
    descricao?: string; texto_antes_valor?: string; regras?: string;
    data_sorteio?: string; exibir_home?: boolean; exibir_popup?: boolean;
    exibir_banner_home?: boolean; mostrar_valor?: boolean;
  };
  popup?: {
    ativo?: boolean; frequencia?: string; titulo?: string; subtitulo?: string;
    valor_destaque?: string; texto?: string; texto_botao?: string;
    texto_botao_secundario?: string; destino_botao?: string;
    destino_botao_secundario?: string; exibir_botao_secundario?: boolean;
    exibir_fechar?: boolean; atraso_segundos?: number; confetes?: boolean;
    cor_fundo?: string; cor_texto?: string; cor_botao?: string;
    mostrar_desktop?: boolean; mostrar_mobile?: boolean;
  };
  reserva?: {
    ativa?: boolean; permitir_renovacao?: boolean; permitir_cancelamento?: boolean;
    texto_expiracao?: string; texto_concluida?: string; texto_expirada?: string;
    alerta_horas?: number; prazo_padrao_horas?: number;
  };
  produtos?: {
    mostrar_imagens?: boolean; mostrar_precos?: boolean; mostrar_descricao?: boolean;
    mostrar_links_amazon?: boolean; mensagem_vazio?: string; modo_preco?: string;
  };
  aparencia?: {
    cor_primaria?: string; cor_fundo?: string; cor_destaque?: string;
    cor_texto?: string; cor_verde?: string; logo_url?: string;
    arredondamento?: number; ativo?: boolean;
  };
  textos?: {
    como_funciona_titulo?: string; produtos_titulo?: string; regras_titulo?: string;
    botao_participar?: string; aviso_importante?: string;
  };
  contato?: {
    whatsapp?: string; mensagem_whatsapp?: string; instagram?: string;
    facebook?: string; tiktok?: string; email?: string; exibir_redes?: boolean;
  };
  pix?: {
    ativo?: boolean; beneficiario?: string; tipo_chave?: string;
    instrucao?: string; mensagem_apos_envio?: string; prazo_horas?: number;
  };
  sorteio?: {
    ativo?: boolean; data?: string; horario?: string; texto?: string;
    exibir_data?: boolean; mensagem_antes?: string; mensagem_depois?: string;
  };
  seo?: {
    titulo_pagina?: string; descricao?: string; imagem?: string; titulo_whatsapp?: string;
  };
  sistema?: {
    modo_manutencao?: boolean; mensagem_manutencao?: string;
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchSiteSettings(): Promise<SiteSettings | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/public/site-settings`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as SiteSettings;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Helpers de leitura com fallback
// ---------------------------------------------------------------------------

export function s(v: string | undefined | null, fallback = ""): string {
  return v === undefined || v === null || v === "" ? fallback : v;
}

export function popupConfig(site: SiteSettings | null) {
  const p = site?.popup;
  return {
    enabled: p?.ativo ?? true,
    valor: s(p?.valor_destaque, "R$ 250,00"),
    titulo: s(p?.titulo, "CHÁ RIFA DO LAEL"),
    chamada: s(p?.subtitulo, "CONCORRA A"),
    texto: s(p?.texto, "Escolha seu número, presenteie o Lael e concorra a um prêmio especial!"),
    mensagemComplementar: "Escolha seu número e participe dessa bênção com a gente!",
    botaoPrincipal: s(p?.texto_botao, "QUERO PARTICIPAR"),
    botaoSecundario: s(p?.texto_botao_secundario, "VER OS PRESENTES"),
    destinoBotao: s(p?.destino_botao, "#numeros"),
    destinoBotaoSecundario: s(p?.destino_botao_secundario, "#regras"),
    exibirBotaoSecundario: p?.exibir_botao_secundario ?? true,
    exibirFechar: p?.exibir_fechar ?? true,
    atrasoSegundos: p?.atraso_segundos ?? 0,
    confetes: p?.confetes ?? true,
    corFundo: s(p?.cor_fundo, "#FFF8F0"),
    corTexto: s(p?.cor_texto, "#29343A"),
    corBotao: s(p?.cor_botao, "#42677D"),
    mostrarDesktop: p?.mostrar_desktop ?? true,
    mostrarMobile: p?.mostrar_mobile ?? true,
    frequencia: s(p?.frequencia, "sessao"),
  };
}
