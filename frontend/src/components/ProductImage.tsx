"use client";

import { useState } from "react";

interface ProductImageProps {
  src?: string | null;
  alt: string;
  /** Classes do container quadrado (ex.: "w-14 h-14 rounded-xl ...") */
  className?: string;
  /** Emoji/conteúdo exibido quando não há imagem ou a URL falha */
  fallback?: React.ReactNode;
}

/**
 * Imagem de produto com fallback elegante:
 * - sem URL ou URL inválida/quebrada → mostra o fallback (nunca imagem quebrada)
 * - object-contain para não cortar embalagens
 * - loading lazy para não pesar a página
 */
export default function ProductImage({ src, alt, className = "", fallback = "🎁" }: ProductImageProps) {
  const [failed, setFailed] = useState(false);

  const base = `flex items-center justify-center overflow-hidden ${className}`;

  if (!src || failed) {
    return <div className={`${base} bg-slate-50 border border-slate-100`}><span className="text-2xl">{fallback}</span></div>;
  }

  return (
    <div className={`${base} bg-white border border-slate-100`}>
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onError={() => setFailed(true)}
        className="object-contain w-full h-full p-1"
      />
    </div>
  );
}
