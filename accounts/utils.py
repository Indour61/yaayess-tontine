from django.conf import settings
import random
import string

def envoyer_invitation(phone, lien):
    """
    Simule l'envoi d'un lien d'invitation par WhatsApp ou SMS.
    (À remplacer par une intégration réelle avec Twilio, WhatsApp API ou autre)
    """
    print(f"📲 Envoi d'invitation à {phone} avec le lien : {lien}")
    # TODO : Implémenter l'envoi réel via Twilio, SMS API ou WhatsApp Cloud API

def generate_alias(nom):
    """
    Génère un alias unique basé sur le nom + 4 caractères aléatoires.
    Exemple : Fatou -> Fatou-AB12
    """
    suffixe = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    base = ''.join(e for e in nom if e.isalnum())  # supprime les espaces et caractères spéciaux
    return f"{base}-{suffixe}"


