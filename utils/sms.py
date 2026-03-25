from django.conf import settings

def send_sms_notification(user):
    # MODE DEV → simulation
    if not hasattr(settings, "TWILIO_SID"):
        print(f"📱 [SIMULATION SMS] envoyé à {user.phone}")
        return

    # MODE PROD → Twilio
    from twilio.rest import Client

    client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH)

    message = client.messages.create(
        body=f"Nouveau utilisateur YaayESS: {user.phone}",
        from_=settings.TWILIO_PHONE,
        to=user.phone
    )

    return message.sid