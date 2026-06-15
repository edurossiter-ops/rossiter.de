#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump dos parametros de entrada dos slugs corretos."""
import os, json, urllib.request, urllib.error
BASE = "https://backend.composio.dev/api/v3"
KEY = os.environ.get("COMPOSIO_API_KEY")
H = {"x-api-key": KEY, "Content-Type": "application/json"}
def get(url):
    req = urllib.request.Request(url, method="GET", headers=H)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
for slug in ["INSTAGRAM_CREATE_MEDIA_CONTAINER","INSTAGRAM_CREATE_POST"]:
    st, raw = get(f"{BASE}/tools/{slug}")
    print("==", slug, st, "==")
    try:
        d = json.loads(raw)
        params = d.get("input_parameters") or d.get("inputParameters") or d.get("parameters") or {}
        props = params.get("properties", params) if isinstance(params, dict) else {}
        req = params.get("required", []) if isinstance(params, dict) else []
        print("required:", req)
        for k, v in props.items():
            desc = (v.get("description","")[:70] if isinstance(v, dict) else "")
            print(f"   {k}: {desc}")
    except Exception as e:
        print("parse err", e, raw[:800])
