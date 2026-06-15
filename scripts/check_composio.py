#!/usr/bin/env python3
"""Lista as conexoes que a COMPOSIO_API_KEY enxerga, para achar a do Instagram
(id real + user/entity id). Depois testa a execucao."""
import os, json, sys, urllib.request, urllib.error

BASE = "https://backend.composio.dev/api/v3"
key = os.environ.get("COMPOSIO_API_KEY")
if not key:
    print("ERRO: COMPOSIO_API_KEY ausente."); sys.exit(2)
H = {"x-api-key": key, "Content-Type": "application/json"}

def call(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# lista todas as conexoes visiveis por essa key
for url in (f"{BASE}/connected_accounts", f"{BASE}/connected_accounts?toolkit_slugs=instagram"):
    st, raw = call("GET", url)
    print("== GET", url, "==", st)
    print(raw[:4000])
    print("----")
