"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  ShieldCheck, LogOut, CheckCircle2, Clock, AlertTriangle,
  FileSpreadsheet, Settings, Gift, ListOrdered, History,
  Search, ExternalLink, RefreshCw, Plus, ArrowUpRight, Check, X
} from "lucide-react";
import {
  adminLoginApi, fetchDashboardStats, fetchAdminReservations,
  actionVoucherApi, confirmReservationApi, releaseReservationApi,
  extendReservationApi, fetchAdminProdutos, updateAdminProdutoPrice, updateAdminProduto,
  fetchAdminMimos, updateAdminMimoPrice, updateAdminMimo, fetchAdminConfig,
  updateAdminConfig, fetchAuditLogs, getExportUrl,
  fetchAdminNumeros, marcarCompraExternaApi, importarMimosTextoApi, regenerarFaixasApi,
  DashboardStats, ReservationAdminItem
} from "@/lib/api";

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [adminName, setAdminName] = useState<string>("");

  // Login form state
  const [loginEmail, setLoginEmail] = useState("");
  const [loginSenha, setLoginSenha] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  // Active Tab
  const [activeTab, setActiveTab] = useState<"dashboard" | "reservas" | "presentes" | "mimos" | "config" | "export" | "auditoria">("dashboard");

  // Dashboard Data
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Reservations Data
  const [reservations, setReservations] = useState<ReservationAdminItem[]>([]);
  const [resStatusFilter, setResStatusFilter] = useState<string>("todos");
  const [resSearch, setResSearch] = useState<string>("");

  // Products & Mimos
  const [produtos, setProdutos] = useState<any[]>([]);
  const [mimos, setMimos] = useState<any[]>([]);
  // Importação de mimos por texto (§3 v2)
  const [textoImportacao, setTextoImportacao] = useState("");
  // Números (RN-10: compra externa)
  const [numerosAdmin, setNumerosAdmin] = useState<any[]>([]);
  const [numeroExterno, setNumeroExterno] = useState("");
  const [origemExterna, setOrigemExterna] = useState("");
  // Edição de fraldas (RN-01) e mimos (RN-09/RN-10)
  const [editingProdutoId, setEditingProdutoId] = useState<number | null>(null);
  const [produtoForm, setProdutoForm] = useState<any>(null);
  const [editingMimoId, setEditingMimoId] = useState<number | null>(null);
  const [mimoForm, setMimoForm] = useState<any>(null);

  // Settings
  const [configs, setConfigs] = useState<Record<string, string>>({});
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // General Loading & Feedback
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  // Load token from storage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("lael_admin_token");
    const savedName = localStorage.getItem("lael_admin_name");
    if (savedToken) {
      setToken(savedToken);
      if (savedName) setAdminName(savedName);
    }
  }, []);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 4000);
  };

  // Load Tab Data
  const loadTabData = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      if (activeTab === "dashboard") {
        const data = await fetchDashboardStats(token);
        setStats(data);
      } else if (activeTab === "reservas") {
        const data = await fetchAdminReservations(token, resStatusFilter, resSearch);
        setReservations(data);
      } else if (activeTab === "presentes") {
        const data = await fetchAdminProdutos(token);
        setProdutos(data);
        const nums = await fetchAdminNumeros(token);
        setNumerosAdmin(nums);
      } else if (activeTab === "mimos") {
        const data = await fetchAdminMimos(token);
        setMimos(data);
      } else if (activeTab === "config") {
        const data = await fetchAdminConfig(token);
        setConfigs(data);
      } else if (activeTab === "auditoria") {
        const data = await fetchAuditLogs(token);
        setAuditLogs(data);
      }
    } catch (err: any) {
      if (err.message?.includes("401") || err.message?.includes("expirado")) {
        handleLogout();
      }
    } finally {
      setIsLoading(false);
    }
  }, [token, activeTab, resStatusFilter, resSearch]);

  useEffect(() => {
    if (token) {
      loadTabData();
    }
  }, [token, activeTab, loadTabData]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoggingIn(true);
    setLoginError("");

    try {
      const data = await adminLoginApi(loginEmail, loginSenha);
      setToken(data.access_token);
      setAdminName(data.admin_nome);
      localStorage.setItem("lael_admin_token", data.access_token);
      localStorage.setItem("lael_admin_name", data.admin_nome);
      showToast(`Bem-vindos, ${data.admin_nome}!`);
    } catch (err: any) {
      setLoginError(err.message || "E-mail ou senha inválidos.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setAdminName("");
    localStorage.removeItem("lael_admin_token");
    localStorage.removeItem("lael_admin_name");
  };

  // Voucher Action
  const handleVoucherAction = async (compId: number, status: string) => {
    if (!token) return;
    try {
      await actionVoucherApi(token, compId, status, `Alterado para ${status} pelo painel`);
      showToast(`Comprovante marcado como ${status}.`);
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao atualizar comprovante");
    }
  };

  // Confirm Reservation
  const handleConfirmReservation = async (resId: number) => {
    if (!token) return;
    if (!confirm("Confirmar esta contribuição e aprovar definitivamente o número?")) return;
    try {
      await confirmReservationApi(token, resId);
      showToast("Reserva e número confirmados com sucesso! 🎉");
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao confirmar reserva");
    }
  };

  // Release Reservation
  const handleReleaseReservation = async (resId: number) => {
    if (!token) return;
    const motivo = prompt("Motivo da liberação do número (opcional):");
    if (motivo === null) return;
    try {
      await releaseReservationApi(token, resId, motivo);
      showToast("Reserva cancelada e número colocado novamente disponível.");
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao liberar número");
    }
  };

  // Extend Deadline
  const handleExtendDeadline = async (resId: number, horas: number) => {
    if (!token) return;
    try {
      await extendReservationApi(token, resId, horas);
      showToast(`Prazo estendido com sucesso em +${horas} horas!`);
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao estender prazo");
    }
  };

  // Quick Price Updates
  const handleUpdatePrice = async (id: number, type: "produto" | "mimo", currentPrice: number) => {
    if (!token) return;
    const input = prompt(`Informe o novo preço (R$):`, currentPrice.toFixed(2));
    if (!input) return;
    const newPrice = parseFloat(input.replace(",", "."));
    if (isNaN(newPrice) || newPrice <= 0) {
      alert("Preço inválido.");
      return;
    }

    try {
      if (type === "produto") {
        await updateAdminProdutoPrice(token, id, newPrice);
      } else {
        await updateAdminMimoPrice(token, id, newPrice);
      }
      showToast("Preço atualizado com sucesso!");
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao atualizar preço");
    }
  };

  // RN-01: edição de fralda e regeneração de faixas
  const openProdutoEditor = (p: any) => {
    setEditingProdutoId(p.id);
    setProdutoForm({
      nome: p.nome,
      tamanho: p.tamanho || "",
      ordem_exibicao: p.ordem_exibicao ?? 0,
      quantidade_desejada: p.quantidade_desejada ?? 1,
      quantidade_comprada_externa: p.quantidade_comprada_externa ?? 0,
      produto_url: p.produto_url || "",
      imagem_url: p.imagem_url || "",
      ativo: p.ativo !== false,
    });
  };

  const handleSaveProduto = async () => {
    if (!token || !produtoForm) return;
    const qtd = parseInt(produtoForm.quantidade_desejada, 10);
    const qtdExt = parseInt(produtoForm.quantidade_comprada_externa, 10) || 0;
    if (!produtoForm.nome?.trim() || isNaN(qtd) || qtd < 1) {
      alert("Informe um nome e uma quantidade desejada válida (mínimo 1).");
      return;
    }
    try {
      await updateAdminProduto(token, editingProdutoId!, {
        nome: produtoForm.nome.trim(),
        tamanho: produtoForm.tamanho || null,
        ordem_exibicao: parseInt(produtoForm.ordem_exibicao, 10) || 0,
        quantidade_desejada: qtd,
        quantidade_comprada_externa: qtdExt,
        produto_url: produtoForm.produto_url || null,
        imagem_url: produtoForm.imagem_url || null,
        ativo: !!produtoForm.ativo,
        // campos não editados aqui são recarregados do objeto original
        asin: produtos.find((p) => p.id === editingProdutoId)?.asin || null,
        descricao: produtos.find((p) => p.id === editingProdutoId)?.descricao || null,
        categoria: produtos.find((p) => p.id === editingProdutoId)?.categoria || "Fraldas",
        preco_atual: produtos.find((p) => p.id === editingProdutoId)?.preco_atual ?? null,
        preco_anterior: produtos.find((p) => p.id === editingProdutoId)?.preco_anterior ?? null,
      });
      showToast("Fralda atualizada! Use 'Regerar faixas' se as quantidades mudaram.");
      setEditingProdutoId(null);
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao salvar fralda");
    }
  };

  const handleRegenerarFaixas = async () => {
    if (!token) return;
    if (!confirm("Regerar as faixas de números conforme as quantidades e ordem atuais das fraldas?\n\nNúmeros reservados, confirmados ou marcados como compra externa NÃO serão alterados.")) return;
    try {
      const r = await regenerarFaixasApi(token);
      showToast(r.message || "Faixas regeradas.");
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao regerar faixas");
    }
  };

  // RN-09/RN-10: edição de mimo
  const openMimoEditor = (m: any) => {
    setEditingMimoId(m.id);
    setMimoForm({
      nome: m.nome,
      categoria: m.categoria || "",
      quantidade_desejada: m.quantidade_desejada ?? 1,
      quantidade_comprada_externa: m.quantidade_comprada_externa ?? 0,
      produto_url: m.produto_url || "",
      imagem_url: m.imagem_url || "",
      ativo: m.ativo !== false,
    });
  };

  const handleSaveMimo = async () => {
    if (!token || !mimoForm) return;
    const qtd = parseInt(mimoForm.quantidade_desejada, 10);
    const qtdExt = parseInt(mimoForm.quantidade_comprada_externa, 10) || 0;
    if (!mimoForm.nome?.trim() || isNaN(qtd) || qtd < 1) {
      alert("Informe um nome e uma quantidade desejada válida (mínimo 1).");
      return;
    }
    try {
      const original = mimos.find((m) => m.id === editingMimoId);
      await updateAdminMimo(token, editingMimoId!, {
        nome: mimoForm.nome.trim(),
        categoria: mimoForm.categoria || null,
        quantidade_desejada: qtd,
        quantidade_comprada_externa: qtdExt,
        produto_url: mimoForm.produto_url || null,
        imagem_url: mimoForm.imagem_url || null,
        ativo: !!mimoForm.ativo,
        asin: original?.asin || null,
        descricao: original?.descricao || null,
        preco_atual: original?.preco_atual ?? null,
        preco_anterior: original?.preco_anterior ?? null,
      });
      showToast("Mimo atualizado com sucesso!");
      setEditingMimoId(null);
      loadTabData();
    } catch (err: any) {
      alert(err.message || "Erro ao salvar mimo");
    }
  };

  // Save Settings
  const handleSaveConfigs = async () => {
    if (!token) return;
    setIsSavingConfig(true);
    try {
      await updateAdminConfig(token, configs);
      showToast("Configurações salvas com sucesso!");
    } catch (err: any) {
      alert(err.message || "Erro ao salvar configurações");
    } finally {
      setIsSavingConfig(false);
    }
  };

  // ================= LOGIN SCREEN =================
  if (!token) {
    return (
      <div className="min-h-screen bg-[#FFF8F0] flex flex-col justify-center items-center p-4">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-xl border border-[#B9D8E8] p-6 sm:p-8">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[#B9D8E8] to-[#FFF8F0] border border-[#42677D]/20 flex items-center justify-center text-3xl mx-auto mb-3 shadow-xs">
              👶
            </div>
            <h1 className="text-2xl font-black text-[#42677D]">Painel do Casal</h1>
            <p className="text-xs text-slate-500 mt-1">
              Acesso exclusivo para Talia & Lucas administrarem o Chá de Rifa do Lael.
            </p>
          </div>

          {loginError && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#42677D] mb-1">E-mail</label>
              <input
                type="email"
                required
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="w-full px-3.5 py-2.5 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#42677D] mb-1">Senha</label>
              <input
                type="password"
                required
                value={loginSenha}
                onChange={(e) => setLoginSenha(e.target.value)}
                className="w-full px-3.5 py-2.5 text-xs bg-slate-50 rounded-xl border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
              />
            </div>

            <button
              type="submit"
              disabled={isLoggingIn}
              className="w-full py-3 rounded-xl bg-[#42677D] hover:bg-[#345264] text-white font-bold text-xs shadow-md transition-all cursor-pointer"
            >
              {isLoggingIn ? "Entrando..." : "Entrar no Painel"}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-100 text-center">
            <Link href="/" className="text-xs font-semibold text-[#42677D] hover:underline">
              ← Voltar ao site público da rifa
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ================= MAIN ADMIN DASHBOARD =================
  return (
    <div className="min-h-screen bg-[#FFF8F0] flex flex-col">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-[#42677D] text-white px-4 py-3 rounded-2xl shadow-xl text-xs font-bold flex items-center gap-2 animate-bounce">
          <span>✨</span>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Admin Top Header */}
      <header className="bg-white border-b border-[#B9D8E8] sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-2xl">👶</span>
              <span className="font-extrabold text-[#42677D] text-sm sm:text-base">
                Chá de Rifa do Lael <span className="text-xs font-normal text-slate-500">| Painel</span>
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-700 hidden sm:inline">
              Olá, <strong>{adminName || "Talia e Lucas"}</strong>
            </span>

            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-xl text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sair</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 flex gap-2 overflow-x-auto pb-2 scrollbar-none">
          {[
            { id: "dashboard", label: "Dashboard", icon: "📊" },
            { id: "reservas", label: "Reservas & Comprovantes", icon: "📋" },
            { id: "presentes", label: "Presentes Principais", icon: "🎁" },
            { id: "mimos", label: "Mimos Complementares", icon: "🧸" },
            { id: "config", label: "Configurações & Pix", icon: "⚙️" },
            { id: "export", label: "Relatórios & Exportar", icon: "📥" },
            { id: "auditoria", label: "Histórico de Auditoria", icon: "🔍" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? "bg-[#42677D] text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {/* ================= TAB: DASHBOARD ================= */}
        {activeTab === "dashboard" && stats && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-[#42677D]">Visão Geral do Chá de Rifa</h2>
                <p className="text-xs text-slate-500">Acompanhamento em tempo real das reservas e arrecadação.</p>
              </div>
              <button
                onClick={loadTabData}
                className="px-3 py-1.5 rounded-xl bg-white border border-[#B9D8E8] text-xs font-semibold text-[#42677D] hover:bg-[#B9D8E8]/20 flex items-center gap-1 cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Atualizar</span>
              </button>
            </div>

            {/* Metric Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
                <span className="text-xs text-slate-500 block mb-1">Total de Números</span>
                <span className="text-2xl font-black text-[#42677D]">{stats.total_numeros}</span>
              </div>

              <div className="bg-emerald-50/80 p-4 rounded-2xl border border-emerald-200 shadow-2xs">
                <span className="text-xs text-emerald-800 font-semibold block mb-1">Disponíveis (Verde)</span>
                <span className="text-2xl font-black text-emerald-900">{stats.numeros_disponiveis}</span>
              </div>

              <div className="bg-amber-50/80 p-4 rounded-2xl border border-amber-200 shadow-2xs">
                <span className="text-xs text-amber-800 font-semibold block mb-1">Reservados (Amarelo)</span>
                <span className="text-2xl font-black text-amber-900">{stats.numeros_reservados}</span>
              </div>

              <div className="bg-slate-100 p-4 rounded-2xl border border-slate-300 shadow-2xs">
                <span className="text-xs text-slate-700 font-semibold block mb-1">Confirmados (Cinza)</span>
                <span className="text-2xl font-black text-slate-900">{stats.numeros_confirmados}</span>
              </div>
            </div>

            {/* RN-11: alerta de capacidade de mimos */}
            {stats.alerta_capacidade_mimos && (
              <div className="p-4 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 text-xs sm:text-sm flex items-start gap-3">
                <span className="text-lg">⚠️</span>
                <span>
                  <strong>Atenção:</strong> só há <strong>{stats.mimos_disponiveis_total}</strong> mimo(s) disponível(eis),
                  mas existem <strong>{stats.numeros_nao_confirmados}</strong> número(s) ainda não confirmado(s).
                  Cada reserva exige um mimo — amplie a lista ou registre as compras externas.
                </span>
              </div>
            )}

            {/* RN-01 v2: totais por tamanho de fralda */}
            {stats.por_tamanho && stats.por_tamanho.length > 0 && (
              <div className="bg-white p-5 rounded-2xl border border-[#B9D8E8] shadow-xs">
                <h3 className="font-bold text-sm text-[#42677D] mb-3">Fraldas por tamanho</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                  {stats.por_tamanho.map((g) => (
                    <div key={g.produto_id} className="p-3 rounded-xl bg-[#FFF8F0] border border-[#A9B8A0]/40">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-black text-[#D99A7B]">{g.tamanho}</span>
                        {!g.ativo && <span className="text-[9px] bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded-full font-bold">inativo</span>}
                      </div>
                      <span className="text-[10px] text-slate-500 block truncate mb-1.5" title={g.nome}>{g.nome}</span>
                      <div className="text-[11px] space-y-0.5 text-slate-700">
                        <div>🟢 {g.disponiveis} disponíveis</div>
                        <div>🟡 {g.reservados} reservados</div>
                        <div>⚪ {g.confirmados} confirmados</div>
                        {g.compra_externa > 0 && <div>🛒 {g.compra_externa} compra externa</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Financial & Pending Highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-[#B9D8E8] shadow-xs">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Arrecadação Pix Confirmada
                </span>
                <span className="text-2xl sm:text-3xl font-black text-emerald-700 block">
                  R$ {stats.valor_total_pix_confirmado.toFixed(2).replace(".", ",")}
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Comprovantes aprovados e confirmados
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#B9D8E8] shadow-xs">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Pix Previsto em Reservas
                </span>
                <span className="text-2xl sm:text-3xl font-black text-amber-600 block">
                  R$ {stats.valor_total_pix_pendente.toFixed(2).replace(".", ",")}
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Aguardando conferência de comprovantes
                </span>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#B9D8E8] shadow-xs">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Comprovantes Pendentes
                </span>
                <span className="text-2xl sm:text-3xl font-black text-[#D99A7B] block">
                  {stats.comprovantes_pendentes}
                </span>
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Aguardando aprovação para liberar confirmação
                </span>
              </div>
            </div>

            {/* Tops Lists */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
                <h3 className="font-bold text-sm text-[#42677D] mb-3">🎁 Presentes Principais Mais Escolhidos</h3>
                <div className="space-y-2">
                  {stats.top_presentes.map((p, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
                      <span className="font-medium text-slate-800 truncate pr-2">{p.nome}</span>
                      <span className="font-bold text-[#42677D] bg-slate-100 px-2 py-0.5 rounded-full shrink-0">
                        {p.total} reserva(s)
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs">
                <h3 className="font-bold text-sm text-[#42677D] mb-3">🧸 Mimos Mais Escolhidos</h3>
                <div className="space-y-2">
                  {stats.top_mimos.map((m, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
                      <span className="font-medium text-slate-800 truncate pr-2">{m.nome}</span>
                      <span className="font-bold text-[#42677D] bg-slate-100 px-2 py-0.5 rounded-full shrink-0">
                        {m.total} escolha(s)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB: RESERVAS & COMPROVANTES ================= */}
        {activeTab === "reservas" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-black text-[#42677D]">Gestão de Reservas</h2>
                <p className="text-xs text-slate-500">Conferência dos 2 comprovantes obrigatórios e aprovação.</p>
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2 w-full sm:w-auto">
                <select
                  value={resStatusFilter}
                  onChange={(e) => setResStatusFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-slate-300 text-xs bg-white font-medium cursor-pointer"
                >
                  <option value="todos">Todos os Status</option>
                  <option value="reservada">Apenas Reservadas</option>
                  <option value="confirmada">Apenas Confirmadas</option>
                  <option value="expirada">Apenas Expiradas</option>
                  <option value="cancelada">Apenas Canceladas</option>
                </select>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Buscar nome ou whatsapp..."
                    value={resSearch}
                    onChange={(e) => setResSearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 rounded-xl border border-slate-300 text-xs bg-white"
                  />
                </div>
              </div>
            </div>

            {/* Reservations Table */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                      <th className="p-3">Nº</th>
                      <th className="p-3">Convidado & Contato</th>
                      <th className="p-3">Presente Principal</th>
                      <th className="p-3">Mimo Complementar</th>
                      <th className="p-3">Pix Total</th>
                      <th className="p-3">Tempo Restante</th>
                      <th className="p-3">Comprovantes (Presente / Mimo)</th>
                      <th className="p-3 text-right">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reservations.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-slate-400 text-xs">
                          Nenhuma reserva encontrada com os filtros selecionados.
                        </td>
                      </tr>
                    ) : (
                      reservations.map((r) => {
                        const compPres = r.comprovantes.find((c) => c.tipo_item === "presente");
                        const compMimo = r.comprovantes.find((c) => c.tipo_item === "mimo");

                        return (
                          <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                            <td className="p-3 font-black text-sm text-[#42677D]">
                              #{String(r.numero).padStart(2, "0")}
                            </td>

                            <td className="p-3">
                              <span className="font-bold text-slate-800 block">{r.nome_convidado}</span>
                              <a
                                href={`https://api.whatsapp.com/send?phone=55${r.whatsapp}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-emerald-700 font-semibold hover:underline inline-flex items-center gap-1 text-[11px]"
                              >
                                <span>{r.whatsapp}</span>
                                <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            </td>

                            <td className="p-3">
                              <span className="font-medium text-slate-800 block truncate max-w-[140px]">{r.presente_nome}</span>
                              <span className="text-[10px] text-slate-500">
                                {r.forma_presente === "amazon" ? "📦 Amazon" : r.forma_presente === "local" ? "🛍️ Loja Física" : `💸 Pix (R$ ${r.preco_presente_reserva.toFixed(2)})`}
                              </span>
                            </td>

                            <td className="p-3">
                              <span className="font-medium text-slate-800 block truncate max-w-[140px]">{r.mimo_nome}</span>
                              <span className="text-[10px] text-slate-500">
                                {r.forma_mimo === "amazon" ? "📦 Amazon" : r.forma_mimo === "local" ? "🛍️ Loja Física" : `💸 Pix (R$ ${r.preco_mimo_reserva.toFixed(2)})`}
                              </span>
                            </td>

                            <td className="p-3 font-black text-slate-800">
                              {r.valor_pix_total > 0 ? `R$ ${r.valor_pix_total.toFixed(2)}` : "-"}
                            </td>

                            <td className="p-3">
                              {r.status === "reservada" ? (
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                  r.horas_restantes < 12 ? "bg-rose-100 text-rose-800" : "bg-amber-100 text-amber-800"
                                }`}>
                                  ⏱️ {r.horas_restantes}h restantes
                                </span>
                              ) : r.status === "confirmada" ? (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700">
                                  ✓ Confirmada
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500">
                                  {r.status}
                                </span>
                              )}
                            </td>

                            {/* VOUCHERS CONTROL */}
                            <td className="p-3">
                              <div className="space-y-1">
                                {/* Presente Voucher */}
                                {compPres && (
                                  <div className="flex items-center gap-1.5 text-[11px]">
                                    <span className="font-semibold text-slate-600 w-14">Presente:</span>
                                    <span className={`px-1.5 py-0.5 rounded-md text-[9px] font-bold ${
                                      compPres.status === "aprovado" ? "bg-emerald-100 text-emerald-800" :
                                      compPres.status === "rejeitado" ? "bg-rose-100 text-rose-800" :
                                      "bg-amber-100 text-amber-800"
                                    }`}>
                                      {compPres.status}
                                    </span>
                                    {r.status === "reservada" && (
                                      <div className="flex items-center gap-1 ml-1">
                                        <button
                                          onClick={() => handleVoucherAction(compPres.id, "aprovado")}
                                          className="p-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold"
                                          title="Aprovar Comprovante do Presente"
                                        >
                                          ✓
                                        </button>
                                        <button
                                          onClick={() => handleVoucherAction(compPres.id, "rejeitado")}
                                          className="p-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold"
                                          title="Rejeitar Comprovante"
                                        >
                                          ✕
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                )}

                                {/* Mimo Voucher */}
                                {compMimo && (
                                  <div className="flex items-center gap-1.5 text-[11px]">
                                    <span className="font-semibold text-slate-600 w-14">Mimo:</span>
                                    <span className={`px-1.5 py-0.5 rounded-md text-[9px] font-bold ${
                                      compMimo.status === "aprovado" ? "bg-emerald-100 text-emerald-800" :
                                      compMimo.status === "rejeitado" ? "bg-rose-100 text-rose-800" :
                                      "bg-amber-100 text-amber-800"
                                    }`}>
                                      {compMimo.status}
                                    </span>
                                    {r.status === "reservada" && (
                                      <div className="flex items-center gap-1 ml-1">
                                        <button
                                          onClick={() => handleVoucherAction(compMimo.id, "aprovado")}
                                          className="p-1 rounded bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold"
                                          title="Aprovar Comprovante do Mimo"
                                        >
                                          ✓
                                        </button>
                                        <button
                                          onClick={() => handleVoucherAction(compMimo.id, "rejeitado")}
                                          className="p-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold"
                                          title="Rejeitar Comprovante"
                                        >
                                          ✕
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </td>

                            {/* Actions Column */}
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                {r.status === "reservada" && (
                                  <>
                                    <button
                                      onClick={() => handleConfirmReservation(r.id)}
                                      disabled={!r.pode_confirmar}
                                      className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                                        r.pode_confirmar
                                          ? "bg-emerald-600 text-white hover:bg-emerald-700 shadow-xs"
                                          : "bg-slate-100 text-slate-400 cursor-not-allowed"
                                      }`}
                                      title={r.pode_confirmar ? "Confirmar Reserva" : "Aprovação pendente dos 2 comprovantes"}
                                    >
                                      Confirmar
                                    </button>

                                    <button
                                      onClick={() => handleExtendDeadline(r.id, 24)}
                                      className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold cursor-pointer"
                                      title="Estender Prazo em +24 horas"
                                    >
                                      +24h
                                    </button>

                                    <button
                                      onClick={() => handleReleaseReservation(r.id)}
                                      className="px-2 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 text-[11px] font-semibold cursor-pointer"
                                      title="Liberar Número (Cancelar Reserva)"
                                    >
                                      Liberar
                                    </button>
                                  </>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB: PRESENTES PRINCIPAIS (FRALDAS) ================= */}
        {activeTab === "presentes" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-[#42677D]">Fraldas (Lista da Talia)</h2>
                <p className="text-xs text-slate-500">Cada número equivale a uma fralda; os grupos seguem a ordem por tamanho (editável pelo administrador).</p>
              </div>
              <button
                onClick={handleRegenerarFaixas}
                className="px-4 py-2 rounded-xl bg-[#A9B8A0] hover:bg-[#93a589] text-[#29343A] text-xs font-bold shadow-2xs cursor-pointer"
                title="Reagrupa os números em faixas contínuas conforme as quantidades e a ordem atuais. Não altera números reservados, confirmados ou de compra externa."
              >
                ⟳ Regerar faixas de números
              </button>
            </div>

            {/* RN-10: compra externa */}
            <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-xs">
              <h3 className="font-bold text-sm text-[#42677D] mb-1">🛒 Compra externa de fralda (RN-10)</h3>
              <p className="text-[11px] text-slate-500 mb-3">
                Alguém comprou uma fralda direto na lista da Amazon? Marque o número como ocupado — ele fica cinza para todos e a origem fica registrada.
              </p>
              <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
                <input
                  type="number"
                  min={1}
                  placeholder="Nº (ex.: 42)"
                  value={numeroExterno}
                  onChange={(e) => setNumeroExterno(e.target.value)}
                  aria-label="Número ocupado por compra externa"
                  className="w-28 px-3 py-2 text-xs bg-white rounded-xl border border-[#B9D8E8]"
                />
                <input
                  type="text"
                  placeholder="Origem (ex.: avó comprou na Amazon)"
                  value={origemExterna}
                  onChange={(e) => setOrigemExterna(e.target.value)}
                  aria-label="Origem da compra externa"
                  className="flex-1 px-3 py-2 text-xs bg-white rounded-xl border border-[#B9D8E8]"
                />
                <button
                  onClick={async () => {
                    try {
                      const alvo = numerosAdmin.find((n: any) => n.numero === parseInt(numeroExterno, 10));
                      if (!alvo) { showToast("Número não encontrado."); return; }
                      const r = await marcarCompraExternaApi(token!, alvo.id, true, origemExterna || undefined);
                      showToast(r.message || "Número marcado como compra externa.");
                      setNumeroExterno(""); setOrigemExterna("");
                      const nums = await fetchAdminNumeros(token!);
                      setNumerosAdmin(nums);
                    } catch (e: any) {
                      showToast(e.message || "Erro ao marcar compra externa.");
                    }
                  }}
                  className="px-4 py-2 rounded-xl bg-[#42677D] text-white text-xs font-bold hover:bg-[#345264] cursor-pointer"
                >
                  Marcar como ocupado
                </button>
              </div>
              {numerosAdmin.some((n: any) => n.status === "compra_externa") && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {numerosAdmin.filter((n: any) => n.status === "compra_externa").map((n: any) => (
                    <button
                      key={n.id}
                      onClick={async () => {
                        try {
                          await marcarCompraExternaApi(token!, n.id, false);
                          showToast(`Número ${String(n.numero).padStart(2, "0")} voltou a ficar disponível.`);
                          const nums = await fetchAdminNumeros(token!);
                          setNumerosAdmin(nums);
                        } catch (e: any) {
                          showToast(e.message || "Erro ao remover marcação.");
                        }
                      }}
                      title={`${n.origem_ocupacao ?? "Compra externa"} — clique para devolver o número`}
                      className="px-2 py-1 rounded-lg bg-slate-200 text-slate-700 text-[11px] font-bold hover:bg-rose-100 hover:text-rose-800 transition-colors cursor-pointer"
                    >
                      {String(n.numero).padStart(2, "0")} ✕
                    </button>
                  ))}
                  <span className="text-[10px] text-slate-400 self-center">clique em um número para desfazer</span>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {produtos.map((p) => (
                <div key={p.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
                  <div className="flex gap-3">
                  <div className="w-20 h-20 rounded-xl bg-slate-50 shrink-0 border border-slate-100 overflow-hidden flex items-center justify-center">
                    {p.imagem_url ? (
                      <img src={p.imagem_url} alt={p.nome} className="object-contain w-full h-full p-1" />
                    ) : (
                      <span>🎁</span>
                    )}
                  </div>

                  <div className="flex-1">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">
                      {p.tamanho ? `Tamanho ${p.tamanho} · ` : ""}{p.categoria}
                    </span>
                    <h4 className="font-bold text-xs text-slate-800 line-clamp-1">{p.nome}</h4>
                    <span className="text-sm font-black text-[#42677D] block mt-1">
                      {p.preco_atual === null || p.preco_atual === undefined
                        ? <span className="text-[#D99A7B]">Preço a informar</span>
                        : `R$ ${Number(p.preco_atual).toFixed(2).replace(".", ",")}`}
                    </span>
                    <span className="text-[10px] text-slate-400 block">
                      Desejado: {p.quantidade_desejada} · Números: {(p.numeros_associados || []).length > 0 ? `${Math.min(...p.numeros_associados)}–${Math.max(...p.numeros_associados)}` : "—"}
                      {!p.ativo ? " · INATIVA" : ""}
                    </span>

                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => handleUpdatePrice(p.id, "produto", p.preco_atual ?? 0)}
                        className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold cursor-pointer"
                      >
                        {p.preco_atual == null ? "Informar Preço" : "Editar Preço"}
                      </button>
                      <button
                        onClick={() => (editingProdutoId === p.id ? setEditingProdutoId(null) : openProdutoEditor(p))}
                        className="px-2 py-1 rounded-lg bg-[#B9D8E8] hover:bg-[#a5c8dc] text-[#42677D] text-[11px] font-bold cursor-pointer"
                      >
                        {editingProdutoId === p.id ? "Fechar" : "Editar"}
                      </button>

                      {p.produto_url && (
                        <a
                          href={p.produto_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-[#42677D] hover:underline flex items-center gap-1"
                        >
                          <span>Amazon</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                  </div>

                  {editingProdutoId === p.id && produtoForm && (
                    <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2">
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">Nome do produto</label>
                      <input
                        type="text"
                        value={produtoForm.nome}
                        onChange={(e) => setProdutoForm({ ...produtoForm, nome: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="text-[10px] font-bold text-slate-500">Tamanho</label>
                      <label className="text-[10px] font-bold text-slate-500">Ordem na grade</label>
                      <input
                        type="text"
                        value={produtoForm.tamanho}
                        onChange={(e) => setProdutoForm({ ...produtoForm, tamanho: e.target.value })}
                        placeholder="ex.: RN, P, M, G"
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <input
                        type="number"
                        value={produtoForm.ordem_exibicao}
                        onChange={(e) => setProdutoForm({ ...produtoForm, ordem_exibicao: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="text-[10px] font-bold text-slate-500">Unidades desejadas (números)</label>
                      <label className="text-[10px] font-bold text-slate-500">Compradas fora do site</label>
                      <input
                        type="number"
                        min={1}
                        value={produtoForm.quantidade_desejada}
                        onChange={(e) => setProdutoForm({ ...produtoForm, quantidade_desejada: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <input
                        type="number"
                        min={0}
                        value={produtoForm.quantidade_comprada_externa}
                        onChange={(e) => setProdutoForm({ ...produtoForm, quantidade_comprada_externa: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">Link da Amazon</label>
                      <input
                        type="url"
                        value={produtoForm.produto_url}
                        onChange={(e) => setProdutoForm({ ...produtoForm, produto_url: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">URL da imagem</label>
                      <input
                        type="url"
                        value={produtoForm.imagem_url}
                        onChange={(e) => setProdutoForm({ ...produtoForm, imagem_url: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 flex items-center gap-2 text-xs font-semibold text-slate-700">
                        <input
                          type="checkbox"
                          checked={!!produtoForm.ativo}
                          onChange={(e) => setProdutoForm({ ...produtoForm, ativo: e.target.checked })}
                        />
                        Fralda ativa (disponível para os números)
                      </label>
                      <div className="col-span-2 flex gap-2 pt-1">
                        <button
                          onClick={handleSaveProduto}
                          className="px-4 py-1.5 rounded-lg bg-[#42677D] text-white text-xs font-bold cursor-pointer"
                        >
                          Salvar fralda
                        </button>
                        <button
                          onClick={() => setEditingProdutoId(null)}
                          className="px-4 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-bold cursor-pointer"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= TAB: MIMOS ================= */}
        {activeTab === "mimos" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-[#42677D]">Mimos Complementares (Lista de Lucas)</h2>
                <p className="text-xs text-slate-500">Controle de estoque, compras externas e disponibilidade.</p>
              </div>
            </div>

            {/* §3/§5 v2: importação por texto colado */}
            <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-xs">
              <h3 className="font-bold text-sm text-[#42677D] mb-1">📋 Importar lista por texto</h3>
              <p className="text-[11px] text-slate-500 mb-2">
                Cole a lista copiada da Amazon. Um item por linha, separado por ponto e vírgula: <code>Nome; quantidade; preço</code> (preço é opcional).
              </p>
              <textarea
                value={textoImportacao}
                onChange={(e) => setTextoImportacao(e.target.value)}
                rows={4}
                placeholder={"Toalha com capuz; 1; R$ 39,90\nChupeta silicone; 3; 29,90\nLivro de pano; 2"}
                aria-label="Texto da lista de mimos para importação"
                className="w-full px-3 py-2 text-xs bg-white rounded-xl border border-[#B9D8E8] font-mono"
              />
              <button
                onClick={async () => {
                  try {
                    const r = await importarMimosTextoApi(token!, textoImportacao);
                    showToast(`Importação concluída: ${r.criados ?? 0} criados, ${r.atualizados ?? 0} atualizados.`);
                    setTextoImportacao("");
                    const data = await fetchAdminMimos(token!);
                    setMimos(data);
                  } catch (e: any) {
                    showToast(e.message || "Erro na importação.");
                  }
                }}
                disabled={!textoImportacao.trim()}
                className="mt-2 px-4 py-2 rounded-xl bg-[#42677D] text-white text-xs font-bold hover:bg-[#345264] cursor-pointer disabled:opacity-40"
              >
                Importar mimos
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {mimos.map((m) => (
                <div key={m.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs">
                  <div className="flex gap-3">
                  <div className="w-20 h-20 rounded-xl bg-slate-50 shrink-0 border border-slate-100 overflow-hidden flex items-center justify-center">
                    {m.imagem_url ? (
                      <img src={m.imagem_url} alt={m.nome} className="object-contain w-full h-full p-1" />
                    ) : (
                      <span>🧸</span>
                    )}
                  </div>

                  <div className="flex-1">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">{m.categoria}</span>
                    <h4 className="font-bold text-xs text-slate-800 line-clamp-1">{m.nome}</h4>
                    <span className="text-sm font-black text-[#42677D] block mt-1">
                      {m.preco_atual === null || m.preco_atual === undefined
                        ? <span className="text-[#D99A7B]">Preço a informar</span>
                        : `R$ ${Number(m.preco_atual).toFixed(2).replace(".", ",")}`}
                    </span>
                    {!m.ativo && <span className="text-[10px] font-bold text-rose-600">INATIVO</span>}

                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                      <span>Desejado: <strong>{m.stock_info?.quantidade_desejada}</strong></span>
                      <span>•</span>
                      <span>Disponível: <strong className="text-emerald-700">{m.stock_info?.disponibilidade_restante}</strong></span>
                      <span>•</span>
                      <span>Externo: <strong>{m.stock_info?.quantidade_comprada_externa}</strong></span>
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => handleUpdatePrice(m.id, "mimo", m.preco_atual ?? 0)}
                        className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold cursor-pointer"
                      >
                        {m.preco_atual == null ? "Informar Preço" : "Editar Preço"}
                      </button>
                      <button
                        onClick={() => (editingMimoId === m.id ? setEditingMimoId(null) : openMimoEditor(m))}
                        className="px-2 py-1 rounded-lg bg-[#B9D8E8] hover:bg-[#a5c8dc] text-[#42677D] text-[11px] font-bold cursor-pointer"
                      >
                        {editingMimoId === m.id ? "Fechar" : "Editar"}
                      </button>

                      {m.produto_url && (
                        <a
                          href={m.produto_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-[#42677D] hover:underline flex items-center gap-1"
                        >
                          <span>Amazon</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      )}
                    </div>
                  </div>
                  </div>

                  {editingMimoId === m.id && mimoForm && (
                    <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-2 gap-2">
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">Nome do mimo</label>
                      <input
                        type="text"
                        value={mimoForm.nome}
                        onChange={(e) => setMimoForm({ ...mimoForm, nome: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="text-[10px] font-bold text-slate-500">Categoria</label>
                      <label className="text-[10px] font-bold text-slate-500">Quantidade desejada</label>
                      <input
                        type="text"
                        value={mimoForm.categoria}
                        onChange={(e) => setMimoForm({ ...mimoForm, categoria: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <input
                        type="number"
                        min={1}
                        value={mimoForm.quantidade_desejada}
                        onChange={(e) => setMimoForm({ ...mimoForm, quantidade_desejada: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="text-[10px] font-bold text-slate-500">Compradas fora do site</label>
                      <label className="text-[10px] font-bold text-slate-500">&nbsp;</label>
                      <input
                        type="number"
                        min={0}
                        value={mimoForm.quantidade_comprada_externa}
                        onChange={(e) => setMimoForm({ ...mimoForm, quantidade_comprada_externa: e.target.value })}
                        className="px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">Link da Amazon</label>
                      <input
                        type="url"
                        value={mimoForm.produto_url}
                        onChange={(e) => setMimoForm({ ...mimoForm, produto_url: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 text-[10px] font-bold text-slate-500">URL da imagem</label>
                      <input
                        type="url"
                        value={mimoForm.imagem_url}
                        onChange={(e) => setMimoForm({ ...mimoForm, imagem_url: e.target.value })}
                        className="col-span-2 px-2 py-1.5 text-xs bg-slate-50 rounded-lg border border-slate-300"
                      />
                      <label className="col-span-2 flex items-center gap-2 text-xs font-semibold text-slate-700">
                        <input
                          type="checkbox"
                          checked={!!mimoForm.ativo}
                          onChange={(e) => setMimoForm({ ...mimoForm, ativo: e.target.checked })}
                        />
                        Mimo ativo (visível para os convidados)
                      </label>
                      <div className="col-span-2 flex gap-2 pt-1">
                        <button
                          onClick={handleSaveMimo}
                          className="px-4 py-1.5 rounded-lg bg-[#42677D] text-white text-xs font-bold cursor-pointer"
                        >
                          Salvar mimo
                        </button>
                        <button
                          onClick={() => setEditingMimoId(null)}
                          className="px-4 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-bold cursor-pointer"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= TAB: CONFIGURAÇÕES & PIX ================= */}
        {activeTab === "config" && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <h2 className="text-xl font-black text-[#42677D]">Configurações do Evento & Pix</h2>
              <p className="text-xs text-slate-500">
                Altere dados bancários, WhatsApp do casal e regras gerais sem mexer no código.
              </p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
              <div>
                <label className="block text-xs font-bold text-[#42677D] mb-1">WhatsApp do Casal (com DDD)</label>
                <input
                  type="text"
                  value={configs.whatsapp_casal || ""}
                  onChange={(e) => setConfigs({ ...configs, whatsapp_casal: e.target.value })}
                  className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">Chave Pix</label>
                  <input
                    type="text"
                    value={configs.chave_pix || ""}
                    onChange={(e) => setConfigs({ ...configs, chave_pix: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">Tipo de Chave</label>
                  <input
                    type="text"
                    value={configs.tipo_chave_pix || ""}
                    onChange={(e) => setConfigs({ ...configs, tipo_chave_pix: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">Titular da Conta</label>
                  <input
                    type="text"
                    value={configs.titular_pix || ""}
                    onChange={(e) => setConfigs({ ...configs, titular_pix: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">Instituição Financeira (Banco)</label>
                  <input
                    type="text"
                    value={configs.banco_pix || ""}
                    onChange={(e) => setConfigs({ ...configs, banco_pix: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#42677D] mb-1">Prazo Padrão de Reserva (Horas)</label>
                <input
                  type="number"
                  value={configs.prazo_padrao_horas || "72"}
                  onChange={(e) => setConfigs({ ...configs, prazo_padrao_horas: e.target.value })}
                  className="w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300"
                />
              </div>

              <div className="pt-2">
                <button
                  onClick={handleSaveConfigs}
                  disabled={isSavingConfig}
                  className="px-6 py-2.5 rounded-xl bg-[#42677D] hover:bg-[#345264] text-white text-xs font-bold shadow-xs cursor-pointer"
                >
                  {isSavingConfig ? "Salvando..." : "Salvar Configurações"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB: RELATÓRIOS & EXPORTAR ================= */}
        {activeTab === "export" && token && (
          <div className="space-y-4 max-w-2xl">
            <div>
              <h2 className="text-xl font-black text-[#42677D]">Exportação de Dados & Relatórios</h2>
              <p className="text-xs text-slate-500">Gere relatórios completos para planilha em formatos CSV e Excel.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-3">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-sm text-slate-800">Todas as Reservas</h3>
                </div>
                <p className="text-xs text-slate-500">
                  Lista completa dos números, convidados, presentes, mimos e comprovantes.
                </p>
                <div className="flex items-center gap-2 pt-2">
                  <a
                    href={getExportUrl("reservations", "csv", token)}
                    className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold"
                  >
                    Baixar CSV
                  </a>
                  <a
                    href={getExportUrl("reservations", "xlsx", token)}
                    className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-2xs"
                  >
                    Baixar Excel (.xlsx)
                  </a>
                </div>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-3">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-5 h-5 text-[#42677D]" />
                  <h3 className="font-bold text-sm text-slate-800">Relatório Financeiro Pix</h3>
                </div>
                <p className="text-xs text-slate-500">
                  Resumo das contribuições financeiras recebidas e pendentes por Pix.
                </p>
                <div className="flex items-center gap-2 pt-2">
                  <a
                    href={getExportUrl("pix", "csv", token)}
                    className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold"
                  >
                    Baixar CSV
                  </a>
                  <a
                    href={getExportUrl("pix", "xlsx", token)}
                    className="px-3 py-1.5 rounded-xl bg-[#42677D] hover:bg-[#345264] text-white text-xs font-bold shadow-2xs"
                  >
                    Baixar Excel (.xlsx)
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB: AUDITORIA ================= */}
        {activeTab === "auditoria" && (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-black text-[#42677D]">Histórico de Auditoria</h2>
              <p className="text-xs text-slate-500">Registro cronológico de todas as ações administrativas e do sistema.</p>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                      <th className="p-3">Data/Hora</th>
                      <th className="p-3">Responsável</th>
                      <th className="p-3">Ação</th>
                      <th className="p-3">Descrição Detalhada</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/70">
                        <td className="p-3 text-slate-500 whitespace-nowrap">
                          {new Date(log.criado_em).toLocaleString("pt-BR")}
                        </td>
                        <td className="p-3 font-semibold text-slate-800 whitespace-nowrap">
                          {log.administrador_nome}
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-[#42677D]">
                            {log.acao}
                          </span>
                        </td>
                        <td className="p-3 text-slate-700 leading-relaxed">
                          {log.descricao}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
