"use client";

import { CheckCircle2, ShoppingBag, Send, Clock, Sparkles } from "lucide-react";

export default function RulesSection() {
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
      title: "Presente + Mimo",
      desc: "Cada número traz um presente principal especial. Em seguida, escolha um mimo complementar da lista.",
    },
    {
      num: "3",
      icon: "💳",
      title: "Amazon ou Pix (Independente)",
      desc: "Você decide separadamente: pode comprar pela Amazon ou transferir o valor por Pix para cada um dos dois produtos.",
    },
    {
      num: "4",
      icon: "📲",
      title: "Envio de Comprovantes",
      desc: "Após reservar, você tem até 72 horas para mandar os 2 comprovantes pelo WhatsApp para confirmação pelo casal.",
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
            Como Funciona a Participação
          </h2>
          <p className="text-xs sm:text-sm text-[#29343A]/80">
            É muito fácil e rápido garantir seu número e demonstrar seu carinho pelo Lael.
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
