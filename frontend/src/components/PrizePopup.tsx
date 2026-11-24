"use client";

import { useEffect, useRef, useState } from "react";
import confetti from "canvas-confetti";
import { X, Sparkles, ArrowDown, Gift, Baby } from "lucide-react";
import { popupConfig, SiteSettings } from "@/lib/siteSettings";

const CONFETTI_COLORS = ["#B9D8E8", "#D99A7B", "#A9B8A0", "#42677D", "#FFF8F0"];

/**
 * Popup promocional do prêmio — exibido conforme frequência configurada
 * no painel admin (site.popup.*). Client-side apenas: sem hydration risk.
 */
export default function PrizePopup({
  site,
  onNavigate,
}: {
  site?: SiteSettings | null;
  onNavigate?: (target: string) => void;
}) {
  const cfg = popupConfig(site ?? null);
  const [open, setOpen] = useState(false);
  const closeRef = useRef<HTMLButtonElement>(null);
  const shownRef = useRef(false);

  // Frequência: "uma_vez" usa localStorage, demais usam sessionStorage.
  const storageKey = `lael_popup_${cfg.frequencia === "uma_vez" ? "ever" : "session"}`;
  const storage = cfg.frequencia === "uma_vez" ? localStorage : sessionStorage;

  useEffect(() => {
    if (shownRef.current) return;
    shownRef.current = true;

    if (!cfg.enabled) return;

    // Respeita mostrar_desktop / mostrar_mobile
    const isMobile = window.matchMedia("(max-width: 640px)").matches;
    if ((isMobile && !cfg.mostrarMobile) || (!isMobile && !cfg.mostrarDesktop)) return;

    // Frequência
    try {
      if (cfg.frequencia !== "sempre" && storage.getItem(storageKey)) return;
      if (cfg.frequencia !== "sempre") storage.setItem(storageKey, "1");
    } catch { /* storage indisponível → mostra uma vez */ }

    const delay = Math.max(0, cfg.atrasoSegundos) * 1000;
    const timer = setTimeout(() => {
      setOpen(true);
      window.scrollTo({ top: 0, behavior: "auto" });
      if (cfg.confetes) {
        try {
          confetti({
            particleCount: 90,
            spread: 70,
            origin: { y: 0.25 },
            colors: CONFETTI_COLORS,
            disableForReducedMotion: true,
          });
        } catch { /* confete é opcional */ }
      }
    }, delay);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cfg.enabled, cfg.frequencia, cfg.atrasoSegundos, cfg.confetes, cfg.mostrarDesktop, cfg.mostrarMobile]);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closePopup();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!open) return null;

  const closePopup = () => {
    setOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const go = (target: string) => {
    setOpen(false);
    onNavigate?.(target);
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center p-3 sm:p-6 bg-[#29343A]/55 backdrop-blur-sm animate-in fade-in duration-300"
      role="dialog"
      aria-modal="true"
      aria-label={cfg.chamada}
      onClick={closePopup}
    >
      <div
        className="relative w-[92%] sm:w-[85%] max-w-3xl rounded-3xl overflow-hidden shadow-2xl border bg-gradient-to-br from-white/80 to-[#B9D8E8]/20 animate-in zoom-in-95 duration-300"
        style={{ backgroundColor: cfg.corFundo, color: cfg.corTexto, borderColor: `${cfg.corBotao}40` }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* faixa decorativa superior */}
        <div className="h-2 bg-gradient-to-r from-[#B9D8E8] via-[#D99A7B] to-[#A9B8A0]" />

        {cfg.exibirFechar && (
          <button
            ref={closeRef}
            onClick={closePopup}
            aria-label="Fechar aviso do prêmio"
            className="absolute top-3 right-3 z-10 w-9 h-9 rounded-full bg-white/80 hover:bg-white border border-[#B9D8E8]/60 flex items-center justify-center transition-colors cursor-pointer"
            style={{ color: cfg.corBotao }}
          >
            <X className="w-4 h-4" />
          </button>
        )}

        <div className="px-6 sm:px-10 py-8 sm:py-10 text-center">
          <div className="flex items-center justify-center gap-2 mb-3 text-[#D99A7B]">
            <Baby className="w-5 h-5" />
            <Sparkles className="w-4 h-4" />
            <Gift className="w-5 h-5" />
            <Sparkles className="w-4 h-4" />
            <Baby className="w-5 h-5" />
          </div>

          <p className="text-xs sm:text-sm font-bold tracking-[0.25em] uppercase mb-1 opacity-80">
            {cfg.titulo}
          </p>

          <p className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider mb-4 opacity-60">
            {cfg.chamada}
          </p>

          <div className="my-4 inline-flex flex-col items-center">
            <span
              className="inline-flex items-center justify-center gap-2 text-5xl sm:text-7xl font-black drop-shadow-sm"
              style={{ color: cfg.corBotao }}
            >
              <Gift className="w-9 h-9 sm:w-14 sm:h-14 text-[#D99A7B]" />
              {cfg.valor}
            </span>
          </div>

          <p className="text-sm sm:text-base opacity-80 max-w-xl mx-auto leading-relaxed">
            {cfg.texto}
          </p>
          <p className="text-xs sm:text-sm font-semibold mt-2" style={{ color: cfg.corBotao }}>
            Escolha seu número e participe dessa bênção com a gente!
          </p>

          <div className="mt-7 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => go(cfg.destinoBotao)}
              className="w-full sm:w-auto px-7 py-3.5 rounded-2xl text-white font-black text-sm tracking-wide shadow-lg transition-all hover:scale-[1.02] cursor-pointer flex items-center justify-center gap-2"
              style={{ backgroundColor: cfg.corBotao }}
            >
              {cfg.botaoPrincipal}
              <ArrowDown className="w-4 h-4" />
            </button>
            {cfg.exibirBotaoSecundario && (
              <button
                onClick={() => go(cfg.destinoBotaoSecundario)}
                className="w-full sm:w-auto px-6 py-3.5 rounded-2xl bg-white/70 hover:bg-white border font-bold text-sm transition-all cursor-pointer"
                style={{ borderColor: `${cfg.corBotao}40`, color: cfg.corBotao }}
              >
                {cfg.botaoSecundario}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
