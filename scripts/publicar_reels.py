#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publica Reels devidos no Instagram @rossiterconsulting via Composio.

Le reels/manifest.json (agenda) e reels/published.json (estado). Para cada post cujo
publish_at <= agora e que ainda nao foi publicado: cria o container e publica.
Em caso de erro, espera 5 min e tenta de novo, ate um teto de tentativas.
Idempotente: grava o slot em published.json apos sucesso.

DOIS TRANSPORTES (a Composio remove/renomeia slugs sem aviso):
  1. MCP (endpoint /v3/mcp/.../mcp): tem as slugs novas INSTAGRAM_POST_IG_USER_MEDIA /
     INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH, que aceitam 'collaborators'. E o principal.
  2. REST (endpoint /api/v3/tools/execute): so tem as antigas
     INSTAGRAM_CREATE_MEDIA_CONTAINER / INSTAGRAM_CREATE_POST (SEM colaboradores).
     E o fallback: garante que SEMPRE publica, mesmo se o MCP cair.
O fallback so acontece na CRIACAO do container (nada publicado ainda) -> sem risco de duplicar.

Env:
  COMPOSIO_API_KEY  (obrigatorio) -- chave do projeto com o toolkit novo (ak_...)
  COMPOSIO_USER_ID  (default RossiterConsulting)
  IG_CONNECTED_ACCOUNT_ID (default ca_C8RaGOzsCic0)  -- usado so no fallback REST
  COMPOSIO_MCP_URL  (default: servidor MCP cf910f90)  -- override opcional
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
MCP_URL = os.environ.get(
    "COMPOSIO_MCP_URL",
    "https://backend.composio.dev/v3/mcp/cf910f90-6c2e-4434-a9c8-73acfb4538d3/mcp?user_id=" + USER,
)

RETRY_WAIT_S = 300        # 5 min entre tentativas
MAX_ATTEMPTS = 12         # teto: ~1h por slot


def log(*a):
    print(*a, flush=True)


def _ok(res):
    return bool(res.get("successful") or res.get("successfull"))


def _extract_id(res):
    d = res.get("data", {}) or {}
    return d.get("id") or (d.get("response_data", {}) or {}).get("id") or d.get("creation_id")


# ---------------------------------------------------------------- REST (fallback)
class ApiError(RuntimeError):
    def __init__(self, action, code, body):
        self.action, self.code, self.body = action, code, body
        super().__init__(f"HTTP {code} em {action}: {body[:400]}")


def execute(action, arguments):
    """Chama uma tool pelo endpoint REST tools/execute (slugs antigas, sem colaboradores)."""
    body = json.dumps({"user_id": USER, "connected_account_id": CONN, "arguments": arguments}).encode()
    req = urllib.request.Request(f"{BASE}/tools/execute/{action}", data=body, method="POST",
                                 headers={"x-api-key": KEY, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=320) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ApiError(action, e.code, e.read().decode())


# ---------------------------------------------------------------- MCP (principal)
_MCP_HEADERS = {"x-api-key": KEY or "", "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"}
_mcp_ready = False


def _mcp_post(payload, timeout):
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), method="POST",
                                 headers=_MCP_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode()


def _mcp_parse(body):
    # a resposta pode vir como JSON puro ou SSE ("data: {...}")
    if body.lstrip().startswith("{"):
        return json.loads(body)
    for ln in body.splitlines():
        ln = ln.strip()
        if ln.startswith("data:"):
            return json.loads(ln[5:].strip())
    raise RuntimeError(f"resposta MCP inesperada: {body[:300]}")


def _mcp_init():
    global _mcp_ready
    if _mcp_ready:
        return
    _mcp_post({"jsonrpc": "2.0", "id": "init", "method": "initialize",
               "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                          "clientInfo": {"name": "reels", "version": "1"}}}, 60)
    try:
        _mcp_post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, 30)
    except Exception:
        pass
    _mcp_ready = True


def mcp_call(slug, arguments, timeout=240):
    """Chama uma tool pelo endpoint MCP. Retorna o dict de resultado da Composio
    (com 'successful'/'data'). Lanca em erro de transporte/protocolo."""
    _mcp_init()
    msg = _mcp_parse(_mcp_post({"jsonrpc": "2.0", "id": slug, "method": "tools/call",
                                "params": {"name": slug, "arguments": arguments}}, timeout))
    if msg.get("error"):
        raise RuntimeError(f"MCP erro em {slug}: {json.dumps(msg['error'])[:300]}")
    result = msg.get("result", {}) or {}
    content = result.get("content") or []
    if content and isinstance(content, list) and content[0].get("type") == "text":
        try:
            return json.loads(content[0]["text"])
        except Exception:
            return {"_text": content[0]["text"]}
    if result.get("structuredContent"):
        return result["structuredContent"]
    raise RuntimeError(f"MCP sem conteudo em {slug}: {json.dumps(result)[:300]}")


# ---------------------------------------------------------------- publicacao
def _create_container(post):
    """Cria o container. Tenta MCP (com colaboradores); se o transporte MCP falhar,
    cai pro REST antigo (sem colaboradores). Retorna (creation_id, transport, com_colab)."""
    base = {"ig_user_id": "me", "media_type": "REELS",
            "video_url": post["video_url"], "cover_url": post["cover_url"], "caption": post["caption"]}
    colab = (post.get("colaboradores") or [])[:3]   # API: maximo 3 colaboradores

    # 1) MCP -- slug nova, com colaboradores
    try:
        args = dict(base)
        if colab:
            args["collaborators"] = colab
        res = mcp_call("INSTAGRAM_POST_IG_USER_MEDIA", args)
        if _ok(res):
            cid = _extract_id(res)
            if cid:
                return cid, "mcp", bool(colab)
        log(f"    MCP create sem sucesso: {json.dumps(res)[:200]}")
    except Exception as e:
        log(f"    MCP create indisponivel ({str(e)[:160]}) -> fallback REST")

    # 2) REST -- slug antiga, SEM colaboradores (rede de seguranca)
    res = execute("INSTAGRAM_CREATE_MEDIA_CONTAINER", base)
    if not _ok(res):
        raise RuntimeError(f"REST create falhou: {json.dumps(res)[:300]}")
    cid = _extract_id(res)
    if not cid:
        raise RuntimeError(f"REST create sem id: {json.dumps(res)[:300]}")
    if colab:
        log("    AVISO: publicado via fallback REST -> SEM colaboradores (slug nova indisponivel)")
    return cid, "rest", False


def _publish_container(creation_id, transport):
    """Publica o container (mesmo creation_id em todas as tentativas -> idempotente).
    Reels demora a processar -> tenta ate ~5 min em passos de 20s."""
    last = None
    for i in range(15):
        try:
            if transport == "mcp":
                res = mcp_call("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
                               {"ig_user_id": "me", "creation_id": creation_id,
                                "max_wait_seconds": 120, "poll_interval_seconds": 5})
            else:
                res = execute("INSTAGRAM_CREATE_POST", {"ig_user_id": "me", "creation_id": creation_id})
            if _ok(res):
                return _extract_id(res)
            last = json.dumps(res)[:300]
        except Exception as e:
            last = str(e)[:300]
        log(f"    aguardando processamento ({i+1}/15)... [{last}]")
        time.sleep(20)
    raise RuntimeError(f"publish nao concluiu: {last}")


def publish_one(post):
    creation_id, transport, com_colab = _create_container(post)
    log(f"    container criado ({transport}, colaboradores={com_colab}): {creation_id}")
    media_id = _publish_container(creation_id, transport)
    log(f"    PUBLICADO ({transport}): media_id={media_id}")
    return media_id


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
