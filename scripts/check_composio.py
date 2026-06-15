#!/usr/bin/env python3
"""Teste de conectividade com o Composio.
Chama INSTAGRAM_GET_USER_INFO via API REST do Composio usando a COMPOSIO_API_KEY
(secret) e o connected_account_id. Se retornar o perfil, o acesso esta OK.
"""
import os, json, sys, urllib.request, urllib.error

BASE = "https://backend.composio.dev/api/v3"
ACTION = "INSTAGRAM_GET_USER_INFO"
CONN = os.environ.get("IG_CONNECTED_ACCOUNT_ID", "ac_Jb2VYl-UeLkh")
key = os.environ.get("COMPOSIO_API_KEY")

if not key:
    print("ERRO: COMPOSIO_API_KEY ausente no ambiente.")
    sys.exit(2)

url = f"{BASE}/tools/execute/{ACTION}"
body = json.dumps({
    "connected_account_id": CONN,
    "arguments": {"ig_user_id": "me"},
}).encode()

req = urllib.request.Request(
    url, data=body, method="POST",
    headers={"x-api-key": key, "Content-Type": "application/json"},
)

try:
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        print("HTTP", r.status)
        print(raw)
        data = json.loads(raw)
        # estruturas possiveis: {data:{...}} ou {data:{response_data:{...}}}
        ok = json.dumps(data).find("rossiterconsulting") >= 0 or data.get("successful") or data.get("successfull")
        print("ACESSO_OK" if ok else "ACESSO_DUVIDOSO")
        sys.exit(0 if ok else 1)
except urllib.error.HTTPError as e:
    print("HTTP_ERROR", e.code)
    print(e.read().decode())
    sys.exit(1)
except Exception as e:
    print("EXC", repr(e))
    sys.exit(1)
