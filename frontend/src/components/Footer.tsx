import Link from "next/link";
import { Heart, ShieldCheck, MessageCircle } from "lucide-react";

export default function Footer({ whatsapp }: { whatsapp?: string }) {
  const cleanPhone = whatsapp ? whatsapp.replace(/\D/g, "") : "85999998888";

  return (
    <footer className="bg-white border-t border-[#B9D8E8] mt-16 pt-10 pb-8 px-4 text-center">
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="inline-flex items-center justify-center gap-2 text-xl font-bold text-[#42677D]">
          <span>👶</span>
          <span>Chá de Rifa do Lael</span>
          <span>✨</span>
        </div>

        <p className="text-xs sm:text-sm text-[#29343A]/80 max-w-md mx-auto leading-relaxed">
          Agradecemos de coração a cada um de vocês por fazer parte da história do nosso filho. Sua presença, oração e carinho são o nosso maior presente!
        </p>

        <div className="text-xs font-semibold text-[#D99A7B] flex items-center justify-center gap-1.5">
          <span>Com todo o amor de</span>
          <span className="font-bold text-[#42677D]">Talia Vitória & Lucas Gabriel</span>
          <span>❤️</span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-4 text-xs pt-2">
          <a
            href={`https://api.whatsapp.com/send?phone=55${cleanPhone}&text=Ol%C3%A1!%20Tenho%20uma%20d%C3%BAvida%20sobre%20o%20Ch%C3%A1%20de%20Rifa%20do%20Lael.`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-emerald-700 hover:text-emerald-800 font-semibold"
          >
            <MessageCircle className="w-3.5 h-3.5" />
            <span>Falar com o Casal no WhatsApp</span>
          </a>

          <span className="text-slate-300">•</span>

          <Link
            href="/admin"
            className="inline-flex items-center gap-1 text-slate-500 hover:text-[#42677D] font-medium"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Acesso dos Pais / Administrador</span>
          </Link>
        </div>

        <div className="border-t border-slate-100 pt-4 text-[10px] text-slate-400 max-w-md mx-auto leading-normal">
          <p>
            Fortaleza — Ceará • Previsão: Março de 2027.
          </p>
          <p className="mt-1">
            Plataforma desenvolvida para o evento familiar privado. Os dados são armazenados de acordo com a LGPD exclusivamente para a conferência das contribuições.
          </p>
        </div>
      </div>
    </footer>
  );
}
