from django.conf import settings
from twilio.rest import Client

from django.conf import settings

def envoyer_invitation(phone, lien):
    # Simulation locale pour éviter l'erreur
    if not hasattr(settings, "TWILIO_ACCOUNT_SID") or not settings.TWILIO_ACCOUNT_SID:
        print(f"[SIMULATION] Invitation envoyée à {phone} avec le lien : {lien}")
        return

    # Sinon, ici tu mets ton vrai code Twilio
    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # message = client.messages.create(
    #     body=f"Bonjour ! Voici votre lien d'invitation : {lien}",
    #     from_=settings.TWILIO_PHONE_NUMBER,
    #     to=phone
    # )
    # return message.sid

