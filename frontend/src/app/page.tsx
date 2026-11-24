"use client";

import { useEffect, useState, useCallback } from "react";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import RulesSection from "@/components/RulesSection";
import NumbersGrid from "@/components/NumbersGrid";
import ReservationModal from "@/components/ReservationModal";
import Footer from "@/components/Footer";
import PrizePopup from "@/components/PrizePopup";
import { fetchSiteSettings, SiteSettings, s as sStr } from "@/lib/siteSettings";
import {
  fetchPublicConfig, fetchNumbersGrid, fetchNumberDetail,
  fetchAvailableMimos, PublicConfig, GridItem, NumeroDetail, Mimo
} from "@/lib/api";

export default function Home() {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [site, setSite] = useState<SiteSettings | null>(null);
  const [numbers, setNumbers] = useState<GridItem[]>([]);
  const [mimos, setMimos] = useState<Mimo[]>([]);
  const [isLoadingGrid, setIsLoadingGrid] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedNumberDetail, setSelectedNumberDetail] = useState<NumeroDetail | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoadingGrid(true);
      const [cfg, grid, mimoList, siteCfg] = await Promise.all([
        fetchPublicConfig().catch(() => null),
        fetchNumbersGrid().catch(() => []),
        fetchAvailableMimos().catch(() => []),
        fetchSiteSettings().catch(() => null),
      ]);
      if (cfg) setConfig(cfg);
      setSite(siteCfg);
      setNumbers(grid);
      setMimos(mimoList);
    } finally {
      setIsLoadingGrid(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // RN/§4: a grade consulta o backend periodicamente (polling a cada 12s) —
  // o backend é a fonte definitiva da disponibilidade; nunca o navegador.
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const grid = await fetchNumbersGrid();
        setNumbers(grid);
      } catch {
        // silencioso: próxima tentativa do polling tenta de novo
      }
    }, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectNumber = async (num: number) => {
    try {
      const detail = await fetchNumberDetail(num);
      setSelectedNumberDetail(detail);
      setIsModalOpen(true);
    } catch (err) {
      alert("Não foi possível carregar os detalhes do número. Tente novamente.");
    }
  };

  const handleScrollToNumbers = () => {
    const el = document.getElementById("numeros");
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handlePopupNavigate = (target: string) => {
    const el = document.getElementById(target.replace("#", ""));
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Modo de manutenção: visitantes veem aviso; reservas/admin seguem via /admin
  if (site?.sistema?.modo_manutencao) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#FFF8F0] px-6 text-center">
        <span className="text-6xl mb-4">🔧</span>
        <h1 className="text-2xl font-extrabold text-[#42677D] mb-2">Em manutenção</h1>
        <p className="text-[#29343A]/80 max-w-md">
          {sStr(site.sistema.mensagem_manutencao, "Estamos em manutenção. Voltamos em breve!")}
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#FFF8F0]">
      <Navbar />

      <main className="flex-1">
        <Hero onChooseNumber={handleScrollToNumbers} site={site} prazoHoras={config?.prazo_padrao_horas} />
        <RulesSection site={site} />
        <NumbersGrid
          numbers={numbers}
          isLoading={isLoadingGrid}
          onSelectNumber={handleSelectNumber}
        />
      </main>

      <Footer whatsapp={config?.whatsapp_casal} />

      <PrizePopup site={site} onNavigate={handlePopupNavigate} />

      <ReservationModal
        numberDetail={selectedNumberDetail}
        mimos={mimos}
        config={config}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={() => {
          loadData();
        }}
      />
    </div>
  );
}
