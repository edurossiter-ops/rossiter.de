#!/usr/bin/env python3
"""Descobre o entity_id/user_id da conexao Instagram no Composio e testa execucao.
1) GET connected_accounts/{id} -> imprime o objeto e extrai candidatos a user/entity id.
2) Tenta INSTAGRAM_GET_USER_INFO passando connected_account_id + user_id/entity_id.
"""
import os, json, sys, urllib.request, urllib.error

BASE = "https://backend.composio.dev/api/v3"
CONN = os.environ.get("IG_CONNECTED_ACCOUNT_ID", "ac_Jb2VYl-UeLkh")
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

# 1) detalhes da conexao
st, raw = call("GET", f"{BASE}/connected_accounts/{CONN}")
print("== GET connected_account ==", st)
print(raw[:2000])
entity = None
try:
    d = json.loads(raw)
    for k in ("user_id", "entity_id", "entityId", "userId"):
        if isinstance(d, dict) and d.get(k):
            entity = d[k]; break
    if not entity and isinstance(d, dict):
        # as vezes vem aninhado
        for parent in ("data", "connectedAccount", "connected_account"):
            sub = d.get(parent) if isinstance(d.get(parent), dict) else None
            if sub:
                for k in ("user_id", "entity_id", "entityId", "userId"):
                    if sub.get(k):
                        entity = sub[k]; break
            if entity: break
except Exception as e:
    print("parse err", e)
print("ENTITY_DESCOBERTO:", entity)

# 2) testa execucao com candidatos
candidates = [c for c in [entity, "default"] if c]
for ent in candidates:
    for field in ("user_id", "entity_id"):
        body = {"connected_account_id": CONN, field: ent, "arguments": {"ig_user_id": "me"}}
        st, raw = call("POST", f"{BASE}/tools/execute/INSTAGRAM_GET_USER_INFO", body)
        print(f"== execute {field}={ent} ==", st)
        print(raw[:1500])
        if st == 200 and ("rossiterconsulting" in raw or '"successful":true' in raw or '"successfull":true' in raw):
            print("ACESSO_OK", "field=", field, "entity=", ent)
            sys.exit(0)
print("ACESSO_FALHOU")
sys.exit(1)
