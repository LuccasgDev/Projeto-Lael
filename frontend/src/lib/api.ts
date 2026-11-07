const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface PublicConfig {
  nome_evento: string;
  data_evento: string;
  whatsapp_casal: string;
  chave_pix: string;
  tipo_chave_pix: string;
  titular_pix: string;
  banco_pix: string;
  prazo_padrao_horas: number;
  total_numeros: number;
  mensagem_inicial?: string;
  mensagem_confirmacao?: string;
}

export interface GridItem {
  id: number;
  numero: number;
  status: "disponivel" | "reservado" | "confirmado" | "compra_externa";
  nome_publico?: string | null;
  produto_id?: number | null;
  produto_nome?: string | null;
  produto_tamanho?: string | null;
  produto_imagem?: string | null;
}

export interface ProdutoPrincipal {
  id: number;
  asin?: string;
  nome: string;
  descricao?: string;
  imagem_url?: string;
  produto_url?: string;
  categoria?: string;
  tamanho?: string | null;
  preco_atual: number | null;
  preco_anterior?: number | null;
  preco_sincronizado_em?: string;
  quantidade_desejada: number;
  disponibilidade_restante: number;
}

export interface NumeroDetail {
  id: number;
  numero: number;
  status: "disponivel" | "reservado" | "confirmado";
  produto_principal?: ProdutoPrincipal;
}

export interface Mimo {
  id: number;
  asin?: string;
  nome: string;
  descricao?: string;
  imagem_url?: string;
  produto_url?: string;
  categoria?: string;
  preco_atual: number | null;
  preco_anterior?: number | null;
  preco_sincronizado_em?: string;
  disponibilidade_restante: number;
}

export interface Comprovante {
  id: number;
  tipo_item: "presente" | "mimo";
  forma_aquisicao: "amazon" | "pix";
  status: "aguardando_envio" | "recebido" | "aprovado" | "rejeitado";
  observacao_admin?: string;
  recebido_em?: string;
  aprovado_em?: string;
  rejeitado_em?: string;
}

export type FormaAquisicao = "amazon" | "pix" | "local";

export interface ReservationResponse {
  id: number;
  numero: number;
  nome_convidado: string;
  whatsapp: string;
  forma_presente: FormaAquisicao;
  forma_mimo: FormaAquisicao;
  presente_nome: string;
  presente_imagem?: string;
  presente_url?: string;
  preco_presente_reserva: number;
  mimo_nome: string;
  mimo_imagem?: string;
  mimo_url?: string;
  preco_mimo_reserva: number;
  valor_pix_total: number;
  status: "reservada" | "confirmada" | "expirada" | "cancelada";
  criada_em: string;
  expira_em: string;
  token_acompanhamento?: string;
  whatsapp_link: string;
  whatsapp_mensagem: string;
  comprovantes: Comprovante[];
}

export interface DashboardStats {
  total_numeros: number;
  numeros_disponiveis: number;
  numeros_reservados: number;
  numeros_confirmados: number;
  reservas_expiradas: number;
  comprovantes_pendentes: number;
  valor_total_pix_confirmado: number;
  valor_total_pix_pendente: number;
  top_presentes: { nome: string; total: number }[];
  top_mimos: { nome: string; total: number }[];
  mimos_disponiveis_total: number;
  numeros_nao_confirmados: number;
  alerta_capacidade_mimos: boolean;
  por_tamanho: { produto_id: number; tamanho: string; nome: string; ativo: boolean; total: number; disponiveis: number; reservados: number; confirmados: number; compra_externa: number }[];
}

export interface ReservationAdminItem {
  id: number;
  numero_id: number;
  numero: number;
  mimo_id: number;
  nome_convidado: string;
  whatsapp: string;
  autoriza_nome_publico: boolean;
  forma_presente: FormaAquisicao;
  forma_mimo: FormaAquisicao;
  preco_presente_reserva: number;
  preco_mimo_reserva: number;
  valor_pix_total: number;
  status: "reservada" | "confirmada" | "expirada" | "cancelada";
  criada_em: string;
  expira_em: string;
  confirmada_em?: string;
  presente_nome: string;
  mimo_nome: string;
  comprovantes: Comprovante[];
  pode_confirmar: boolean;
  horas_restantes: number;
}

export async function fetchPublicConfig(): Promise<PublicConfig> {
  const res = await fetch(`${API_BASE_URL}/public/config`, { cache: "no-store" });
  if (!res.ok) throw new Error("Falha ao carregar configurações do evento");
  return res.json();
}

export async function fetchNumbersGrid(): Promise<GridItem[]> {
  const res = await fetch(`${API_BASE_URL}/public/numbers`, { cache: "no-store" });
  if (!res.ok) throw new Error("Falha ao carregar a grade de números");
  return res.json();
}

export async function fetchNumberDetail(num: number): Promise<NumeroDetail> {
  const res = await fetch(`${API_BASE_URL}/public/numbers/${num}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Falha ao carregar detalhes do número");
  return res.json();
}

export async function fetchAvailableMimos(): Promise<Mimo[]> {
  const res = await fetch(`${API_BASE_URL}/public/mimos`, { cache: "no-store" });
  if (!res.ok) throw new Error("Falha ao carregar mimos");
  return res.json();
}

export async function createReservationApi(data: {
  numero_id: number;
  mimo_id: number;
  nome_convidado: string;
  whatsapp: string;
  autoriza_nome_publico: boolean;
  forma_presente: FormaAquisicao;
  forma_mimo: FormaAquisicao;
  consentimento_lgpd: boolean;
}): Promise<ReservationResponse> {
  const res = await fetch(`${API_BASE_URL}/public/reserve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Erro ao realizar a reserva");
  }
  return res.json();
}

// --- Admin APIs ---

