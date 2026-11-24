"use client";

import { Sparkles, Gift, AlertCircle, ArrowDown, Trophy } from "lucide-react";
import { SiteSettings, s as sStr } from "@/lib/siteSettings";

export default function Hero({
  onChooseNumber,
  site,
  prazoHoras,
}: {
  onChooseNumber: () => void;
  site?: SiteSettings | null;
  prazoHoras?: number;
}) {
  const ev = site?.evento;
  const premio = site?.premio;
  const textos = site?.textos;
  const horas = prazoHoras ?? site?.reserva?.prazo_padrao_horas ?? 72;

  const exibirDadosEvento = ev?.exibir_dados_evento !== false;
  const local = [ev?.cidade, ev?.estado].filter(Boolean).join("/");
  const pillText = [
    `Chá de Bebê d${sStr(ev?.bebe, "o Lael")}`,
    ev?.data,
    local || null,
  ].filter(Boolean).join(" • ");

  const premioAtivo = (premio?.ativo ?? true) && (premio?.exibir_banner_home ?? true);
  const premioValor = sStr(premio?.valor, "R$ 250,00");

  return (
    <section className="relative overflow-hidden pt-8 pb-12 sm:pt-14 sm:pb-16 px-4">
      {/* Decorative Celestial Elements */}
      <div className="absolute top-4 left-6 text-xl sm:text-2xl animate-twinkle-1 select-none pointer-events-none opacity-60">
        ⭐
      </div>
      <div className="absolute top-10 right-10 text-2xl sm:text-3xl animate-twinkle-2 select-none pointer-events-none opacity-50">
        🌙
      </div>
      <div className="absolute top-36 left-1/4 text-sm animate-twinkle-3 select-none pointer-events-none opacity-40">
        ✨
      </div>
      <div className="absolute bottom-6 right-16 text-lg animate-twinkle-1 select-none pointer-events-none opacity-50">
        ☁️
      </div>

      <div className="max-w-4xl mx-auto text-center relative z-10">
        {/* Event Pill */}
        {exibirDadosEvento && (
          <div className="inline-flex flex-wrap items-center justify-center gap-x-2 px-4 py-1.5 rounded-full bg-[#B9D8E8]/40 border border-[#B9D8E8] text-[#42677D] text-xs sm:text-sm font-semibold mb-6 shadow-xs animate-float max-w-full">
            <span>👶</span>
            <span className="text-center">{pillText}</span>
          </div>
        )}

        {/* Main Title — última palavra em destaque (ex.: "Lael") */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold text-[#42677D] tracking-tight mb-4 leading-tight">
          {(() => {
            const nome = sStr(ev?.nome, "Chá Rifa do Lael");
            const idx = nome.lastIndexOf(" ");
            if (idx === -1) return nome;
            return (
              <>
                {nome.slice(0, idx + 1)}
                <span className="text-[#D99A7B] underline decoration-[#B9D8E8] decoration-wavy decoration-2">{nome.slice(idx + 1)}</span>
              </>
            );
          })()}
        </h1>

        {/* Emotional Subtitle */}
        <p className="text-base sm:text-lg md:text-xl text-[#29343A]/85 max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
          {sStr(ev?.subtitulo, "Escolha seu número da sorte, presenteie o Lael e comemore essa bênção com a gente!")}
        </p>

        {/* Prêmio principal */}
        {premioAtivo && premio?.mostrar_valor !== false && (
          <div className="max-w-md mx-auto mb-7">
            <div className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-2xl bg-gradient-to-r from-[#42677D]/10 via-[#D99A7B]/15 to-[#42677D]/10 border border-[#D99A7B]/50 shadow-md">
              <Trophy className="w-5 h-5 text-[#D99A7B] shrink-0" />
              <span className="text-xs sm:text-sm font-bold text-[#42677D]">
                {sStr(premio?.texto_antes_valor, "Prêmio principal:")}{" "}
                <span className="text-[#D99A7B] text-base sm:text-lg font-black">{premioValor}</span>
              </span>
            </div>
          </div>
        )}

        {/* Call To Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-8">
          <button
            onClick={onChooseNumber}
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-[#42677D] text-white font-bold text-base shadow-md hover:bg-[#345264] hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Sparkles className="w-5 h-5 text-[#B9D8E8]" />
            {sStr(textos?.botao_participar, "Escolher meu número")}
            <ArrowDown className="w-4 h-4 ml-1" />
          </button>

          <a
            href="#regras"
            className="w-full sm:w-auto px-6 py-3.5 rounded-2xl bg-white/80 hover:bg-white text-[#42677D] font-semibold text-sm border border-[#B9D8E8] shadow-xs transition-colors flex items-center justify-center gap-2"
          >
            <Gift className="w-4 h-4 text-[#D99A7B]" />
            Como funciona a rifa
          </a>
        </div>

        {/* Key Badges */}
        <div className="grid grid-cols-3 gap-2 sm:gap-4 max-w-lg mx-auto mb-8">
          <div className="bg-white/70 backdrop-blur-xs p-3 rounded-xl border border-[#B9D8E8]/50 shadow-2xs">
            <span className="text-xl block mb-1">🔢</span>
            <span className="text-xs font-bold text-[#42677D] block">100 Números</span>
            <span className="text-[11px] text-[#29343A]/70">de 01 a 100</span>
          </div>

          <div className="bg-white/70 backdrop-blur-xs p-3 rounded-xl border border-[#B9D8E8]/50 shadow-2xs">
            <span className="text-xl block mb-1">🎁</span>
            <span className="text-xs font-bold text-[#42677D] block">Presente + Mimo</span>
            <span className="text-[11px] text-[#29343A]/70">Amazon, Loja ou Pix</span>
          </div>

          <div className="bg-white/70 backdrop-blur-xs p-3 rounded-xl border border-[#B9D8E8]/50 shadow-2xs">
            <span className="text-xl block mb-1">⏱️</span>
            <span className="text-xs font-bold text-[#42677D] block">{horas} Horas</span>
            <span className="text-[11px] text-[#29343A]/70">prazo de reserva</span>
          </div>
        </div>

        {/* MANDATORY ALERT BANNER */}
        <div className="max-w-2xl mx-auto bg-gradient-to-r from-[#D99A7B]/15 via-[#FFF8F0] to-[#D99A7B]/15 border-2 border-[#D99A7B]/60 p-4 rounded-2xl shadow-sm text-left flex items-start gap-3">
          <AlertCircle className="w-6 h-6 text-[#D99A7B] shrink-0 mt-0.5" />
          <div>
            <span className="block font-bold text-sm text-[#42677D] mb-0.5">
              Aviso Importante:
            </span>
            <p className="text-xs sm:text-sm text-[#29343A] leading-relaxed font-medium">
              &ldquo;{sStr(site?.rifa?.aviso_confirmacao || textos?.aviso_importante, "Para confirmar seu número, será necessário comprovar a aquisição do presente e do mimo escolhidos.")}&rdquo;
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
