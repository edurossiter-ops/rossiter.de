# Rossiter Consulting — site (redesign v2)

Site estático (HTML/CSS/JS vanilla, sem build) na nova identidade visual ("Instrumento × convergência"). Substitui a estética azul-elétrico/preto/clone-Accenture do site anterior.

## Estrutura
```
index.html · sgi.html · auditoria.html · opex.html · formacao.html · 404.html
assets/   styles.css · app.js · og-cover.png · Video_Hero.mp4 · img-*.jpg · rossiter-logo.png
robots.txt · sitemap.xml · llms.txt
```

## Stack
- HTML/CSS/JS puro. Fontes via Google Fonts (IBM Plex Sans / Sans Condensed / Mono). Formulário via Formspree.
- Sem dependências, sem build. Serve direto em qualquer host estático (GitHub Pages, Netlify, etc.).

## Deploy — STAGING (GitHub Pages, não toca no rossiter.de)
1. Criar um repositório **separado** de staging (ex.: `rossiter-site-staging`).
2. `git remote add origin <url-do-repo>` · `git branch -M main` · `git push -u origin main`
3. GitHub → Settings → Pages → Source: `main` / `/ (root)`. URL: `https://<user>.github.io/<repo>/`.
4. `robots.txt` já está em **noindex** (`Disallow: /`) — staging não vai pro índice. `canonical` de todas as páginas aponta para `rossiter.de` (produção).

> O `gh` CLI não estava instalado no ambiente de geração; o commit inicial foi feito localmente, o push é autenticado por você.

## Promoção para PRODUÇÃO (rossiter.de)
1. Trocar `robots.txt` para a versão de produção (comentada no topo do arquivo: `Allow: /` + `Sitemap`).
2. Adicionar arquivo `CNAME` na raiz com o conteúdo `rossiter.de` e apontar o DNS (registro CNAME/ALIAS) para o GitHub Pages.
3. Conferir `og-cover.png`, `sitemap.xml` e `canonical` (já em `https://rossiter.de/`).

## Identidade & conteúdo (fontes)
Identidade visual: `../../branding/identity/` (DESIGN.md/PRODUCT.md em `../../branding/`). Copy: `_copy/copy-deck.md` (não versionado).
