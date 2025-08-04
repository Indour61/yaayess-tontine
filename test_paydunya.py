import requests
import json

# Vos clés API de test
PAYDUNYA_TEST_KEYS = {
    "master_key": "EWTNDBmX-0SOD-ZbSr-yoUd-Ir5sntAz6oPu",
    "private_key": "test_private_vrIpn4PNbHG5pv5XOrAZALAhOGc",
    "public_key": "krIuIZWRPez0Es6h6cHua6rodKy",
    "token": "LRWkyGfcnXSTvRAjUYN7",
}

# Payload de test
payload = {
    "invoice": {
        "items": [
            {
                "name": "Test Paiement",
                "quantity": 1,
                "unit_price": 1000,
                "total_price": 1000,
                "description": "Paiement de test"
            }
        ],
        "description": "Paiement TontiCollect (test)",
        "total_amount": 1000,
        "callback_url": "https://tonsite.com/paiement/callback/",
        "return_url": "https://tonsite.com/paiement/merci/"
    },
    "store": {
        "name": "TontiCollect",
        "tagline": "Collecte simplifiée",
        "website_url": "https://tonsite.com"
    },
    "custom_data": {
        "test_user_id": 123,
        "test_mode": True
    }
}

# Headers requis par PayDunya
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "PAYDUNYA-MASTER-KEY": PAYDUNYA_TEST_KEYS["master_key"],
    "PAYDUNYA-PRIVATE-KEY": PAYDUNYA_TEST_KEYS["private_key"],
    "PAYDUNYA-PUBLIC-KEY": PAYDUNYA_TEST_KEYS["public_key"],
    "PAYDUNYA-TOKEN": PAYDUNYA_TEST_KEYS["token"]
}

# Envoi de la requête
url = "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create"

print("⏳ Envoi de la requête à PayDunya...")
response = requests.post(url, headers=headers, json=payload)

print(f"✅ Statut HTTP : {response.status_code}")
try:
    data = response.json()
    print("🧾 Réponse JSON PayDunya :")
    print(json.dumps(data, indent=2))

    if data.get("response_code") == "00":
        print("\n🎉 Paiement initié avec succès !")
        print(f"➡️ URL de paiement : {data.get('response_text')}")
    else:
        print("\n❌ Erreur PayDunya :", data.get("response_text"))

except json.JSONDecodeError:
    print("❌ Erreur : La réponse n'est pas un JSON valide")
    print("Contenu brut reçu :")
    print(response.text)
