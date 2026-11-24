"use client";

import { useState } from "react";
import { GridItem } from "@/lib/api";
import { Search, Check, Clock, Info } from "lucide-react";

interface NumbersGridProps {
  numbers: GridItem[];
  isLoading: boolean;
  onSelectNumber: (num: number) => void;
}

/** Cores de identificação por tamanho de fralda (regra fixa RN/P/M/G) */
const TAMANHO_STYLE: Record<string, { cor: string; bg: string; texto: string }> = {
  RN: { cor: "border-sky-400", bg: "bg-sky-100/80", texto: "text-sky-800" },
  P: { cor: "border-violet-400", bg: "bg-violet-100/80", texto: "text-violet-800" },
  M: { cor: "border-rose-400", bg: "bg-rose-100/80", texto: "text-rose-800" },
  G: { cor: "border-amber-500", bg: "bg-amber-100/80", texto: "text-amber-800" },
};

/**
 * §4 v2: grade SIMPLES e única de 01 a 100 — cada número mostra o tamanho
 * da fralda da sua faixa fixa (RN 01-05, P 06-35, M 36-65, G 66-100) com
 * cor própria + legenda. O detalhe do produto e do mimo aparece ao clicar.
 */
export default function NumbersGrid({ numbers, isLoading, onSelectNumber }: NumbersGridProps) {
  const [filter, setFilter] = useState<"todos" | "disponivel" | "reservado" | "confirmado">("todos");
  const [search, setSearch] = useState("");

  const numerosOrdenados = [...numbers].sort((a, b) => a.numero - b.numero);

  const filteredNumbers = numerosOrdenados.filter((item) => {
    // Compra externa também é cinza: aparece em "Todos" e "Confirmados"
    if (item.status === "compra_externa") return filter === "todos" || filter === "confirmado";
    if (filter !== "todos" && item.status !== filter) return false;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const numMatch = String(item.numero).padStart(2, "0").includes(q) || String(item.numero).includes(q);
      const nameMatch = item.nome_publico?.toLowerCase().includes(q);
      return numMatch || nameMatch;
    }
    return true;
  });

  const countDisponiveis = numbers.filter((n) => n.status === "disponivel").length;
  const countReservados = numbers.filter((n) => n.status === "reservado").length;
  const countConfirmados = numbers.filter((n) => n.status === "confirmado").length;
  const countExternas = numbers.filter((n) => n.status === "compra_externa").length;

  return (
    <section id="numeros" className="py-12 px-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center max-w-xl mx-auto mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-[#42677D] bg-[#A9B8A0]/25 px-3 py-1 rounded-full">
          Grade de 01 a 100
        </span>
        <h2 className="text-2xl sm:text-4xl font-extrabold text-[#42677D] mt-2 mb-2">
          Escolha o seu número
        </h2>
        <p className="text-xs sm:text-sm text-[#29343A]/80">
          Cada número já vem com um tamanho de fralda (RN, P, M ou G) e um mimo correspondente.
          Toque em um número <span className="font-semibold text-emerald-700">verde (disponível)</span> para começar.
        </p>
      </div>

      {/* Legenda de tamanhos de fralda (regra fixa) */}
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 mb-6">
        {(["RN", "P", "M", "G"] as const).map((tam) => {
          const estilo = TAMANHO_STYLE[tam];
          const faixa =
            tam === "RN" ? "01–05" : tam === "P" ? "06–35" : tam === "M" ? "36–65" : "66–100";
          return (
            <span
              key={tam}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] sm:text-[11px] font-bold border ${estilo.cor} ${estilo.bg} ${estilo.texto}`}
              title={`Fralda ${tam} · números ${faixa}`}
            >
              <span className="w-2 h-2 rounded-full bg-current opacity-70"></span>
              Fralda {tam} · {faixa}
            </span>
          );
        })}
      </div>

      {/* ALWAYS VISIBLE LEGEND & STATS (RN-03) */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 border border-[#B9D8E8] shadow-xs mb-6 max-w-3xl mx-auto">
        <div className="text-xs font-bold text-[#42677D] uppercase tracking-wider mb-2.5 text-center sm:text-left">
          Legenda de Estados:
        </div>
        <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
          <div
            onClick={() => setFilter("disponivel")}
            className={`p-2.5 rounded-xl cursor-pointer transition-all border ${
              filter === "disponivel"
                ? "bg-emerald-100/90 border-emerald-500 ring-2 ring-emerald-500/30"
                : "bg-emerald-50/70 border-emerald-200 hover:bg-emerald-100/50"
            }`}
          >
            <div className="flex items-center justify-center gap-1.5 mb-0.5">
              <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 inline-block shadow-2xs"></span>
              <span className="text-xs sm:text-sm font-bold text-emerald-900">Disponível</span>
            </div>
            <span className="text-xs font-semibold text-emerald-800/80">{countDisponiveis} livres</span>
          </div>

          <div
            onClick={() => setFilter("reservado")}
            className={`p-2.5 rounded-xl cursor-pointer transition-all border ${
              filter === "reservado"
                ? "bg-amber-100/90 border-amber-500 ring-2 ring-amber-500/30"
                : "bg-amber-50/70 border-amber-200 hover:bg-amber-100/50"
            }`}
          >
            <div className="flex items-center justify-center gap-1.5 mb-0.5">
              <span className="w-3.5 h-3.5 rounded-full bg-amber-500 inline-block shadow-2xs"></span>
              <span className="text-xs sm:text-sm font-bold text-amber-900">Reservado</span>
            </div>
            <span className="text-xs font-semibold text-amber-800/80">{countReservados} em 72h</span>
          </div>

          <div
            onClick={() => setFilter("confirmado")}
            className={`p-2.5 rounded-xl cursor-pointer transition-all border ${
              filter === "confirmado"
                ? "bg-slate-200/90 border-slate-500 ring-2 ring-slate-500/30"
                : "bg-slate-100/70 border-slate-300 hover:bg-slate-200/50"
            }`}
          >
            <div className="flex items-center justify-center gap-1.5 mb-0.5">
              <span className="w-3.5 h-3.5 rounded-full bg-slate-500 inline-block shadow-2xs"></span>
              <span className="text-xs sm:text-sm font-bold text-slate-900">Confirmado</span>
            </div>
            <span className="text-xs font-semibold text-slate-700/80">{countConfirmados} aprovados</span>
          </div>
        </div>
        {countExternas > 0 && (
          <p className="text-[10px] text-slate-500 text-center mt-2">
            🛒 {countExternas} número(s) já comprado(s) direto na lista da Amazon (compra externa)
          </p>
        )}
      </div>

      {/* FILTER BAR & SEARCH */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-6 max-w-4xl mx-auto">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <button
            onClick={() => setFilter("todos")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "todos"
                ? "bg-[#42677D] text-white shadow-xs"
                : "bg-white text-[#42677D] border border-[#B9D8E8] hover:bg-[#B9D8E8]/20"
            }`}
          >
            Todos
          </button>
          <button
            onClick={() => setFilter("disponivel")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "disponivel" ? "bg-emerald-600 text-white" : "bg-white text-[#42677D] border border-[#B9D8E8]"
            }`}
          >
            Disponíveis
          </button>
          <button
            onClick={() => setFilter("reservado")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "reservado" ? "bg-amber-500 text-white" : "bg-white text-[#42677D] border border-[#B9D8E8]"
            }`}
          >
            Reservados
          </button>
          <button
            onClick={() => setFilter("confirmado")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "confirmado" ? "bg-slate-500 text-white" : "bg-white text-[#42677D] border border-[#B9D8E8]"
            }`}
          >
            Confirmados
          </button>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar número..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Buscar número"
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
          />
        </div>
      </div>

      {/* GRADE SIMPLES 01–100 (§4 v2) */}
      {isLoading ? (
        <div className="py-20 text-center">
          <div className="w-10 h-10 border-4 border-[#B9D8E8] border-t-[#42677D] rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-[#42677D] font-medium">Carregando os números...</p>
        </div>
      ) : filteredNumbers.length === 0 ? (
        <div className="py-16 text-center bg-white/60 rounded-2xl border border-dashed border-[#B9D8E8] max-w-md mx-auto">
          <Info className="w-8 h-8 text-[#42677D]/60 mx-auto mb-2" />
          <p className="text-sm font-semibold text-[#42677D]">Nenhum número encontrado</p>
          <p className="text-xs text-slate-500 mt-1">Tente remover os filtros ou buscar outro termo.</p>
          <button
            onClick={() => {
              setFilter("todos");
              setSearch("");
            }}
            className="mt-3 text-xs font-bold text-[#42677D] underline cursor-pointer"
          >
            Ver todos os números
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-2 sm:gap-3 max-w-5xl mx-auto">
          {filteredNumbers.map((item) => {
            const isDisponivel = item.status === "disponivel";
            const isReservado = item.status === "reservado";
            const isConfirmado = item.status === "confirmado";
            const isCompraExterna = item.status === "compra_externa";
            const rotuloEstado = isDisponivel
              ? "Disponível"
              : isReservado
              ? "Reservado"
              : isConfirmado
              ? "Confirmado"
              : "Comprado externamente";

            return (
              <button
                key={item.id}
                onClick={() => {
                  if (isDisponivel) {
                    onSelectNumber(item.numero);
                  }
                }}
                disabled={!isDisponivel}
                aria-label={`Número ${String(item.numero).padStart(2, "0")}${item.produto_tamanho ? ` — fralda ${item.produto_tamanho}` : ""} — ${rotuloEstado}${
                  isDisponivel ? ". Ative para escolher este número." : ""
                }`}
                title={`Número ${String(item.numero).padStart(2, "0")}${item.produto_tamanho ? ` · Fralda ${item.produto_tamanho}` : ""}${item.mimo_nome ? ` + ${item.mimo_nome}` : ""} — ${rotuloEstado}${
                  isCompraExterna ? " (compra fora do site)" : ""
                }`}
                className={`relative aspect-square rounded-2xl flex flex-col items-center justify-center p-1.5 transition-all duration-200 select-none group ${
                  isDisponivel
                    ? "bg-gradient-to-br from-emerald-50 to-emerald-100/80 border-2 border-emerald-400/80 text-emerald-950 shadow-xs hover:border-emerald-600 hover:scale-105 active:scale-95 hover:shadow-md cursor-pointer"
                    : isReservado
                    ? "bg-gradient-to-br from-amber-50 to-amber-100/80 border-2 border-amber-400/80 text-amber-950 cursor-not-allowed opacity-90"
                    : "bg-gradient-to-br from-slate-100 to-slate-200/90 border-2 border-slate-300 text-slate-700 cursor-not-allowed opacity-75"
                }`}
              >
                {/* Status Indicator Icon */}
                <div className="absolute top-1 right-1.5">
                  {isDisponivel && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 block shadow-2xs group-hover:scale-125 transition-transform"></span>
                  )}
                  {isReservado && <Clock className="w-2.5 h-2.5 text-amber-700" aria-hidden="true" />}
                  {(isConfirmado || isCompraExterna) && (
                    <Check className="w-2.5 h-2.5 text-slate-600" aria-hidden="true" />
                  )}
                </div>

                {/* Number Display + tamanho da fralda (regra fixa) */}
                <span className="text-base sm:text-xl font-extrabold tracking-tight block leading-none">
                  {String(item.numero).padStart(2, "0")}
                </span>
                {item.produto_tamanho && (
                  <span
                    className={`text-[8px] sm:text-[9px] font-black px-1 rounded-full leading-tight mt-0.5 ${
                      TAMANHO_STYLE[item.produto_tamanho]?.texto ?? "text-slate-600"
                    } bg-white/70`}
                  >
                    {item.produto_tamanho}
                  </span>
                )}
                {(isReservado || isCompraExterna) && item.nome_publico && (
                  <span className="text-[9px] font-semibold truncate max-w-full px-0.5">{item.nome_publico}</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
