#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test PayDunya (DEV / SANDBOX FORCÉ)
-----------------------------------
Usage:
  python test_paydunya.py

Prérequis:
  pip install requests python-dotenv
  .env avec:
    PAYDUNYA_MASTER_KEY=...
    PAYDUNYA_PRIVATE_KEY=...
    PAYDUNYA_TOKEN=...
    PAYDUNYA_ENV=sandbox   (optionnel ici, l'endpoint est de toute façon forcé sandbox)
"""

import os
import json
import requests

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass

SANDBOX_URL = "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create"

def _tail(v, n=4):
    if not v:
        return None
    return v[-n:] if len(v) >= n else v

def _mask(v):
    if not v:
        return "[MISSING]"
    return ("*" * max(0, len(v) - 4)) + v[-4:]

def _has_trailing_ws(v: str) -> bool:
    if not v:
        return False
    return (v.endswith(" ") or v.endswith("\t") or v.endswith("\r") or v.endswith("\n"))

def _has_non_printable(v: str) -> bool:
    if not v:
        return False
    for ch in v:
        if ord(ch) < 32 and ch not in ("\r", "\n", "\t"):
            return True
        if 0x2000 <= ord(ch) <= 0x200F:
            return True
        if 0xFEFF == ord(ch):
            return True
    return False

def main():
    raw_master = os.getenv("PAYDUNYA_MASTER_KEY", "")
    raw_private = os.getenv("PAYDUNYA_PRIVATE_KEY", "")
    raw_token = os.getenv("PAYDUNYA_TOKEN", "")

    master = raw_master.strip()
    private = raw_private.strip()
    token = raw_token.strip()

    print("🔎 Diagnostic (clés masquées) — ENV DEV (SANDBOX):")
    print(f"  MASTER:  {_mask(master)}  len={len(master)}  tail={_tail(master)}"
          f"  trailing_ws={_has_trailing_ws(raw_master)}  non_printable={_has_non_printable(raw_master)}")
    print(f"  PRIVATE: {_mask(private)}  len={len(private)}  tail={_tail(private)}"
          f"  trailing_ws={_has_trailing_ws(raw_private)} non_printable={_has_non_printable(raw_private)}")
    print(f"  TOKEN:   {_mask(token)}    len={len(token)}    tail={_tail(token)}"
          f"  trailing_ws={_has_trailing_ws(raw_token)}   non_printable={_has_non_printable(raw_token)}")

    # Vérifs minimales
    missing = []
    if not master:  missing.append("PAYDUNYA_MASTER_KEY")
    if not private: missing.append("PAYDUNYA_PRIVATE_KEY")
    if not token:   missing.append("PAYDUNYA_TOKEN")
    if missing:
        print(f"❌ Variables manquantes: {', '.join(missing)}")
        raise SystemExit(2)

    # Avertissement utile: en sandbox, la PRIVATE est souvent de forme 'test_private_...'
    if not private.lower().startswith("test_private_"):
        print("⚠️ PRIVATE sans préfixe 'test_private_' — vérifie que tu utilises bien la PRIVATE de TEST (Sandbox).")

    headers = {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": master,
        "PAYDUNYA-PRIVATE-KEY": private,
        "PAYDUNYA-TOKEN": token,
    }

    # Montant faible pour dev; ajuste la description si tu veux.
    payload = {
        "invoice": {
            "total_amount": 1000,  # 1000 FCFA (test)
            "description": "Test YaayESS DEV (sandbox)",
        },
        "store": {
            "name": "YaayESS",
        }
    }

    print("\n⏳ Envoi de la requête (SANDBOX) à PayDunya...")
    try:
        resp = requests.post(SANDBOX_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException as e:
        print(f"❌ Erreur réseau: {e}")
        raise SystemExit(3)

    print(f"✅ Statut HTTP : {resp.status_code}")
    text = resp.text or ""
    try:
        data = resp.json()
        print("🧾 Réponse JSON PayDunya :")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        code = data.get("response_code")
        text_msg = data.get("response_text")

        if code == "00":
            print("\n🎉 Succès DEV (sandbox): Checkout créé.")
            print("   ➜ URL (sandbox) attendue dans response_text, token sandbox dans 'token'.")
            raise SystemExit(0)

        # Erreurs fréquentes
        if code == "1001":
            print("\n❌ Invalid Masterkey Specified (1001).")
            print("   ➜ Vérifie que la MASTER correspond à l’app et n’a pas d’espace/char caché.")
            print("   ➜ Assure-toi que tu utilises PRIVATE/TOKEN *sandbox* pour l’endpoint sandbox.")
            raise SystemExit(4)

        print(f"\n❌ Erreur PayDunya: code={code} msg={text_msg}")
        raise SystemExit(5)

    except ValueError:
        print("ℹ️ Réponse brute (non-JSON):")
        print(text[:1000])
        print("\n❌ Réponse non JSON: vérifie l’endpoint sandbox et les headers.")
        raise SystemExit(6)

if __name__ == "__main__":
    main()

