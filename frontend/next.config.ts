import type { NextConfig } from "next";

// URL interna do backend dentro da rede Docker (nunca exposta ao browser).
// O browser chama same-origin /api → o Next faz proxy server-side → backend.
const BACKEND_INTERNAL_URL = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_INTERNAL_URL}/api/:path*` },
      { source: "/docs", destination: `${BACKEND_INTERNAL_URL}/docs` },
      { source: "/docs/:path*", destination: `${BACKEND_INTERNAL_URL}/docs/:path*` },
      { source: "/redoc", destination: `${BACKEND_INTERNAL_URL}/redoc` },
      { source: "/redoc/:path*", destination: `${BACKEND_INTERNAL_URL}/redoc/:path*` },
      { source: "/openapi.json", destination: `${BACKEND_INTERNAL_URL}/openapi.json` },
    ];
  },
};

export default nextConfig;