export async function adminLoginApi(email: string, senha: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, senha }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Credenciais inválidas");
  }
  return res.json();
}

export async function fetchDashboardStats(token: string): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE_URL}/admin/dashboard`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar métricas");
  return res.json();
}

export async function fetchAdminReservations(token: string, statusFilter?: string, search?: string): Promise<ReservationAdminItem[]> {
  const params = new URLSearchParams();
  if (statusFilter && statusFilter !== "todos") params.append("status", statusFilter);
  if (search) params.append("search", search);

  const res = await fetch(`${API_BASE_URL}/admin/reservations?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar reservas");
  return res.json();
}

export async function actionVoucherApi(token: string, comprovanteId: number, status: string, observacao: string) {
  const res = await fetch(`${API_BASE_URL}/admin/comprovantes/${comprovanteId}/action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ status, observacao }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao processar comprovante");
  }
  return res.json();
}

export async function confirmReservationApi(token: string, reservaId: number) {
  const res = await fetch(`${API_BASE_URL}/admin/reservations/${reservaId}/confirm`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao confirmar reserva");
  }
  return res.json();
}

export async function releaseReservationApi(token: string, reservaId: number, motivo?: string) {
  const params = new URLSearchParams();
  if (motivo) params.append("motivo", motivo);

  const res = await fetch(`${API_BASE_URL}/admin/reservations/${reservaId}/release?${params.toString()}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao liberar reserva");
  }
  return res.json();
}

export async function extendReservationApi(token: string, reservaId: number, horas: number) {
  const res = await fetch(`${API_BASE_URL}/admin/reservations/${reservaId}/extend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ horas_adicionais: horas }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao estender prazo");
  }
  return res.json();
}

export async function fetchAdminProdutos(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/produtos`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar produtos principais");
  return res.json();
}

// RN-10: listagem de números e marcação de compra externa
export async function fetchAdminNumeros(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/numeros`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar números");
  return res.json();
}

export async function marcarCompraExternaApi(token: string, numeroId: number, marcar: boolean, origem?: string) {
  const res = await fetch(`${API_BASE_URL}/admin/numeros/${numeroId}/compra-externa`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ marcar, origem }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Erro ao marcar compra externa");
  }
  return res.json();
}

// §3/§5 v2: importação de mimos por texto colado (lista da Amazon)
export async function importarMimosTextoApi(token: string, texto: string) {
  const res = await fetch(`${API_BASE_URL}/sync/import-texto?tipo=mimo`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Erro ao importar texto");
  }
  return res.json();
}

export async function updateAdminProdutoPrice(token: string, id: number, preco: number) {
  const res = await fetch(`${API_BASE_URL}/admin/produtos/${id}/price?novo_preco=${preco}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Erro ao atualizar preço");
  return res.json();
}

// RN-01 v2: edição completa da fralda (nome, tamanho, ordem, quantidades, link, imagem, ativo)
export async function updateAdminProduto(token: string, id: number, data: {
  asin?: string | null;
  nome: string;
  descricao?: string | null;
  imagem_url?: string | null;
  produto_url?: string | null;
  categoria?: string | null;
  tamanho?: string | null;
  ordem_exibicao?: number;
  preco_atual?: number | null;
  preco_anterior?: number | null;
  quantidade_desejada?: number;
  quantidade_comprada_externa?: number;
  ativo?: boolean;
}) {
  const res = await fetch(`${API_BASE_URL}/admin/produtos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao salvar fralda");
  }
  return res.json();
}

// RN-01 v2: regera as faixas contínuas de números a partir das quantidades/tamanhos,
// preservando números reservados, confirmados e marcados como compra externa.
export async function regenerarFaixasApi(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/numeros/regenerar-faixas`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao regerar faixas");
  }
  return res.json();
}

export async function fetchAdminMimos(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/mimos`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar mimos");
  return res.json();
}

export async function updateAdminMimoPrice(token: string, id: number, preco: number) {
  const res = await fetch(`${API_BASE_URL}/admin/mimos/${id}/price?novo_preco=${preco}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Erro ao atualizar preço");
  return res.json();
}

// RN-09/RN-10: edição completa do mimo (nome, categoria, quantidades, link, imagem, ativo)
export async function updateAdminMimo(token: string, id: number, data: {
  asin?: string | null;
  nome: string;
  descricao?: string | null;
  imagem_url?: string | null;
  produto_url?: string | null;
  categoria?: string | null;
  preco_atual?: number | null;
  preco_anterior?: number | null;
  quantidade_desejada?: number;
  quantidade_comprada_externa?: number;
  ativo?: boolean;
}) {
  const res = await fetch(`${API_BASE_URL}/admin/mimos/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erro ao salvar mimo");
  }
  return res.json();
}

export async function fetchAdminConfig(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/config`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar configurações");
  return res.json();
}

export async function updateAdminConfig(token: string, configuracoes: Record<string, string>) {
  const res = await fetch(`${API_BASE_URL}/admin/config`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ configuracoes }),
  });
  if (!res.ok) throw new Error("Erro ao salvar configurações");
  return res.json();
}

export async function fetchAuditLogs(token: string) {
  const res = await fetch(`${API_BASE_URL}/admin/audit-logs`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Erro ao carregar logs");
  return res.json();
}

export function getExportUrl(type: "reservations" | "pix", format: "csv" | "xlsx", token: string) {
  return `${API_BASE_URL}/admin/export/${type}?format_type=${format}`;
}


// --- Acompanhamento (link secreto, sem login) ---
export async function fetchAcompanhamento(token: string): Promise<ReservationResponse> {
  const res = await fetch(`${API_BASE_URL}/public/acompanhamento/${encodeURIComponent(token)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Link de acompanhamento inválido.");
  }
  return res.json();
}
