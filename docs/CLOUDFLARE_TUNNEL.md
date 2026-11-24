# Cloudflare Tunnel — publicação pública

Publica o site sem abrir portas no roteador/firewall. O `cloudflared` roda como serviço opcional do compose.

## Arquitetura

```
Visitante → rifa.seudominio.com.br (Cloudflare)
         → Cloudflare Tunnel (cloudflared no container)
         → http://frontend:3000  (rede Docker interna)
         → /api/* → backend:8000 (proxy interno do Next.js)
```

O backend **não precisa** de hostname público — o frontend faz proxy de `/api`.

## Passo a passo

1. **Criar o Tunnel** no dashboard Cloudflare: *Zero Trust → Networks → Tunnels → Create a tunnel* (cloudflared). Copie o **token** exibido.
2. **Configurar o hostname público** na aba *Public Hostname* do tunnel:
   - Subdomain: `rifa` · Domain: `seudominio.com.br`
   - Service: `HTTP` → `frontend` · Port: `3000`
   (ou aponte para `http://frontend:3000` — o DNS `rifa.seudominio.com.br` é criado automaticamente como CNAME do tunnel)
3. **No `.env` da VM:**
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=<token copiado>
   ```
4. **Subir com o profile:**
   ```bash
   docker compose --profile tunnel up -d
   docker compose logs -f cloudflared   # deve mostrar "Registered tunnel connection"
   ```
5. Acesse `https://rifa.seudominio.com.br` — o Cloudflare já termina TLS; **não é preciso** o Caddy/proxy nem portas 80/443 abertas.

## Notas

- Sem `CLOUDFLARE_TUNNEL_TOKEN`, o serviço `cloudflared` simplesmente não sobe (profile inativo) — a app funciona normal em rede local.
- Se quiser HTTPS próprio via domínio (sem Cloudflare), use o serviço `proxy` (Caddy) com `SITE_DOMAIN=seudominio.com.br` no `.env` — ele emite certificado Let's Encrypt automaticamente.
- Diagnóstico: `docker compose logs cloudflared`; métricas em `https://<tunnel-id>.cfargotunnel.com/metrics`.
- **Nunca** commite o token — ele fica só no `.env` da VM.
