"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { fetchAcompanhamento, ReservationResponse } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";
import { formatBRL } from "@/lib/format";
import { MessageCircle, Loader2 } from "lucide-react";

function AcompanhamentoInner() {
  const searchParams = useSearchParams();
  const [reserva, setReserva] = useState<ReservationResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    const token = searchParams.get("t") || localStorage.getItem("lael_tracking_token");
    if (!token) {
      setErro("Nenhum link de acompanhamento encontrado. Use o link secreto enviado a você após a reserva.");
      setCarregando(false);
      return;
    }
    fetchAcompanhamento(token)
      .then(setReserva)
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false));
  }, [searchParams]);

  if (carregando) {
    return (
      <div className="flex items-center justify-center py-24 text-[#42677D]">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (erro || !reserva) {
    return (
      <div className="max-w-md mx-auto text-center py-16 px-4">
        <p className="text-[#29343A] text-sm bg-white rounded-2xl p-6 shadow-md border border-[#B9D8E8]/50">
          {erro || "Reserva não encontrada."}
        </p>
      </div>
    );
  }

  const expira = new Date(reserva.expira_em);

  return (
    <div className="max-w-md mx-auto px-4 py-10">
      <div className="bg-white rounded-3xl shadow-lg border border-[#B9D8E8]/60 p-6 space-y-4">
        <h1 className="font-serif text-2xl text-[#42677D] text-center">Acompanhamento da Reserva</h1>
        <div className="text-center">
          <p className="text-xs text-[#29343A]/70">Número reservado</p>
          <p className="text-4xl font-extrabold text-[#42677D]">{String(reserva.numero).padStart(2, "0")}</p>
        </div>

        <div className="flex justify-center">
          <StatusBadge status={reserva.status} />
        </div>

        {reserva.status === "reservada" && (
          <p className="text-xs text-center text-[#29343A]/80">
            Prazo para envio dos comprovantes: até{" "}
            <strong>{expira.toLocaleDateString("pt-BR")} às {expira.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</strong>
          </p>
        )}

        <dl className="text-sm space-y-2 bg-[#FFF8F0] rounded-2xl p-4 border border-[#A9B8A0]/40">
          <div className="flex justify-between gap-2"><dt className="text-[#29343A]/70">Presente</dt><dd className="text-right font-medium">{reserva.presente_nome}</dd></div>
          <div className="flex justify-between gap-2"><dt className="text-[#29343A]/70">Forma do presente</dt><dd className="font-medium">{reserva.forma_presente === "pix" ? "Pix" : "Compra na Amazon"}</dd></div>
          <div className="flex justify-between gap-2"><dt className="text-[#29343A]/70">Mimo</dt><dd className="text-right font-medium">{reserva.mimo_nome}</dd></div>
          <div className="flex justify-between gap-2"><dt className="text-[#29343A]/70">Forma do mimo</dt><dd className="font-medium">{reserva.forma_mimo === "pix" ? "Pix" : "Compra na Amazon"}</dd></div>
          {reserva.valor_pix_total > 0 && (
            <div className="flex justify-between gap-2 border-t border-[#A9B8A0]/40 pt-2">
              <dt className="font-bold">Total via Pix</dt>
              <dd className="font-bold text-[#42677D]">{formatBRL(reserva.valor_pix_total)}</dd>
            </div>
          )}
        </dl>

        <ul className="text-xs space-y-1 text-[#29343A]/80">
          {reserva.comprovantes.map((c) => (
            <li key={c.id} className="flex items-center gap-2">
              <span className="capitalize font-medium">{c.tipo_item}:</span>
              <span className="text-[#42677D]">{c.status === "aguardando_envio" ? "aguardando envio" : c.status}</span>
            </li>
          ))}
        </ul>

        <a
          href={reserva.whatsapp_link}
          target="_blank"
          rel="noopener noreferrer"
          className="w-full py-3 px-6 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2"
        >
          <MessageCircle className="w-5 h-5" /> Falar com o casal no WhatsApp
        </a>
      </div>
    </div>
  );
}

export default function AcompanhamentoPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#FFF8F0]">
      <Navbar />
      <main className="flex-1">
        <Suspense fallback={null}>
          <AcompanhamentoInner />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}
