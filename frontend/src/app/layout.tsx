import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Chá de Rifa do Lael 👶✨ | Fortaleza - Março 2027",
  description: "Participe do Chá de Rifa do pequeno Lael! Escolha seu número de 01 a 100, contribua com um presente ou mimo e comemore conosco este momento especial.",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>👶</text></svg>",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#42677D",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className="h-full">
      <body className="min-h-full flex flex-col bg-[#FFF8F0] text-[#29343A] selection:bg-[#B9D8E8] selection:text-[#42677D]">
        {children}
      </body>
    </html>
  );
}
