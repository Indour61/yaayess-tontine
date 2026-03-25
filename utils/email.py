from django.core.mail import EmailMultiAlternatives
from django.conf import settings

# =========================================
# 📧 EMAIL BIENVENUE
# =========================================
def send_welcome_email(user):
    if not user.email:
        return

    subject = "🎉 Bienvenue sur YaayESS"
    from_email = settings.EMAIL_HOST_USER
    to = [user.email]

    text = "Bienvenue sur YaayESS"

    html = f"""
    <div style="font-family:Arial, sans-serif; padding:20px;">
        <h2 style="color:#2e7d32;">Bienvenue sur YaayESS 🎉</h2>

        <p>Votre inscription est confirmée ✅</p>

        <p><strong>Téléphone :</strong> {user.phone}</p>

        <p>
            YaayESS vous permet de gérer vos tontines,
            épargne et crédits facilement 💰
        </p>

        <a href="https://yaayess.com"
           style="background:#2e7d32;color:white;padding:10px 20px;
           text-decoration:none;border-radius:5px;display:inline-block;margin-top:10px;">
           Accéder à la plateforme
        </a>

        <hr style="margin-top:20px;">

        <small style="color:gray;">
            YaayESS - Plateforme digitale africaine 🌍
        </small>
    </div>
    """

    try:
        msg = EmailMultiAlternatives(subject, text, from_email, to)
        msg.attach_alternative(html, "text/html")
        msg.send()
        print("📧 Email bienvenue envoyé")
    except Exception as e:
        print("Erreur email bienvenue :", e)


# =========================================
# 📧 EMAIL INVITATION GROUPE
# =========================================
def envoyer_invitation(email, lien):
    subject = "📩 Invitation à rejoindre un groupe YaayESS"
    from_email = settings.EMAIL_HOST_USER
    to = [email]

    text = f"Vous êtes invité à rejoindre un groupe YaayESS : {lien}"

    html = f"""
    <div style="font-family:Arial, sans-serif; padding:20px;">
        <h2 style="color:#2e7d32;">Invitation YaayESS 📩</h2>

        <p>Vous êtes invité à rejoindre un groupe sur YaayESS.</p>

        <a href="{lien}"
           style="background:#2e7d32;color:white;padding:10px 20px;
           text-decoration:none;border-radius:5px;">
           Rejoindre le groupe
        </a>

        <p style="margin-top:15px;">
            Ou copiez ce lien :<br>
            <small>{lien}</small>
        </p>
    </div>
    """

    try:
        msg = EmailMultiAlternatives(subject, text, from_email, to)
        msg.attach_alternative(html, "text/html")
        msg.send()
        print(f"📧 Invitation envoyée à {email}")
    except Exception as e:
        print("Erreur email invitation :", e)