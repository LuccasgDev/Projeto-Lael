/** Formata valores monetários em Real brasileiro (centavos → "R$ 12,34"). */
export function formatBRL(value: number | string): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  return `R$ ${n.toFixed(2).replace(".", ",")}`;
}
