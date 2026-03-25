from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Notification

from django.core.mail import send_mail
from django.conf import settings

from utils.email import send_welcome_email


@receiver(post_save, sender=CustomUser)
def notify_new_user(sender, instance, created, **kwargs):
    if not created:
        return

    phone = getattr(instance, "phone", None)
    email = getattr(instance, "email", None)

    print(f"📱 Nouveau user inscrit : {phone}")

    # =========================
    # 🔔 NOTIFICATION DASHBOARD
    # =========================
    try:
        Notification.objects.create(
            message=f"Nouveau utilisateur : {phone}"
        )
    except Exception as e:
        print("❌ Erreur Notification :", e)

    # =========================
    # 📱 SMS (simulation)
    # =========================
    try:
        from utils.sms import send_sms_notification
        if phone:
            send_sms_notification(instance)
    except Exception as e:
        print("❌ Erreur SMS :", e)

    # =========================
    # 💬 WHATSAPP
    # =========================
    try:
        from utils.whatsapp import send_whatsapp_message

        if phone:
            message = f"""
🎉 Bienvenue sur YaayESS !

Votre compte est activé ✅

📱 Numéro : {phone}

Vous pouvez maintenant :
✔ gérer votre tontine
✔ suivre vos cotisations
✔ demander un crédit

👉 https://yaayess.com
"""
            send_whatsapp_message(phone, message)

    except Exception as e:
        print("❌ Erreur WhatsApp :", e)

    # =========================
    # 📧 EMAIL ADMIN
    # =========================
    try:
        send_mail(
            subject="🚀 Nouveau utilisateur YaayESS",
            message=f"""
Un nouvel utilisateur vient de s'inscrire :

📱 Téléphone : {phone}
📧 Email : {email if email else 'Non renseigné'}

👉 Vérifiez dans votre dashboard.
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=["indour787@hotmail.com"],
            fail_silently=True,
        )
        print("📧 Email admin envoyé")
    except Exception as e:
        print("❌ Erreur Email Admin :", e)

    # =========================
    # 📧 EMAIL UTILISATEUR
    # =========================
    try:
        if email:
            print("📧 Envoi email bienvenue...")
            send_welcome_email(instance)
        else:
            print("ℹ️ Pas d'email utilisateur → pas d'envoi")
    except Exception as e:
        print("❌ Erreur Email Bienvenue :", e)