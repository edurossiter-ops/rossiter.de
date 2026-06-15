#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lista os slugs reais das acoes (tools) do toolkit instagram no Composio."""
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

for url in (f"{BASE}/tools?toolkit_slugs=instagram&limit=200",
            f"{BASE}/tools?toolkit_slug=instagram&limit=200"):
    st, raw = get(url)
    print("== GET", url, "==", st)
    try:
        d = json.loads(raw)
        items = d.get("items") or d.get("data") or []
        slugs = []
        for it in items:
            s = it.get("slug") or it.get("name") or it.get("enum")
            if s: slugs.append(s)
        print("TOTAL:", len(slugs))
        for s in sorted(slugs):
            print("  ", s)
    except Exception as e:
        print("parse err", e, raw[:500])
    print("----")
    if st == 200:
        break
