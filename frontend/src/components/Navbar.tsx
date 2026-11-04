"use client";

import Link from "next/link";
import { Sparkles, ShieldCheck, Heart } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 bg-[#FFF8F0]/90 backdrop-blur-md border-b border-[#B9D8E8]/50 shadow-xs">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-[#B9D8E8] to-[#FFF8F0] border border-[#42677D]/20 flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform">
            <span className="text-xl">👶</span>
          </div>
          <div>
            <span className="font-bold text-lg text-[#42677D] tracking-tight block leading-tight">
              Chá de Rifa do Lael
            </span>
            <span className="text-xs text-[#29343A]/70 flex items-center gap-1">
              <span>Fortaleza — CE</span>
              <span className="text-[#D99A7B]">•</span>
              <span>Março de 2027</span>
            </span>
          </div>
        </Link>

        <div className="flex items-center gap-3">
          <a
            href="#numeros"
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[#A9B8A0]/20 text-[#42677D] border border-[#A9B8A0]/40 hover:bg-[#A9B8A0]/30 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#42677D]" />
            Escolher Número
          </a>

          <Link
            href="/admin"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[#42677D] hover:bg-[#B9D8E8]/30 transition-colors border border-transparent hover:border-[#B9D8E8]"
          >
            <ShieldCheck className="w-4 h-4" />
            <span className="hidden sm:inline">Painel do Casal</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
