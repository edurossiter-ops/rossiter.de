#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publica Reels devidos no Instagram @rossiterconsulting via API REST do Composio.

Le reels/manifest.json (agenda) e reels/published.json (estado). Para cada post cujo
publish_at <= agora e que ainda nao foi publicado: cria o container e publica.
Em caso de erro, espera 5 min e tenta de novo, ate um teto de tentativas.
Idempotente: grava o slot em published.json apos sucesso.

Env:
  COMPOSIO_API_KEY  (obrigatorio)
  COMPOSIO_USER_ID  (default RossiterConsulting)
  IG_CONNECTED_ACCOUNT_ID (default ca_C8RaGOzsCic0)
  DRY_RUN=1  -> nao chama a API, so mostra o que faria
"""
import os, json, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "reels", "manifest.json")
PUBLISHED = os.path.join(ROOT, "reels", "published.json")

BASE = "https://backend.composio.dev/api/v3"
USER = os.environ.get("COMPOSIO_USER_ID", "RossiterConsulting")
CONN = os.environ.get("IG_CONNECTED_ACCOUNT_ID", "ca_C8RaGOzsCic0")
KEY = os.environ.get("COMPOSIO_API_KEY")
DRY = os.environ.get("DRY_RUN") == "1"

RETRY_WAIT_S = 300        # 5 min entre tentativas
MAX_ATTEMPTS = 12         # teto: ~1h por slot


def log(*a):
    print(*a, flush=True)


def execute(action, arguments):
    body = json.dumps({"user_id": USER, "connected_account_id": CONN, "arguments": arguments}).encode()
    req = urllib.request.Request(f"{BASE}/tools/execute/{action}", data=body, method="POST",
                                 headers={"x-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=320) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} em {action}: {e.read().decode()[:400]}")


def _extract_id(res):
    d = res.get("data", {}) or {}
    return d.get("id") or (d.get("response_data", {}) or {}).get("id") or d.get("creation_id")


def publish_one(post):
    """Cria container (CREATE_MEDIA_CONTAINER) + publica (CREATE_POST).
    Espera o video processar antes de publicar. Lanca excecao em erro."""
    args = {
        "ig_user_id": "me",
        "content_type": "reel",
        "media_type": "REELS",
        "video_url": post["video_url"],
        "cover_url": post["cover_url"],
        "caption": post["caption"],
    }
    colaboradores = post.get("colaboradores")
    if colaboradores:
        args["collaborators"] = colaboradores[:3]   # API: maximo 3 colaboradores
    res = execute("INSTAGRAM_CREATE_MEDIA_CONTAINER", args)
    if not (res.get("successful") or res.get("successfull")):
        raise RuntimeError(f"create falhou: {json.dumps(res)[:400]}")
    creation_id = _extract_id(res)
    if not creation_id:
        raise RuntimeError(f"sem creation_id: {json.dumps(res)[:400]}")
    log(f"    container criado: {creation_id}")

    # publica; reels demora a processar -> tenta ate ~5 min em passos de 20s
    last = None
    for i in range(15):
        try:
            res2 = execute("INSTAGRAM_CREATE_POST", {"ig_user_id": "me", "creation_id": creation_id})
            if res2.get("successful") or res2.get("successfull"):
                media_id = _extract_id(res2)
                log(f"    PUBLICADO: media_id={media_id}")
                return media_id
            last = json.dumps(res2)[:300]
        except Exception as e:
            last = str(e)[:300]
        log(f"    aguardando processamento ({i+1}/15)... [{last}]")
        time.sleep(20)
    raise RuntimeError(f"publish nao concluiu: {last}")


def main():
    if not KEY and not DRY:
        log("ERRO: COMPOSIO_API_KEY ausente."); sys.exit(2)
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    published = {}
    if os.path.exists(PUBLISHED):
        published = json.load(open(PUBLISHED, encoding="utf-8"))
    now = datetime.now(timezone.utc)
    log(f"agora UTC: {now.isoformat()}  | DRY_RUN={DRY}")

    due = []
    for p in manifest["posts"]:
        when = datetime.fromisoformat(p["publish_at"]).astimezone(timezone.utc)
        already = p["slot"] in published
        status = "JA_PUBLICADO" if already else ("DEVIDO" if when <= now else "futuro")
        log(f"  {p['slot']}  {p['publish_at']}  -> {status}")
        if when <= now and not already:
            due.append(p)

    if not due:
        log("Nada a publicar agora."); return

    for p in due:
        log(f"== {p['slot']} ==")
        if DRY:
            log(f"    [DRY] publicaria video={p['video_url']} capa={p['cover_url']} cap={len(p['caption'])}ch")
            continue
        ok = False
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                media_id = publish_one(p)
                published[p["slot"]] = {"media_id": media_id, "published_at_utc": datetime.now(timezone.utc).isoformat()}
                json.dump(published, open(PUBLISHED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                ok = True
                break
            except Exception as e:
                log(f"    tentativa {attempt}/{MAX_ATTEMPTS} falhou: {e}")
                if attempt < MAX_ATTEMPTS:
                    log(f"    aguardando {RETRY_WAIT_S}s...")
                    time.sleep(RETRY_WAIT_S)
        if not ok:
            log(f"    !! {p['slot']} nao publicado apos {MAX_ATTEMPTS} tentativas")
            sys.exit(1)  # falha o run; o proximo cron tenta de novo (slot segue pendente)


if __name__ == "__main__":
    main()
