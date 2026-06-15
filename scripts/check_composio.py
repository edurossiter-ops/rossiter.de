#!/usr/bin/env python3
"""Confirma execucao Composio: entity user_id=RossiterConsulting."""
import os, json, sys, urllib.request, urllib.error

BASE = "https://backend.composio.dev/api/v3"
USER = os.environ.get("COMPOSIO_USER_ID", "RossiterConsulting")
CA = os.environ.get("IG_CONNECTED_ACCOUNT_ID", "ca_C8RaGOzsCic0")
key = os.environ.get("COMPOSIO_API_KEY")
if not key:
    print("ERRO: COMPOSIO_API_KEY ausente."); sys.exit(2)
H = {"x-api-key": key, "Content-Type": "application/json"}

def execute(action, arguments, body_extra):
    body = {"user_id": USER, "arguments": arguments}
    body.update(body_extra)
    req = urllib.request.Request(f"{BASE}/tools/execute/{action}", data=json.dumps(body).encode(),
                                 method="POST", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1) auto-resolve por entity
st, raw = execute("INSTAGRAM_GET_USER_INFO", {"ig_user_id": "me"}, {})
print("== user_id only ==", st); print(raw[:1200])
ok1 = st == 200 and "rossiterconsulting" in raw

# 2) com connected_account_id especifico
st2, raw2 = execute("INSTAGRAM_GET_USER_INFO", {"ig_user_id": "me"}, {"connected_account_id": CA})
print("== user_id + connected_account_id", CA, "==", st2); print(raw2[:1200])
ok2 = st2 == 200 and "rossiterconsulting" in raw2

if ok1 or ok2:
    print("ACESSO_OK")
    sys.exit(0)
print("ACESSO_FALHOU")
sys.exit(1)
