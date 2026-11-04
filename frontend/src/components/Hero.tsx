"use client";

import { Sparkles, Heart, Gift, AlertCircle, ArrowDown, Clock, ShieldCheck } from "lucide-react";

export default function Hero({ onChooseNumber }: { onChooseNumber: () => void }) {
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
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#B9D8E8]/40 border border-[#B9D8E8] text-[#42677D] text-xs sm:text-sm font-semibold mb-6 shadow-xs animate-float">
          <span>👶</span>
          <span>Chá de Bebê do Lael • Março de 2027 • Fortaleza/CE</span>
        </div>

        {/* Main Title */}
        <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold text-[#42677D] tracking-tight mb-4 leading-tight">
          Chá de Rifa do <span className="text-[#D99A7B] underline decoration-[#B9D8E8] decoration-wavy decoration-2">Lael</span>
        </h1>

        {/* Emotional Subtitle */}
        <p className="text-base sm:text-lg md:text-xl text-[#29343A]/85 max-w-2xl mx-auto mb-8 font-normal leading-relaxed">
          Com o coração transbordando de amor, estamos preparando a chegada do nosso tão esperado menininho. Escolha seu número da sorte, presenteie o Lael e comemore essa bênção com a gente!
        </p>

        {/* Call To Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-8">
          <button
            onClick={onChooseNumber}
            className="w-full sm:w-auto px-8 py-3.5 rounded-2xl bg-[#42677D] text-white font-bold text-base shadow-md hover:bg-[#345264] hover:shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Sparkles className="w-5 h-5 text-[#B9D8E8]" />
            Escolher meu número
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
            <span className="text-[11px] text-[#29343A]/70">Amazon ou Pix</span>
          </div>

          <div className="bg-white/70 backdrop-blur-xs p-3 rounded-xl border border-[#B9D8E8]/50 shadow-2xs">
            <span className="text-xl block mb-1">⏱️</span>
            <span className="text-xs font-bold text-[#42677D] block">72 Horas</span>
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
              &ldquo;Para confirmar seu número, será necessário comprovar a aquisição do presente e do mimo escolhidos.&rdquo;
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
