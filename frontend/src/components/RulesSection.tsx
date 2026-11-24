"use client";

import { CheckCircle2, ShoppingBag, Send, Clock, Sparkles } from "lucide-react";
import { SiteSettings, s as sStr } from "@/lib/siteSettings";

export default function RulesSection({ site }: { site?: SiteSettings | null }) {
  const steps = [
    {
      num: "1",
      icon: "🔢",
      title: "Escolha seu número",
      desc: "Navegue pela grade de 01 a 100. Os números verdes estão livres e prontos para você escolher.",
    },
    {
      num: "2",
      icon: "🎁",
      title: "Fralda + Mimo do número",
      desc: "Cada número corresponde a um tamanho de fralda (RN, P, M ou G) e já inclui um mimo especial correspondente. Nos números de tamanho M, você poderá escolher o mimo que desejar para complementar sua contribuição ao enxoval do Lael.",
    },
    {
      num: "3",
      icon: "💳",
      title: "Amazon, Loja Física ou Pix",
      desc: "Você pode escolher a forma que preferir para contribuir: comprar diretamente pela nossa lista do bebê na Amazon, adquirir os produtos em uma loja física e combinar a entrega conosco, ou enviar o valor correspondente por Pix para cada um dos dois produtos.",
    },
    {
      num: "4",
      icon: "📲",
      title: "Envio de Comprovantes",
      desc: "Após reservar seu número, você terá até 72 horas para enviar os comprovantes pelo WhatsApp para que o casal possa confirmar sua participação.",
    },
  ];

  return (
    <section id="regras" className="py-10 px-4 bg-white/50 border-y border-[#B9D8E8]/40">
      <div className="max-w-5xl mx-auto">
        <div className="text-center max-w-xl mx-auto mb-8">
          <span className="text-xs font-bold uppercase tracking-wider text-[#42677D] bg-[#B9D8E8]/40 px-3 py-1 rounded-full">
            Passo a Passo
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-[#42677D] mt-2 mb-2">
            {sStr(site?.textos?.como_funciona_titulo, "Como Funciona a Participação")}
          </h2>
          <p className="text-xs sm:text-sm text-[#29343A]/80">
            {sStr(site?.rifa?.mensagem_instrucoes, "É muito fácil e rápido garantir seu número e demonstrar seu carinho pelo Lael.")}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {steps.map((st, i) => (
            <div
              key={i}
              className="bg-white p-5 rounded-2xl border border-[#B9D8E8]/60 shadow-2xs hover:shadow-xs transition-shadow flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-2xl">{st.icon}</span>
                  <span className="w-6 h-6 rounded-full bg-[#42677D] text-white text-xs font-bold flex items-center justify-center">
                    {st.num}
                  </span>
                </div>
                <h3 className="font-bold text-sm text-[#42677D] mb-1.5">{st.title}</h3>
                <p className="text-xs text-[#29343A]/75 leading-relaxed">{st.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
