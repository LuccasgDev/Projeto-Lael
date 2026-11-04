"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import confetti from "canvas-confetti";
import {
  X, Check, ArrowRight, ArrowLeft, ExternalLink,
  ShieldCheck, AlertTriangle, Copy, CheckCheck,
  Sparkles, Clock, Heart, Send, MessageCircle
} from "lucide-react";
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
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);

  // Selections
  const [formaPresente, setFormaPresente] = useState<"amazon" | "pix">("amazon");
  const [selectedMimoId, setSelectedMimoId] = useState<number | null>(null);
  const [formaMimo, setFormaMimo] = useState<"amazon" | "pix">("amazon");

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

      // Auto-select first available mimo
      const firstAvailable = mimos.find((m) => m.disponibilidade_restante > 0);
      if (firstAvailable) {
        setSelectedMimoId(firstAvailable.id);
      }
    }
  }, [isOpen, mimos]);

  if (!isOpen || !numberDetail) return null;

  const produtoPrincipal = numberDetail.produto_principal;
  const selectedMimo = mimos.find((m) => m.id === selectedMimoId);

  // Price calculations
  const precoPresente = produtoPrincipal ? produtoPrincipal.preco_atual : 0;
  const precoMimo = selectedMimo ? selectedMimo.preco_atual : 0;

  let totalPix = 0;
  if (formaPresente === "pix") totalPix += precoPresente;
  if (formaMimo === "pix") totalPix += precoMimo;

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
    if (step === 2 && !selectedMimoId) {
      setErrorMessage("Por favor, selecione um mimo da lista.");
      return;
    }
    if (step === 4) {
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
    setStep((prev) => (prev + 1) as any);
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
      setStep(5);
      onSuccess();

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
      setErrorMessage(err.message || "Erro ao processar reserva. Tente novamente.");
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-xs overflow-y-auto animate-fade-in">
      <div className="bg-[#FFF8F0] w-full max-w-xl rounded-3xl shadow-2xl border border-[#B9D8E8] overflow-hidden my-auto relative">
        {/* Modal Top Bar */}
        <div className="bg-gradient-to-r from-[#42677D] to-[#345264] text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-sm font-bold">
              {String(numberDetail.numero).padStart(2, "0")}
            </span>
            <div>
              <h3 className="font-bold text-sm sm:text-base leading-tight">
                {step === 5 ? "Reserva Realizada com Sucesso! 🎉" : `Reservar Número ${String(numberDetail.numero).padStart(2, "0")}`}
              </h3>
              <p className="text-[11px] text-[#B9D8E8]">
                {step === 1 && "Etapa 1 de 4: Presente Principal"}
                {step === 2 && "Etapa 2 de 4: Mimo Complementar"}
                {step === 3 && "Etapa 3 de 4: Resumo das Escolhas"}
                {step === 4 && "Etapa 4 de 4: Seus Dados e WhatsApp"}
                {step === 5 && "Envie os comprovantes pelo WhatsApp"}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Progress Bar */}
        {step < 5 && (
          <div className="w-full bg-[#B9D8E8]/40 h-1.5 flex">
            <div
              className="bg-[#D99A7B] h-full transition-all duration-300"
              style={{ width: `${(step / 4) * 100}%` }}
            ></div>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-4 sm:p-6 max-h-[75vh] overflow-y-auto">
          {errorMessage && (
            <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* ================= ETAPA 1: PRESENTE PRINCIPAL ================= */}
          {step === 1 && produtoPrincipal && (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8]/70 shadow-2xs flex flex-col sm:flex-row gap-4 items-center">
                <div className="w-24 h-24 sm:w-28 sm:h-28 relative rounded-xl overflow-hidden bg-slate-50 shrink-0 border border-slate-100 flex items-center justify-center">
                  {produtoPrincipal.imagem_url ? (
                    <img
                      src={produtoPrincipal.imagem_url}
                      alt={produtoPrincipal.nome}
                      className="object-contain w-full h-full p-2"
                    />
                  ) : (
                    <span className="text-3xl">🎁</span>
                  )}
                </div>

                <div className="flex-1 text-center sm:text-left">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-[#42677D] bg-[#B9D8E8]/30 px-2 py-0.5 rounded-full inline-block mb-1">
                    {produtoPrincipal.categoria || "Presente Principal"}
                  </span>
                  <h4 className="font-bold text-sm sm:text-base text-[#29343A] leading-snug mb-1">
                    {produtoPrincipal.nome}
                  </h4>
                  <p className="text-xs text-slate-500 line-clamp-2 mb-2">
                    {produtoPrincipal.descricao}
                  </p>

                  <div className="flex items-baseline justify-center sm:justify-start gap-2">
                    <span className="text-lg font-black text-[#42677D]">
                      R$ {precoPresente.toFixed(2).replace(".", ",")}
                    </span>
                    {produtoPrincipal.preco_anterior && (
                      <span className="text-xs text-slate-400 line-through">
                        R$ {produtoPrincipal.preco_anterior.toFixed(2).replace(".", ",")}
                      </span>
                    )}
                  </div>

                  {produtoPrincipal.preco_sincronizado_em && (
                    <span className="text-[10px] text-slate-400 block mt-0.5">
                      Preço verificado em: {new Date(produtoPrincipal.preco_sincronizado_em).toLocaleDateString("pt-BR")}
                    </span>
                  )}

                  {produtoPrincipal.produto_url && (
                    <a
                      href={produtoPrincipal.produto_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#42677D] hover:text-[#D99A7B] mt-1.5 underline"
                    >
                      <span>Ver produto na Amazon</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>

              {/* INDEPENDENT ACQUISITION CHOICE FOR PRESENTE */}
              <div className="bg-[#B9D8E8]/20 p-4 rounded-2xl border border-[#B9D8E8]/50">
                <span className="text-xs font-bold text-[#42677D] block mb-2">
                  Como você prefere presentear o item principal?
                </span>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setFormaPresente("amazon")}
                    className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer ${
                      formaPresente === "amazon"
                        ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                        : "bg-white/60 border-slate-200 hover:bg-white"
                    }`}
                  >
                    <span className="text-lg block mb-1">📦</span>
                    <span className="text-xs font-bold text-[#42677D] block">Comprar na Amazon</span>
                    <span className="text-[10px] text-slate-500">Você compra e entrega ou envia</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setFormaPresente("pix")}
                    className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer ${
                      formaPresente === "pix"
                        ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                        : "bg-white/60 border-slate-200 hover:bg-white"
                    }`}
                  >
                    <span className="text-lg block mb-1">💸</span>
                    <span className="text-xs font-bold text-[#42677D] block">Enviar via Pix</span>
                    <span className="text-[10px] text-slate-500">
                      R$ {precoPresente.toFixed(2).replace(".", ",")}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ================= ETAPA 2: MIMO COMPLEMENTAR ================= */}
          {step === 2 && (
            <div className="space-y-4">
              <div>
                <h4 className="font-bold text-sm text-[#42677D] mb-1">
                  Escolha um Mimo Complementar para o Lael
                </h4>
                <p className="text-xs text-slate-600 mb-3">
                  Selecione um dos mimos disponíveis da lista de desejos:
                </p>
              </div>

              {/* Mimos Card Selection List */}
              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {mimos.map((mimo) => {
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
                        <div className="w-12 h-12 rounded-xl bg-slate-50 shrink-0 border border-slate-100 flex items-center justify-center overflow-hidden">
                          {mimo.imagem_url ? (
                            <img src={mimo.imagem_url} alt={mimo.nome} className="object-contain w-full h-full p-1" />
                          ) : (
                            <span className="text-xl">🧸</span>
                          )}
                        </div>

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
                            R$ {mimo.preco_atual.toFixed(2).replace(".", ",")}
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

              {/* INDEPENDENT ACQUISITION CHOICE FOR MIMO */}
              {selectedMimo && (
                <div className="bg-[#B9D8E8]/20 p-4 rounded-2xl border border-[#B9D8E8]/50 mt-4">
                  <span className="text-xs font-bold text-[#42677D] block mb-2">
                    Como você prefere presentear o mimo &ldquo;{selectedMimo.nome}&rdquo;?
                  </span>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setFormaMimo("amazon")}
                      className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer ${
                        formaMimo === "amazon"
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                          : "bg-white/60 border-slate-200 hover:bg-white"
                      }`}
                    >
                      <span className="text-lg block mb-1">📦</span>
                      <span className="text-xs font-bold text-[#42677D] block">Comprar na Amazon</span>
                      <span className="text-[10px] text-slate-500">Você adquire pelo link</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setFormaMimo("pix")}
                      className={`p-3 rounded-xl border-2 text-left transition-all cursor-pointer ${
                        formaMimo === "pix"
                          ? "bg-white border-[#42677D] ring-2 ring-[#42677D]/20 shadow-xs"
                          : "bg-white/60 border-slate-200 hover:bg-white"
                      }`}
                    >
                      <span className="text-lg block mb-1">💸</span>
                      <span className="text-xs font-bold text-[#42677D] block">Enviar via Pix</span>
                      <span className="text-[10px] text-slate-500">
                        R$ {precoMimo.toFixed(2).replace(".", ",")}
                      </span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================= ETAPA 3: RESUMO ================= */}
          {step === 3 && (
            <div className="space-y-4">
              <h4 className="font-bold text-sm text-[#42677D] mb-2">
                Resumo da sua Contribuição
              </h4>

              <div className="bg-white p-4 rounded-2xl border border-[#B9D8E8] shadow-2xs space-y-3">
                {/* Number */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <span className="text-xs text-slate-500">Número Selecionado:</span>
                  <span className="text-sm font-extrabold text-[#42677D]">
                    #{String(numberDetail.numero).padStart(2, "0")}
                  </span>
                </div>

                {/* Presente */}
                <div className="flex items-start justify-between pb-2 border-b border-slate-100 gap-2">
                  <div>
                    <span className="text-xs font-bold text-[#29343A] block">
                      {produtoPrincipal?.nome}
                    </span>
                    <span className="text-[11px] text-[#42677D] font-medium">
                      Forma: {formaPresente === "amazon" ? "📦 Comprar na Amazon" : "💸 Enviar via Pix"}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-slate-700 shrink-0">
                    R$ {precoPresente.toFixed(2).replace(".", ",")}
                  </span>
                </div>

                {/* Mimo */}
                <div className="flex items-start justify-between pb-2 border-b border-slate-100 gap-2">
                  <div>
                    <span className="text-xs font-bold text-[#29343A] block">
                      {selectedMimo?.nome}
                    </span>
                    <span className="text-[11px] text-[#42677D] font-medium">
                      Forma: {formaMimo === "amazon" ? "📦 Comprar na Amazon" : "💸 Enviar via Pix"}
                    </span>
                  </div>
                  <span className="text-xs font-bold text-slate-700 shrink-0">
                    R$ {precoMimo.toFixed(2).replace(".", ",")}
                  </span>
                </div>

                {/* Pix Total Highlight */}
                <div className="pt-2 flex items-center justify-between bg-[#B9D8E8]/20 -mx-4 -mb-4 p-4 rounded-b-2xl">
                  <div>
                    <span className="text-xs font-bold text-[#42677D] block">
                      Total a transferir por Pix:
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {totalPix === 0
                        ? "Nenhum valor em Pix (ambos na Amazon)"
                        : formaPresente === "pix" && formaMimo === "pix"
                        ? "Presente + Mimo"
                        : formaPresente === "pix"
                        ? "Apenas Presente Principal"
                        : "Apenas Mimo"}
                    </span>
                  </div>
                  <span className="text-xl font-black text-[#42677D]">
                    R$ {totalPix.toFixed(2).replace(".", ",")}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
                <Clock className="w-4 h-4 shrink-0 text-amber-600" />
                <span>
                  Após confirmar, você terá <strong>72 horas</strong> para enviar os comprovantes.
                </span>
              </div>
            </div>
          )}

          {/* ================= ETAPA 4: IDENTIFICAÇÃO E LGPD ================= */}
          {step === 4 && (
            <div className="space-y-4">
              <div>
                <h4 className="font-bold text-sm text-[#42677D] mb-1">
                  Identificação do Convidado
                </h4>
                <p className="text-xs text-slate-600 mb-3">
                  Informe seus dados para o casal identificar sua reserva com carinho:
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">
                    Seu Nome Completo *
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: Maria Clara Silva"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#42677D] mb-1">
                    Seu WhatsApp (com DDD) *
                  </label>
                  <input
                    type="tel"
                    placeholder="(85) 99999-9999"
                    value={whatsapp}
                    onChange={(e) => handleWhatsappChange(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
                  />
                </div>

                {/* LGPD Consent Checkbox */}
                <div className="pt-2">
                  <label className="flex items-start gap-2.5 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={consentimentoLgpd}
                      onChange={(e) => setConsentimentoLgpd(e.target.checked)}
                      className="w-4 h-4 mt-0.5 rounded-md border-slate-300 text-[#42677D] focus:ring-[#42677D] cursor-pointer"
                    />
                    <span className="text-[11px] text-slate-600 leading-snug">
                      Autorizo o uso do meu nome e telefone <strong>exclusivamente</strong> para a organização e conferência do Chá de Rifa do Lael, em conformidade com a LGPD. *
                    </span>
                  </label>
                </div>

                {/* Public Name Display Toggle */}
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
            </div>
          )}

          {/* ================= ETAPA 5: SUCESSO E WHATSAPP ================= */}
          {step === 5 && reservationResult && (
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
                    <div><strong>Favorecido:</strong> {config.titular_pix} ({config.banco_pix})</div>
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
              <div className="bg-emerald-50/70 p-3.5 rounded-2xl border border-emerald-200 text-xs text-emerald-950 text-left space-y-1">
                <strong>Próximo passo obrigatório:</strong>
                <p className="text-[11px] text-emerald-900 leading-relaxed">
                  Clique no botão abaixo para abrir a conversa no WhatsApp com Talia e Lucas. A mensagem já estará pronta com seu número e escolhas! Basta anexar os comprovantes.
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
            </div>
          )}
        </div>

        {/* Modal Footer Controls */}
        {step < 5 && (
          <div className="bg-white p-4 border-t border-slate-100 flex items-center justify-between">
            {step > 1 ? (
              <button
                type="button"
                onClick={() => setStep((prev) => (prev - 1) as any)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100 transition-colors flex items-center gap-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Voltar
              </button>
            ) : (
              <div></div>
            )}

            <button
              type="button"
              onClick={handleNextStep}
              disabled={isSubmitting}
              className="px-6 py-2.5 rounded-xl bg-[#42677D] text-white text-xs font-bold shadow-xs hover:bg-[#345264] transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? (
                <span>Processando...</span>
              ) : step === 4 ? (
                <>
                  <span>Confirmar Reserva</span>
                  <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  <span>Avançar</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        )}

        {step === 5 && (
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
