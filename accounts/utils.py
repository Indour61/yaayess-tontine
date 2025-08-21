from django.conf import settings

def envoyer_invitation(phone, lien):
    """
    Simule l'envoi d'un lien d'invitation par WhatsApp ou SMS.
    (À remplacer par une intégration réelle avec Twilio, WhatsApp API ou autre)
    """
    print(f"📲 Envoi d'invitation à {phone} avec le lien : {lien}")
    # TODO : Implémenter l'envoi réel via Twilio, SMS API ou WhatsApp Cloud API
