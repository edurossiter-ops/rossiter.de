#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Descobre os slugs reais das acoes instagram: testa GET /tools/{slug} para
candidatos e lista os tools do toolkit instagram com filtro correto."""
import os, json, urllib.request, urllib.error

BASE = "https://backend.composio.dev/api/v3"
KEY = os.environ.get("COMPOSIO_API_KEY")
H = {"x-api-key": KEY, "Content-Type": "application/json"}

def get(url):
    req = urllib.request.Request(url, method="GET", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1) filtro correto do toolkit (varias variantes)
for q in ("toolkit_slugs=INSTAGRAM", "toolkitSlugs=instagram", "toolkit=instagram", "toolkits=instagram"):
    st, raw = get(f"{BASE}/tools?{q}&limit=100")
    try:
        d = json.loads(raw); items = d.get("items") or d.get("data") or []
        slugs = [ (it.get("slug") or it.get("name")) for it in items ]
        ig = [s for s in slugs if s and s.upper().startswith("INSTAGRAM")]
        print(f"[{q}] status={st} total={len(slugs)} instagram={len(ig)}")
        if ig:
            for s in sorted(ig): print("   ", s)
            break
    except Exception as e:
        print(f"[{q}] status={st} parse_err {e}")

# 2) checa candidatos por GET /tools/{slug}
print("== checagem por slug ==")
for slug in ["INSTAGRAM_POST_IG_USER_MEDIA","INSTAGRAM_CREATE_MEDIA_CONTAINER",
             "INSTAGRAM_CREATE_MEDIA","INSTAGRAM_MEDIA","INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
             "INSTAGRAM_CREATE_POST","INSTAGRAM_MEDIA_PUBLISH","INSTAGRAM_PUBLISH_MEDIA",
             "INSTAGRAM_GET_USER_INFO"]:
    st, raw = get(f"{BASE}/tools/{slug}")
    print(f"   {slug}: {st}")
