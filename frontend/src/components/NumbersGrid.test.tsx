import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import NumbersGrid from "@/components/NumbersGrid";
import StatusBadge from "@/components/StatusBadge";
import { formatBRL } from "@/lib/format";
import { GridItem } from "@/lib/api";

const grid: GridItem[] = [
  { id: 1, numero: 1, status: "disponivel", produto_nome: "Berço Portátil" },
  { id: 2, numero: 2, status: "reservado", nome_publico: "Ana S.", produto_nome: "Carrinho" },
  { id: 3, numero: 3, status: "confirmado", produto_nome: "Babá Eletrônica" },
];

describe("NumbersGrid (RN-03)", () => {
  it("renderiza a legenda sempre visível com os três estados", () => {
    render(<NumbersGrid numbers={grid} isLoading={false} onSelectNumber={() => {}} />);
    expect(screen.getByText("Disponível", { selector: "[class*='text-emerald-900']" })).toBeTruthy();
    expect(screen.getByText("Reservado", { selector: "[class*='text-amber-900']" })).toBeTruthy();
    expect(screen.getByText("Confirmado", { selector: "[class*='text-slate-900']" })).toBeTruthy();
  });

  it("estado aparece por TEXTO acessível, nunca só por cor", () => {
    render(<NumbersGrid numbers={grid} isLoading={false} onSelectNumber={() => {}} />);
    expect(screen.getByRole("button", { name: /número 01 — disponível/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /número 02 — reservado/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /número 03 — confirmado/i })).toBeTruthy();
  });

  it("permite selecionar número disponível e dispara callback", async () => {
    const onSelect = vi.fn();
    render(<NumbersGrid numbers={grid} isLoading={false} onSelectNumber={onSelect} />);
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /número 01/i }));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("número reservado não pode ser selecionado", () => {
    const onSelect = vi.fn();
    render(<NumbersGrid numbers={grid} isLoading={false} onSelectNumber={onSelect} />);
    const reservado = screen.getByRole("button", { name: /número 02/i });
    expect(reservado).toHaveAttribute("disabled");
    fireEvent.click(reservado);
    expect(onSelect).not.toHaveBeenCalled();
  });
});

describe("StatusBadge (RN-03: texto + ícone, nunca só cor)", () => {
  it("mostra 'Aguardando comprovantes' para reserva ativa", () => {
    render(<StatusBadge status="reservada" />);
    const badge = screen.getByTestId("status-badge");
    expect(badge).toHaveTextContent("Aguardando comprovantes");
  });

  it("mostra 'Confirmada' para reserva confirmada", () => {
    render(<StatusBadge status="confirmada" />);
    expect(screen.getByTestId("status-badge")).toHaveTextContent("Confirmada");
  });

  it("mostra estado expirado/liberado", () => {
    render(<StatusBadge status="expirada" />);
    expect(screen.getByTestId("status-badge")).toHaveTextContent("Expirada ou liberada");
  });
});

describe("formatBRL (§7: dinheiro nunca em float solto na exibição)", () => {
  it("formata centavos corretamente", () => {
    expect(formatBRL(12.5)).toBe("R$ 12,50");
    expect(formatBRL(489.9)).toBe("R$ 489,90");
    expect(formatBRL("1000.00")).toBe("R$ 1000,00");
  });
});
