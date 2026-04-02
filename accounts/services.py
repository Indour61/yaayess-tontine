# accounts/services.py

from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client

# accounts/services.py

def send_otp(user, code):

    message = f"Votre code YaayESS est : {code}"

    # 📧 EMAIL
    if user.email:
        send_mail(
            "Code YaayESS",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True
        )

    # 📱 SMS (MODE DEV SÉCURISÉ)
    if hasattr(user, "phone") and user.phone:
        try:
            if settings.DEBUG:
                print(f"📱 [SIMULATION SMS] Code OTP: {code} → {user.phone}")
            else:
                client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN
                )

                client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=user.phone
                )

        except Exception as e:
            print("❌ Erreur SMS:", e)


from django.utils import timezone
from datetime import timedelta
from accounts.models import OTPVerification


def generate_and_send_otp(user):

    # ❌ supprimer anciens OTP
    OTPVerification.objects.filter(
        user=user,
        is_validated=False
    ).delete()

    # 🔢 générer code
    code = OTPVerification.generate_code()

    otp = OTPVerification.objects.create(
        user=user,
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    # 📩 envoyer OTP
    send_otp(user, code)

    return otp

