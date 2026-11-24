"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import confetti from "canvas-confetti";
import {
  X, Check, ArrowRight, ArrowLeft, ExternalLink,
  ShieldCheck, AlertTriangle, Copy, CheckCheck,
  Clock, MessageCircle
} from "lucide-react";
import ProductImage from "@/components/ProductImage";
import {
  NumeroDetail, Mimo, PublicConfig,
  createReservationApi, ReservationResponse
} from "@/lib/api";

interface ReservationModalProps {
  numberDetail: NumeroDetail | null;
  mimos: Mimo[];
  config: PublicConfig | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ReservationModal({
  numberDetail,
  mimos,
  config,
  isOpen,
  onClose,
  onSuccess,
}: ReservationModalProps) {
  // v2 §4: DOIS popups em sequência.
  // step 1 = Popup 1: escolha do mimo (mostra "Número 22 · Fralda P")
  // step 2 = Popup 2: resumo + formas de aquisição + identificação + Reservar
  // step 3 = confirmação/sucesso (instruções e WhatsApp)
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Selections
  const [formaPresente, setFormaPresente] = useState<"amazon" | "pix" | "local">("amazon");
  const [selectedMimoId, setSelectedMimoId] = useState<number | null>(null);
  const [formaMimo, setFormaMimo] = useState<"amazon" | "pix" | "local">("amazon");

  // Identification & LGPD
  const [nome, setNome] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [autorizaNome, setAutorizaNome] = useState(false);
  const [consentimentoLgpd, setConsentimentoLgpd] = useState(false);

  // State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [reservationResult, setReservationResult] = useState<ReservationResponse | null>(null);
  const [copiedPix, setCopiedPix] = useState(false);

  // Reset modal on open
  useEffect(() => {
    if (isOpen) {
      setStep(1);
      setFormaPresente("amazon");
      setFormaMimo("amazon");
      setNome("");
      setWhatsapp("");
      setAutorizaNome(false);
      setConsentimentoLgpd(false);
      setErrorMessage("");
      setReservationResult(null);
      setSelectedMimoId(null);
      // Mimo fixo (RN/P/G): já vem selecionado do backend — sem etapa de escolha
      if (numberDetail?.mimo_livre === false && numberDetail?.mimo_fixo) {
        setSelectedMimoId(numberDetail.mimo_fixo.id);
      }
    }
  }, [isOpen]);

  const produtoPrincipal = numberDetail?.produto_principal;
  const selectedMimo = mimos.find((m) => m.id === selectedMimoId) ?? numberDetail?.mimo_fixo ?? null;
  // Regra fixa: só a faixa M (36–65) permite escolher o mimo; RN/P/G têm mimo fixo
  const mimoLivre = numberDetail?.mimo_livre !== false;
  const mimoFixo = numberDetail?.mimo_fixo ?? null;

  // Filtro de mimos por categoria e busca (§4 v2)
  const categoriasMimos = useMemo(
    () => Array.from(new Set(mimos.map((m) => m.categoria).filter(Boolean) as string[])),
    [mimos]
  );
  const [filtroCategoriaMimo, setFiltroCategoriaMimo] = useState<string>("");
  const [buscaMimo, setBuscaMimo] = useState("");
  const [ordenacaoMimo, setOrdenacaoMimo] = useState<"padrao" | "nome" | "menor_preco" | "maior_preco">("padrao");
  const [qtdVisivel, setQtdVisivel] = useState(24); // "carregar mais" — nada fica inacessível
  const mimosFiltrados = useMemo(() => {
    const busca = buscaMimo.trim().toLowerCase();
    const lista = mimos.filter((m) => {
      if (filtroCategoriaMimo && m.categoria !== filtroCategoriaMimo) return false;
      if (busca && !m.nome.toLowerCase().includes(busca) && !(m.categoria ?? "").toLowerCase().includes(busca)) return false;
      return true;
    });
    if (ordenacaoMimo === "nome") lista.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
    if (ordenacaoMimo === "menor_preco") lista.sort((a, b) => (a.preco_atual ?? Infinity) - (b.preco_atual ?? Infinity));
    if (ordenacaoMimo === "maior_preco") lista.sort((a, b) => (b.preco_atual ?? -1) - (a.preco_atual ?? -1));
    return lista;
  }, [mimos, filtroCategoriaMimo, buscaMimo, ordenacaoMimo]);
  const mimosVisiveis = mimosFiltrados.slice(0, qtdVisivel);

  if (!isOpen || !numberDetail) return null;

  // Price calculations (RN-08 v2: preço pode ser nulo — "a consultar")
  const precoPresente = produtoPrincipal?.preco_atual ?? null;
  const precoMimo = selectedMimo?.preco_atual ?? null;
  const pixPresenteDisponivel = precoPresente !== null;
  const pixMimoDisponivel = precoMimo !== null;

  let totalPix = 0;
  if (formaPresente === "pix" && precoPresente !== null) totalPix += precoPresente;
  if (formaMimo === "pix" && precoMimo !== null) totalPix += precoMimo;

  const formatPreco = (v: number | null) =>
    v === null ? "Preço a consultar" : `R$ ${v.toFixed(2).replace(".", ",")}`;

  // WhatsApp mask handler: (85) 99999-9999
  const handleWhatsappChange = (val: string) => {
    const raw = val.replace(/\D/g, "").slice(0, 11);
    if (raw.length <= 2) {
      setWhatsapp(raw);
    } else if (raw.length <= 7) {
      setWhatsapp(`(${raw.slice(0, 2)}) ${raw.slice(2)}`);
    } else {
      setWhatsapp(`(${raw.slice(0, 2)}) ${raw.slice(2, 7)}-${raw.slice(7)}`);
    }
  };

  const handleNextStep = () => {
    setErrorMessage("");
    if (step === 1) {
      if (!selectedMimoId) {
        setErrorMessage(mimoLivre
          ? "Por favor, escolha um mimo da lista do Lucas para continuar."
          : "O mimo deste número ainda não foi configurado. Avise o casal.");
        return;
      }
      setStep(2);
      return;
    }
    if (step === 2) {
      if (formaPresente === "pix" && !pixPresenteDisponivel) {
        setErrorMessage("A fralda está sem preço definido. Escolha comprar na Amazon, em loja física, ou aguarde o casal atualizar o valor.");
        return;
      }
      if (formaMimo === "pix" && !pixMimoDisponivel) {
        setErrorMessage("Este mimo está sem preço definido. Escolha comprar na Amazon, em loja física, ou aguarde o casal atualizar o valor.");
        return;
      }
      if (!nome.trim() || nome.trim().length < 2) {
        setErrorMessage("Por favor, informe seu nome completo.");
        return;
      }
      const rawDigits = whatsapp.replace(/\D/g, "");
      if (rawDigits.length < 10) {
        setErrorMessage("Por favor, informe um WhatsApp válido com DDD.");
        return;
      }
      if (!consentimentoLgpd) {
        setErrorMessage("Você precisa concordar com o uso dos dados para organização do evento.");
        return;
      }
      handleSubmitReservation();
      return;
    }
  };

  const handleSubmitReservation = async () => {
    if (!selectedMimoId) return;
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const res = await createReservationApi({
        numero_id: numberDetail.id,
        mimo_id: selectedMimoId,
        nome_convidado: nome.trim(),
        whatsapp: whatsapp.replace(/\D/g, ""),
        autoriza_nome_publico: autorizaNome,
        forma_presente: formaPresente,
        forma_mimo: formaMimo,
        consentimento_lgpd: consentimentoLgpd,
      });

      setReservationResult(res);
      setStep(3);
      onSuccess();

      // Guarda o link secreto de acompanhamento localmente (sem login)
      if (res.token_acompanhamento) {
        try {
          localStorage.setItem("lael_tracking_token", res.token_acompanhamento);
        } catch {}
      }

      // Launch celebration confetti
      try {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ["#B9D8E8", "#D99A7B", "#A9B8A0", "#42677D"],
        });
      } catch (e) {
        // Safe fallback
      }
    } catch (err: any) {
      const msg: string = err.message || "Erro ao processar reserva. Tente novamente.";
      setErrorMessage(msg);
      // §4 v2: se algo mudou, avise e leve o convidado de volta ao popup certo
      const m = msg.toLowerCase();
      if (m.includes("mimo")) {
        setStep(1); // mimo esgotou durante o preenchimento → volta à escolha do mimo
      } else if (m.includes("não está mais disponível") || m.includes("nao esta mais disponivel")) {
        // o número foi tomado → fecha o modal e devolve o convidado à grade atualizada
        onSuccess();
        onClose();
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyPix = () => {
    if (config?.chave_pix) {
      navigator.clipboard.writeText(config.chave_pix);
      setCopiedPix(true);
      setTimeout(() => setCopiedPix(false), 3000);
    }
  };

  const tituloPopup =
    step === 1
      ? mimoLivre ? "Escolha o mimo" : "Fralda e mimo do seu número"
      : step === 2
      ? "Seus dados e pagamento"
      : "Reserva Realizada com Sucesso! 🎉";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs overflow-y-auto animate-fade-in">
      <div className="bg-[#FFF8F0] w-full max-w-xl rounded-3xl shadow-2xl border border-[#B9D8E8] overflow-hidden my-auto relative">
        {/* Modal Top Bar — mostra o número e a fralda correspondente (§4 v2) */}
        <div className="bg-gradient-to-r from-[#42677D] to-[#345264] text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
              {String(numberDetail.numero).padStart(2, "0")}
            </span>
            <div>
              <h3 className="font-bold text-sm sm:text-base leading-tight">{tituloPopup}</h3>
              <p className="text-[11px] text-[#B9D8E8]">
                {step === 3
                  ? "Envie os comprovantes pelo WhatsApp"
                  : `Número ${String(numberDetail.numero).padStart(2, "0")}${
                      produtoPrincipal ? ` · Fralda ${produtoPrincipal.tamanho || produtoPrincipal.nome}` : ""
                    }`}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Fechar"
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 sm:p-6 max-h-[75vh] max-h-[85dvh] overflow-y-auto">
          {errorMessage && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* ================= POPUP 1: ESCOLHA DO MIMO ================= */}
          {step === 1 && (
            <div className="space-y-4">
              {/* Fralda do número escolhido (identificação no topo, §4 v2) */}
              {produtoPrincipal && (
                <div className="bg-white p-3 rounded-2xl border border-[#B9D8E8]/70 shadow-2xs flex items-center gap-3">
                  <ProductImage
                    src={produtoPrincipal.imagem_url}
                    alt={produtoPrincipal.nome}
                    fallback="🎁"
                    className="w-14 h-14 rounded-xl shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[#D99A7B] block">
                      Tamanho {produtoPrincipal.tamanho || "—"}
                    </span>
                    <h4 className="font-bold text-xs text-[#29343A] line-clamp-1">{produtoPrincipal.nome}</h4>
                    <span className="text-[11px] text-[#42677D] font-semibold">{formatPreco(precoPresente)}</span>
                  </div>
                </div>
              )}

              <div>
                <h4 className="font-bold text-sm text-[#42677D] mb-1">
                  {mimoLivre
                    ? "Agora escolha um mimo da lista do Lucas"
                    : "Mimo correspondente ao seu número"}
                </h4>
                <p className="text-xs text-slate-600 mb-3">
                  {mimoLivre
                    ? "O mimo não fica preso ao número: escolha o que mais quiser entre os disponíveis."
                    : "Nos tamanhos RN, P e G, o mimo já vem definido pela faixa do número — ele ajuda a montar o enxoval do Lael."}
                </p>
              </div>

              {/* Mimo FIXO (RN/P/G): sem lista de escolha — mostra o mimo da regra */}
              {!mimoLivre && mimoFixo && (
                <div className="bg-white p-3 rounded-2xl border-2 border-[#42677D]/40 shadow-2xs flex items-center gap-3">
                  <ProductImage
                    src={mimoFixo.imagem_url}
                    alt={mimoFixo.nome}
                    fallback="🧸"
                    className="w-14 h-14 rounded-xl shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <span className="text-[10px] uppercase font-bold tracking-wider text-[#A9B8A0] block">
                      Mimo incluído no número
                    </span>
                    <h4 className="font-bold text-xs text-[#29343A] line-clamp-1">{mimoFixo.nome}</h4>
                    <span className="text-[11px] font-extrabold text-[#42677D]">
                      {formatPreco(mimoFixo.preco_atual)}
                    </span>
                  </div>
                  <div className="w-6 h-6 rounded-full bg-[#42677D] text-white flex items-center justify-center shrink-0">
                    <Check className="w-3.5 h-3.5" />
                  </div>
                </div>
              )}

              {/* Filtro por categoria + busca (§4 v2) — apenas quando o mimo é livre (faixa M) */}
              {mimoLivre && (<>
              <div className="space-y-2">
                <input
                  type="text"
                  placeholder="Buscar mimo por nome ou categoria..."
                  value={buscaMimo}
                  onChange={(e) => { setBuscaMimo(e.target.value); setQtdVisivel(24); }}
                  aria-label="Buscar mimo por nome ou categoria"
                  className="w-full px-3 py-2 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
                />
                {categoriasMimos.length > 0 && (
                  <div className="flex gap-1.5 overflow-x-auto pb-1">
                    <button
                      type="button"
                      onClick={() => { setFiltroCategoriaMimo(""); setQtdVisivel(24); }}
                      className={`px-2.5 py-1 rounded-full text-[10px] font-bold whitespace-nowrap cursor-pointer ${
                        filtroCategoriaMimo === "" ? "bg-[#42677D] text-white" : "bg-white text-[#42677D] border border-[#B9D8E8]"
                      }`}
                    >
                      Todas
                    </button>
                    {categoriasMimos.map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => { setFiltroCategoriaMimo(cat); setQtdVisivel(24); }}
                        className={`px-2.5 py-1 rounded-full text-[10px] font-bold whitespace-nowrap cursor-pointer ${
                          filtroCategoriaMimo === cat ? "bg-[#42677D] text-white" : "bg-white text-[#42677D] border border-[#B9D8E8]"
                        }`}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] text-slate-500" aria-live="polite">
                    {mimosFiltrados.length} mimo{mimosFiltrados.length === 1 ? "" : "s"} encontrado{mimosFiltrados.length === 1 ? "" : "s"} de {mimos.length} do catálogo
                  </span>
                  <select
                    value={ordenacaoMimo}
                    onChange={(e) => setOrdenacaoMimo(e.target.value as any)}
                    aria-label="Ordenar mimos"
                    className="px-2 py-1 text-[10px] bg-white rounded-lg border border-[#B9D8E8] text-[#42677D] font-bold"
                  >
                    <option value="padrao">Ordem da lista</option>
                    <option value="nome">Nome (A–Z)</option>
                    <option value="menor_preco">Menor preço</option>
                    <option value="maior_preco">Maior preço</option>
                  </select>
                </div>
              </div>

              {/* Lista de mimos */}
              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {mimosVisiveis.length === 0 && (
                  <p className="text-xs text-slate-500 text-center py-6">
                    Nenhum mimo encontrado com esse filtro.
                  </p>
                )}
                {mimosVisiveis.map((mimo) => {
                  const isSelected = selectedMimoId === mimo.id;
                  const isEsgotado = mimo.disponibilidade_restante <= 0;

                  return (
                    <div
                      key={mimo.id}
                      onClick={() => {
                        if (!isEsgotado) setSelectedMimoId(mimo.id);
                      }}
                      className={`p-3 rounded-2xl border-2 transition-all flex items-center justify-between gap-3 ${
                        isEsgotado
                          ? "bg-slate-100 border-slate-200 opacity-50 cursor-not-allowed"
                          : isSelected
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs cursor-pointer"
                          : "bg-white/70 border-slate-200 hover:bg-white cursor-pointer"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <ProductImage
                          src={mimo.imagem_url}
                          alt={mimo.nome}
                          fallback="🧸"
                          className="w-12 h-12 rounded-xl shrink-0"
                        />

                        <div>
                          <div className="flex items-center gap-1.5">
                            <h5 className="font-bold text-xs text-[#29343A] leading-tight line-clamp-1">
                              {mimo.nome}
                            </h5>
                            {isEsgotado && (
                              <span className="text-[9px] bg-rose-100 text-rose-800 font-bold px-1.5 py-0.5 rounded-full">
                                Esgotado
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] font-extrabold text-[#42677D] block">
                            {formatPreco(mimo.preco_atual)}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {mimo.disponibilidade_restante} restante{mimo.disponibilidade_restante === 1 ? "" : "s"}
                          </span>
                        </div>
                      </div>

                      <div className="shrink-0">
                        {isSelected && !isEsgotado && (
                          <div className="w-6 h-6 rounded-full bg-[#42677D] text-white flex items-center justify-center">
                            <Check className="w-3.5 h-3.5" />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* "Carregar mais": paginação incremental — o catálogo inteiro continua acessível */}
              {mimosFiltrados.length > mimosVisiveis.length && (
                <button
                  type="button"
                  onClick={() => setQtdVisivel((q) => q + 24)}
                  className="w-full py-2 rounded-xl bg-white border border-[#B9D8E8] text-[11px] font-bold text-[#42677D] hover:bg-[#B9D8E8]/20 cursor-pointer"
                >
                  Carregar mais ({mimosFiltrados.length - mimosVisiveis.length} restantes)
                </button>
              )}
              </>)}
            </div>
          )}

          {/* ================= POPUP 2: DADOS E PAGAMENTO (tudo na mesma tela) ================= */}
          {step === 2 && (
            <div className="space-y-4">
              {/* Resumo: fralda + mimo, com botão para trocar o mimo (§4 v2) */}
              <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-2xs space-y-3">
                {produtoPrincipal && (
                  <div className="flex items-start gap-3 pb-3 border-b border-slate-100">
                    <div className="w-16 h-16 rounded-xl bg-slate-50 shrink-0 border border-slate-100 flex items-center justify-center overflow-hidden">
                      {produtoPrincipal.imagem_url ? (
                        <img src={produtoPrincipal.imagem_url} alt={produtoPrincipal.nome} className="object-contain w-full h-full p-1" />
                      ) : (
                        <span className="text-2xl">🎁</span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-[#42677D] bg-[#B9D8E8]/30 px-2 py-0.5 rounded-full inline-block mb-1">
                        Número {String(numberDetail.numero).padStart(2, "0")} · Tamanho {produtoPrincipal.tamanho || "—"}
                      </span>
                      <h4 className="font-bold text-sm text-[#29343A] leading-snug">{produtoPrincipal.nome}</h4>
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm font-black text-[#42677D]">{formatPreco(precoPresente)}</span>
                        {produtoPrincipal.preco_anterior && (
                          <span className="text-[11px] text-slate-400 line-through">
                            R$ {produtoPrincipal.preco_anterior.toFixed(2).replace(".", ",")}
                          </span>
                        )}
                      </div>
                      {produtoPrincipal.preco_sincronizado_em && (
                        <span className="text-[10px] text-slate-400 block">
                          Preço verificado em: {new Date(produtoPrincipal.preco_sincronizado_em).toLocaleDateString("pt-BR")}
                        </span>
                      )}
                      {produtoPrincipal.produto_url && (
                        <a
                          href={produtoPrincipal.produto_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#42677D] hover:text-[#D99A7B] mt-0.5 underline"
                        >
                          <span>Ver na Amazon</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                )}

                {/* Mimo (fixo ou escolhido) + botão para trocar — só na faixa M */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-slate-50 shrink-0 border border-slate-100 flex items-center justify-center overflow-hidden">
                      {selectedMimo?.imagem_url ? (
                        <img src={selectedMimo.imagem_url} alt={selectedMimo.nome} className="object-contain w-full h-full p-1" />
                      ) : (
                        <span className="text-lg">🧸</span>
                      )}
                    </div>
                    <div className="min-w-0">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">
                        {mimoLivre ? "Mimo escolhido" : "Mimo do número"}
                      </span>
                      <span className="text-xs font-bold text-[#29343A] block line-clamp-1">{selectedMimo?.nome}</span>
                      <span className="text-[11px] font-extrabold text-[#42677D]">{formatPreco(precoMimo)}</span>
                    </div>
                  </div>
                  {mimoLivre && (
                    <button
                      type="button"
                      onClick={() => { setErrorMessage(""); setStep(1); }}
                      className="shrink-0 px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-[11px] font-bold text-slate-700 cursor-pointer"
                    >
                      Trocar mimo
                    </button>
                  )}
                </div>
              </div>

              {/* Forma de aquisição da fralda (RN-04) */}
              <div className="bg-[#B9D8E8]/20 p-4 rounded-2xl border border-[#B9D8E8]/50">
                <span className="text-xs font-bold text-[#42677D] block mb-2">
                  Fralda — como você prefere presentear?
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setFormaPresente("amazon")}
                    className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer flex flex-col justify-between ${
                      formaPresente === "amazon"
                        ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                        : "bg-white/60 border-slate-200 hover:bg-white"
                    }`}
                  >
                    <div>
                      <span className="text-lg block mb-1">📦</span>
                      <span className="text-xs font-bold text-[#42677D] block leading-tight">Comprar na Amazon</span>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">Você compra e entrega ou envia</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setFormaPresente("local")}
                    className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer flex flex-col justify-between ${
                      formaPresente === "local"
                        ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                        : "bg-white/60 border-slate-200 hover:bg-white"
                    }`}
                  >
                    <div>
                      <span className="text-lg block mb-1">🛍️</span>
                      <span className="text-xs font-bold text-[#42677D] block leading-tight">Comprar localmente</span>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">Você compra em loja física e entrega</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => pixPresenteDisponivel && setFormaPresente("pix")}
                    disabled={!pixPresenteDisponivel}
                    className={`p-3 rounded-xl border-2 text-left transition-all flex flex-col justify-between ${
                      formaPresente === "pix" && pixPresenteDisponivel
                        ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                        : "bg-white/60 border-slate-200 hover:bg-white"
                    } ${pixPresenteDisponivel ? "cursor-pointer" : "opacity-50 cursor-not-allowed"}`}
                  >
                    <div>
                      <span className="text-lg block mb-1">💸</span>
                      <span className="text-xs font-bold text-[#42677D] block leading-tight">Enviar via Pix</span>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">
                      {pixPresenteDisponivel
                        ? `R$ ${precoPresente?.toFixed(2).replace(".", ",")}`
                        : "Preço indisponível"}
                    </span>
                  </button>
                </div>
              </div>

              {/* Forma de aquisição do mimo (RN-04) */}
              {selectedMimo && (
                <div className="bg-[#B9D8E8]/20 p-4 rounded-2xl border border-[#B9D8E8]/50">
                  <span className="text-xs font-bold text-[#42677D] block mb-2">
                    Mimo &ldquo;{selectedMimo.nome}&rdquo; — como você prefere presentear?
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    <button
                      type="button"
                      onClick={() => setFormaMimo("amazon")}
                      className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer flex flex-col justify-between ${
                        formaMimo === "amazon"
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                          : "bg-white/60 border-slate-200 hover:bg-white"
                      }`}
                    >
                      <div>
                        <span className="text-lg block mb-1">📦</span>
                        <span className="text-xs font-bold text-[#42677D] block leading-tight">Comprar na Amazon</span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">Você adquire pelo link</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setFormaMimo("local")}
                      className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer flex flex-col justify-between ${
                        formaMimo === "local"
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                          : "bg-white/60 border-slate-200 hover:bg-white"
                      }`}
                    >
                      <div>
                        <span className="text-lg block mb-1">🛍️</span>
                        <span className="text-xs font-bold text-[#42677D] block leading-tight">Comprar localmente</span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">Você compra em loja física e entrega</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => pixMimoDisponivel && setFormaMimo("pix")}
                      disabled={!pixMimoDisponivel}
                      className={`p-3 rounded-xl border-2 text-left transition-all flex flex-col justify-between ${
                        formaMimo === "pix" && pixMimoDisponivel
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                          : "bg-white/60 border-slate-200 hover:bg-white"
                      } ${pixMimoDisponivel ? "cursor-pointer" : "opacity-50 cursor-not-allowed"}`}
                    >
                      <div>
                        <span className="text-lg block mb-1">💸</span>
                        <span className="text-xs font-bold text-[#42677D] block leading-tight">Enviar via Pix</span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1.5 leading-tight">
                        {pixMimoDisponivel
                          ? `R$ ${precoMimo?.toFixed(2).replace(".", ",")}`
                          : "Preço indisponível"}
                      </span>
                    </button>
                  </div>
                </div>
              )}

              {/* Total Pix + dados do Pix (§4 v2: titular, instituição e chave) */}
              <div className="pt-2 flex items-center justify-between bg-[#B9D8E8]/20 p-4 rounded-2xl">
                <div>
                  <span className="text-xs font-bold text-[#42677D] block">Total a transferir por Pix:</span>
                  <span className="text-[10px] text-slate-500">
                    {totalPix === 0
                      ? formaPresente === "amazon" && formaMimo === "amazon"
                        ? "Nenhum valor em Pix (ambos na Amazon)"
                        : formaPresente === "local" && formaMimo === "local"
                        ? "Nenhum valor em Pix (ambos em loja física)"
                        : formaPresente === "pix" || formaMimo === "pix"
                        ? "Nenhum valor em Pix"
                        : "Nenhum valor em Pix (compras presenciais / online)"
                      : formaPresente === "pix" && formaMimo === "pix"
                      ? "Fralda + Mimo"
                      : formaPresente === "pix"
                      ? "Apenas a fralda"
                      : "Apenas o mimo"}
                  </span>
                </div>
                <span className="text-xl font-black text-[#42677D]">
                  R$ {totalPix.toFixed(2).replace(".", ",")}
                </span>
              </div>

              {totalPix > 0 && config && (
                <div className="bg-white p-3 rounded-2xl border border-emerald-200 text-left">
                  <div className="text-[11px] text-slate-600 space-y-0.5">
                    <div><strong>Titular:</strong> {config.titular_pix}</div>
                    <div><strong>Instituição:</strong> {config.banco_pix}</div>
                  </div>
                  <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200 mt-2">
                    <code className="text-xs text-[#42677D] font-mono truncate mr-2">{config.chave_pix}</code>
                    <button
                      type="button"
                      onClick={handleCopyPix}
                      className="px-2.5 py-1 rounded-lg bg-[#42677D] text-white text-[11px] font-bold flex items-center gap-1 hover:bg-[#345264] transition-colors shrink-0 cursor-pointer"
                    >
                      {copiedPix ? <CheckCheck className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedPix ? "Copiado!" : "Copiar Chave"}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Identificação (§4 v2, mesma tela) */}
              <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-2xs space-y-3">
                <div>
                  <h4 className="font-bold text-sm text-[#42677D] mb-1">Identificação do Convidado</h4>
                  <p className="text-xs text-slate-600">
                    Para o casal identificar sua reserva com carinho:
                  </p>
                </div>

                <div>
                  <label htmlFor="nome-convidado" className="block text-xs font-bold text-[#42677D] mb-1">
                    Seu Nome Completo *
                  </label>
                  <input
                    id="nome-convidado"
                    type="text"
                    placeholder="Ex: Maria Clara Silva"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
                  />
                </div>

                <div>
                  <label htmlFor="whatsapp-convidado" className="block text-xs font-bold text-[#42677D] mb-1">
                    Seu WhatsApp (com DDD) *
                  </label>
                  <input
                    id="whatsapp-convidado"
                    type="tel"
                    placeholder="(85) 99999-9999"
                    value={whatsapp}
                    onChange={(e) => handleWhatsappChange(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
                  />
                </div>

                <div className="pt-1">
                  <label className="flex items-start gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={consentimentoLgpd}
                      onChange={(e) => setConsentimentoLgpd(e.target.checked)}
                      className="w-4 h-4 mt-0.5 rounded-md border-slate-300 text-[#42677D] focus:ring-[#42677D] cursor-pointer"
                    />
                    <span className="text-[11px] text-slate-600 leading-snug">
                      Autorizo o uso do meu nome e telefone <strong>exclusivamente</strong> para a organização e conferência do Chá Rifa do Lael, em conformidade com a LGPD (texto v1, consentimento registrado com data). *
                    </span>
                  </label>
                </div>

                <div>
                  <label className="flex items-start gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={autorizaNome}
                      onChange={(e) => setAutorizaNome(e.target.checked)}
                      className="w-4 h-4 mt-0.5 rounded-md border-slate-300 text-[#42677D] focus:ring-[#42677D] cursor-pointer"
                    />
                    <span className="text-[11px] text-slate-600 leading-snug">
                      Autorizo exibir meu primeiro nome na grade pública do site (opcional).
                    </span>
                  </label>
                </div>
              </div>

              {/* Botão Reservar (§4 v2) */}
              <button
                type="button"
                onClick={handleNextStep}
                disabled={isSubmitting}
                className="w-full py-4 px-6 rounded-2xl bg-[#42677D] hover:bg-[#345264] text-white font-extrabold text-sm shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60"
              >
                {isSubmitting ? (
                  <span>Reservando...</span>
                ) : (
                  <>
                    <span>Reservar</span>
                    <Check className="w-4 h-4" />
                  </>
                )}
              </button>

              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
                <Clock className="w-4 h-4 shrink-0 text-amber-600" />
                <span>
                  Após reservar seu número, você terá <strong>72 horas</strong> para enviar os comprovantes pelo WhatsApp — referentes à fralda e ao mimo — para que o casal possa confirmar sua participação.
                </span>
              </div>
            </div>
          )}

          {/* ================= SUCESSO E WHATSAPP ================= */}
          {step === 3 && reservationResult && (
            <div className="space-y-5 text-center py-2">
              <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto text-2xl shadow-inner">
                👶
              </div>

              <div>
                <h4 className="text-xl font-extrabold text-[#42677D]">
                  Número #{String(reservationResult.numero).padStart(2, "0")} Reservado!
                </h4>
                <p className="text-xs text-slate-600 max-w-sm mx-auto mt-1">
                  Parabéns, {reservationResult.nome_convidado}! Seu número está temporariamente bloqueado para você por <strong>72 horas</strong>.
                </p>
              </div>

              {/* Pix Info Box (if applicable) */}
              {reservationResult.valor_pix_total > 0 && config && (
                <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-xs text-left max-w-md mx-auto">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-[#42677D]">Dados para o Pix:</span>
                    <span className="text-xs font-black text-emerald-700">
                      R$ {reservationResult.valor_pix_total.toFixed(2).replace(".", ",")}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-1 mb-3">
                    <div><strong>Titular:</strong> {config.titular_pix} ({config.banco_pix})</div>
                    <div><strong>Tipo de Chave:</strong> {config.tipo_chave_pix}</div>
                  </div>

                  <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <code className="text-xs text-[#42677D] font-mono truncate mr-2">
                      {config.chave_pix}
                    </code>
                    <button
                      type="button"
                      onClick={handleCopyPix}
                      className="px-2.5 py-1 rounded-lg bg-[#42677D] text-white text-[11px] font-bold flex items-center gap-1 hover:bg-[#345264] transition-colors shrink-0 cursor-pointer"
                    >
                      {copiedPix ? <CheckCheck className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedPix ? "Copiado!" : "Copiar Chave"}</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Instructions */}
              <div className="bg-emerald-50/70 p-3.5 rounded-2xl border border-emerald-200 text-xs text-emerald-950 text-left space-y-1 max-w-md mx-auto">
                <strong>Próximo passo obrigatório:</strong>
                <p className="text-[11px] text-emerald-900 leading-relaxed">
                  Clique no botão abaixo para abrir a conversa no WhatsApp com Talia e Lucas. A mensagem já estará pronta com seu número, o tamanho da fralda e o mimo! Basta anexar os comprovantes dos dois produtos.
                </p>
              </div>

              {/* WhatsApp CTA Button */}
              <a
                href={reservationResult.whatsapp_link}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full py-4 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-sm sm:text-base shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                <MessageCircle className="w-5 h-5 fill-white" />
                <span>Enviar Comprovantes no WhatsApp</span>
              </a>

              {/* Acompanhamento sem login (link secreto) */}
              {reservationResult.token_acompanhamento && (
                <Link
                  href={`/acompanhamento?t=${encodeURIComponent(reservationResult.token_acompanhamento)}`}
                  className="block text-xs font-semibold text-[#42677D] underline underline-offset-2 hover:text-[#345264]"
                >
                  Guarde este link: acompanhe o status da sua reserva aqui
                </Link>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        {step < 3 && (
          <div className="bg-white p-4 border-t border-slate-100 flex items-center justify-between">
            {step === 2 ? (
              <button
                type="button"
                onClick={() => { setErrorMessage(""); setStep(1); }}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors flex items-center gap-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Voltar ao mimo
              </button>
            ) : (
              <div></div>
            )}

            {step === 1 && (
              <button
                type="button"
                onClick={handleNextStep}
                className="px-6 py-2.5 rounded-xl bg-[#42677D] text-white text-xs font-bold shadow-xs hover:bg-[#345264] transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <span>Avançar</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="bg-white p-4 border-t border-slate-100 text-center">
            <button
              type="button"
              onClick={onClose}
              className="text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
            >
              Fechar janela e voltar à grade
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
