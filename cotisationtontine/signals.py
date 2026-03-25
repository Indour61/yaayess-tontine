from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GroupMember


@receiver(post_save, sender=GroupMember)
def send_group_invitation(sender, instance, created, **kwargs):
    if not created:
        return

    try:
        from utils.whatsapp import send_whatsapp_message

        user = instance.user
        phone = getattr(user, "phone", None)
        group_name = instance.group.nom

        if not phone:
            print("ℹ️ Pas de téléphone → pas d'invitation WhatsApp")
            return

        # 🔗 Lien invitation basé sur ton modèle Invitation
        lien = f"http://127.0.0.1:8000/join/{instance.group.code_invitation}/"

        message = f"""
👥 YaayESS

Tu as été ajouté à une tontine !

📌 Groupe : {group_name}

💰 Rejoins ici :
{lien}

Bienvenue 🚀
"""

        send_whatsapp_message(phone, message)

        print(f"💬 Invitation groupe envoyée à {phone}")

    except Exception as e:
        print("❌ Erreur invitation WhatsApp :", e)

