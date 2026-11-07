"use client";

import { useEffect, useState, useCallback } from "react";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import RulesSection from "@/components/RulesSection";
import NumbersGrid from "@/components/NumbersGrid";
import ReservationModal from "@/components/ReservationModal";
import Footer from "@/components/Footer";
import {
  fetchPublicConfig, fetchNumbersGrid, fetchNumberDetail,
  fetchAvailableMimos, PublicConfig, GridItem, NumeroDetail, Mimo
} from "@/lib/api";

export default function Home() {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  const [numbers, setNumbers] = useState<GridItem[]>([]);
  const [mimos, setMimos] = useState<Mimo[]>([]);
  const [isLoadingGrid, setIsLoadingGrid] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedNumberDetail, setSelectedNumberDetail] = useState<NumeroDetail | null>(null);

  const loadData = useCallback(async () => {
    try {
      setIsLoadingGrid(true);
      const [cfg, grid, mimoList] = await Promise.all([
        fetchPublicConfig().catch(() => null),
        fetchNumbersGrid().catch(() => []),
        fetchAvailableMimos().catch(() => []),
      ]);
      if (cfg) setConfig(cfg);
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

  return (
    <div className="min-h-screen flex flex-col bg-[#FFF8F0]">
      <Navbar />

      <main className="flex-1">
        <Hero onChooseNumber={handleScrollToNumbers} />
        <RulesSection />
        <NumbersGrid
          numbers={numbers}
          isLoading={isLoadingGrid}
          onSelectNumber={handleSelectNumber}
        />
      </main>

      <Footer whatsapp={config?.whatsapp_casal} />

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
