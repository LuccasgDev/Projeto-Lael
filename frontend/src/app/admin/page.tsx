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
  extendReservationApi, fetchAdminProdutos, updateAdminProdutoPrice,
  fetchAdminMimos, updateAdminMimoPrice, fetchAdminConfig,
  updateAdminConfig, fetchAuditLogs, getExportUrl,
  DashboardStats, ReservationAdminItem
} from "@/lib/api";

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [adminName, setAdminName] = useState<string>("");

  // Login form state
  const [loginEmail, setLoginEmail] = useState("admin@chaderifa.com.br");
  const [loginSenha, setLoginSenha] = useState("admin123");
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
                                {r.forma_presente === "amazon" ? "📦 Amazon" : `💸 Pix (R$ ${r.preco_presente_reserva.toFixed(2)})`}
                              </span>
                            </td>

                            <td className="p-3">
                              <span className="font-medium text-slate-800 block truncate max-w-[140px]">{r.mimo_nome}</span>
                              <span className="text-[10px] text-slate-500">
                                {r.forma_mimo === "amazon" ? "📦 Amazon" : `💸 Pix (R$ ${r.preco_mimo_reserva.toFixed(2)})`}
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

        {/* ================= TAB: PRESENTES PRINCIPAIS ================= */}
        {activeTab === "presentes" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-[#42677D]">Presentes Principais (Lista de Talia)</h2>
                <p className="text-xs text-slate-500">Gestão dos presentes vinculados aos números da rifa.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {produtos.map((p) => (
                <div key={p.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs flex gap-3">
                  <div className="w-20 h-20 rounded-xl bg-slate-50 shrink-0 border border-slate-100 overflow-hidden flex items-center justify-center">
                    {p.imagem_url ? (
                      <img src={p.imagem_url} alt={p.nome} className="object-contain w-full h-full p-1" />
                    ) : (
                      <span>🎁</span>
                    )}
                  </div>

                  <div className="flex-1">
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">{p.categoria}</span>
                    <h4 className="font-bold text-xs text-slate-800 line-clamp-1">{p.nome}</h4>
                    <span className="text-sm font-black text-[#42677D] block mt-1">
                      R$ {p.preco_atual.toFixed(2).replace(".", ",")}
                    </span>

                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => handleUpdatePrice(p.id, "produto", p.preco_atual)}
                        className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold cursor-pointer"
                      >
                        Editar Preço
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {mimos.map((m) => (
                <div key={m.id} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-2xs flex gap-3">
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
                      R$ {m.preco_atual.toFixed(2).replace(".", ",")}
                    </span>

                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                      <span>Desejado: <strong>{m.stock_info?.quantidade_desejada}</strong></span>
                      <span>•</span>
                      <span>Disponível: <strong className="text-emerald-700">{m.stock_info?.disponibilidade_restante}</strong></span>
                    </div>

                    <div className="flex items-center gap-2 mt-2">
                      <button
                        onClick={() => handleUpdatePrice(m.id, "mimo", m.preco_atual)}
                        className="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold cursor-pointer"
                      >
                        Editar Preço
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
