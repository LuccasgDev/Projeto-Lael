"use client";

import { useState } from "react";
import { GridItem } from "@/lib/api";
import { Search, Sparkles, Check, Clock, Lock, Info } from "lucide-react";

interface NumbersGridProps {
  numbers: GridItem[];
  isLoading: boolean;
  onSelectNumber: (num: number) => void;
}

export default function NumbersGrid({ numbers, isLoading, onSelectNumber }: NumbersGridProps) {
  const [filter, setFilter] = useState<"todos" | "disponivel" | "reservado" | "confirmado">("todos");
  const [search, setSearch] = useState("");

  const filteredNumbers = numbers.filter((item) => {
    // Filter by status
    if (filter !== "todos" && item.status !== filter) return false;
    // Filter by search
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const numMatch = String(item.numero).padStart(2, "0").includes(q) || String(item.numero).includes(q);
      const nameMatch = item.nome_publico?.toLowerCase().includes(q);
      const prodMatch = item.produto_nome?.toLowerCase().includes(q);
      return numMatch || nameMatch || prodMatch;
    }
    return true;
  });

  const countDisponiveis = numbers.filter((n) => n.status === "disponivel").length;
  const countReservados = numbers.filter((n) => n.status === "reservado").length;
  const countConfirmados = numbers.filter((n) => n.status === "confirmado").length;

  return (
    <section id="numeros" className="py-12 px-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center max-w-xl mx-auto mb-8">
        <span className="text-xs font-bold uppercase tracking-wider text-[#42677D] bg-[#A9B8A0]/25 px-3 py-1 rounded-full">
          Grade Interativa de 01 a 100
        </span>
        <h2 className="text-2xl sm:text-4xl font-extrabold text-[#42677D] mt-2 mb-2">
          Escolha o seu Número da Sorte
        </h2>
        <p className="text-xs sm:text-sm text-[#29343A]/80">
          Toque em um número <span className="font-semibold text-emerald-700">verde (disponível)</span> para visualizar o presente e garantir sua reserva.
        </p>
      </div>

      {/* ALWAYS VISIBLE LEGEND & STATS */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl p-4 border border-[#B9D8E8] shadow-xs mb-6 max-w-3xl mx-auto">
        <div className="text-xs font-bold text-[#42677D] uppercase tracking-wider mb-2.5 text-center sm:text-left">
          Legenda de Estados:
        </div>
        <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
          {/* Disponível */}
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

          {/* Reservado */}
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

          {/* Confirmado */}
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
            Todos (100)
          </button>
          <button
            onClick={() => setFilter("disponivel")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "disponivel"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-white text-emerald-800 border border-emerald-200 hover:bg-emerald-50"
            }`}
          >
            Disponíveis ({countDisponiveis})
          </button>
          <button
            onClick={() => setFilter("reservado")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "reservado"
                ? "bg-amber-600 text-white shadow-xs"
                : "bg-white text-amber-800 border border-amber-200 hover:bg-amber-50"
            }`}
          >
            Reservados ({countReservados})
          </button>
          <button
            onClick={() => setFilter("confirmado")}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              filter === "confirmado"
                ? "bg-slate-700 text-white shadow-xs"
                : "bg-white text-slate-800 border border-slate-300 hover:bg-slate-100"
            }`}
          >
            Confirmados ({countConfirmados})
          </button>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar número..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white rounded-xl border border-[#B9D8E8] focus:outline-hidden focus:ring-2 focus:ring-[#42677D]/30"
          />
        </div>
      </div>

      {/* NUMBERS GRID */}
      {isLoading ? (
        <div className="py-20 text-center">
          <div className="w-10 h-10 border-4 border-[#B9D8E8] border-t-[#42677D] rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-[#42677D] font-medium">Carregando os números da rifa...</p>
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
            Ver todos os 100 números
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-5 sm:grid-cols-8 md:grid-cols-10 gap-2 sm:gap-3 max-w-5xl mx-auto">
          {filteredNumbers.map((item) => {
            const isDisponivel = item.status === "disponivel";
            const isReservado = item.status === "reservado";
            const isConfirmado = item.status === "confirmado";

            return (
              <button
                key={item.id}
                onClick={() => {
                  if (isDisponivel) {
                    onSelectNumber(item.numero);
                  }
                }}
                disabled={!isDisponivel}
                className={`relative aspect-square rounded-2xl flex flex-col items-center justify-center p-1.5 transition-all duration-200 select-none group ${
                  isDisponivel
                    ? "bg-gradient-to-br from-emerald-50 to-emerald-100/80 border-2 border-emerald-400/80 text-emerald-950 shadow-xs hover:border-emerald-600 hover:scale-105 active:scale-95 hover:shadow-md cursor-pointer"
                    : isReservado
                    ? "bg-gradient-to-br from-amber-50 to-amber-100/80 border-2 border-amber-400/80 text-amber-950 cursor-not-allowed opacity-90"
                    : "bg-gradient-to-br from-slate-100 to-slate-200/90 border-2 border-slate-300 text-slate-700 cursor-not-allowed opacity-75"
                }`}
                title={
                  isDisponivel
                    ? `Número ${String(item.numero).padStart(2, "0")} Disponível! Clique para escolher.`
                    : isReservado
                    ? `Número ${String(item.numero).padStart(2, "0")} Reservado aguardando comprovantes.`
                    : `Número ${String(item.numero).padStart(2, "0")} Confirmado!`
                }
              >
                {/* Status Indicator Icon */}
                <div className="absolute top-1 right-1.5">
                  {isDisponivel && (
                    <span className="w-2 h-2 rounded-full bg-emerald-500 block shadow-2xs group-hover:scale-125 transition-transform"></span>
                  )}
                  {isReservado && (
                    <Clock className="w-2.5 h-2.5 text-amber-700" />
                  )}
                  {isConfirmado && (
                    <Check className="w-2.5 h-2.5 text-slate-600" />
                  )}
                </div>

                {/* Number Display */}
                <span className="text-base sm:text-xl font-extrabold tracking-tight block leading-none">
                  {String(item.numero).padStart(2, "0")}
                </span>

                {/* Bottom label / guest name or status */}
                <span className="text-[9px] sm:text-[10px] font-semibold mt-1 truncate max-w-full px-1 text-center leading-tight">
                  {isDisponivel ? (
                    <span className="text-emerald-800 font-medium">Livre</span>
                  ) : item.nome_publico ? (
                    <span className="text-slate-800">{item.nome_publico}</span>
                  ) : isReservado ? (
                    <span className="text-amber-800">Reservado</span>
                  ) : (
                    <span className="text-slate-600">Confirmado</span>
                  )}
                </span>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
