import { CheckCircle2, Clock, XCircle } from "lucide-react";

/**
 * Estado exibido por TEXTO + ícone, nunca só por cor (RN-03 / §6 acessibilidade).
 */
export default function StatusBadge({ status }: { status: string }) {
  if (status === "confirmada") {
    return (
      <span
        data-testid="status-badge"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-200 text-slate-800 font-bold text-sm"
      >
        <CheckCircle2 className="w-5 h-5" aria-hidden="true" /> Confirmada
      </span>
    );
  }
  if (status === "reservada") {
    return (
      <span
        data-testid="status-badge"
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-200 text-amber-900 font-bold text-sm"
      >
        <Clock className="w-5 h-5" aria-hidden="true" /> Aguardando comprovantes
      </span>
    );
  }
  return (
    <span
      data-testid="status-badge"
      className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-rose-200 text-rose-900 font-bold text-sm"
    >
      <XCircle className="w-5 h-5" aria-hidden="true" /> Expirada ou liberada
    </span>
  );
}
