from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Notification

from django.core.mail import send_mail
from django.conf import settings


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
        print("Erreur Notification :", e)

    # =========================
    # 📱 SMS (simulation)
    # =========================
    try:
        from utils.sms import send_sms_notification
        if phone:
            send_sms_notification(instance)
    except Exception as e:
        print("Erreur SMS :", e)

    # =========================
    # 📧 EMAIL ADMIN
    # =========================
    try:
        send_mail(
            "🚀 Nouveau utilisateur YaayESS",
            f"""
Un nouvel utilisateur vient de s'inscrire :

📱 Téléphone : {phone}
📧 Email : {email if email else 'Non renseigné'}

👉 Vérifiez dans votre dashboard.
""",
            settings.EMAIL_HOST_USER,
            ["indour787@hotmail.com"],
            fail_silently=True,
        )
    except Exception as e:
        print("Erreur Email Admin :", e)

    # =========================
    # 📧 EMAIL UTILISATEUR
    # =========================
    if email:
        try:
            send_mail(
                "🎉 Bienvenue sur YaayESS",
                f"""
Bonjour 👋

Votre inscription est réussie ✅

📱 Téléphone : {phone}

Bienvenue sur YaayESS !
Plateforme de gestion d’épargne et tontine 💰

Merci pour votre confiance 🙏
""",
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=True,
            )
        except Exception as e:
            print("Erreur Email User :", e)

