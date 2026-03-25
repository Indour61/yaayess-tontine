import requests


# =========================
# 💬 WHATSAPP SIMULATION
# =========================
def send_whatsapp_message(phone, message):
    print(f"💬 [SIMULATION WHATSAPP] → {phone}")
    print(message)


# =========================
# 💬 WHATSAPP API (Twilio)
# =========================
def send_whatsapp_real(phone, message):
    url = "https://api.twilio.com/2010-04-01/Accounts/YOUR_SID/Messages.json"

    data = {
        "From": "whatsapp:+14155238886",  # Twilio sandbox
        "To": f"whatsapp:+221{phone}",
        "Body": message,
    }

    auth = ("YOUR_SID", "YOUR_AUTH_TOKEN")

    response = requests.post(url, data=data, auth=auth)

    print("WhatsApp status:", response.status_code)
    print(response.text)
