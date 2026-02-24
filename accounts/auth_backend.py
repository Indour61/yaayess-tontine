from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class PhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifie en utilisant le champ phone
        SimpleJWT envoie username=..., donc on le traite comme phone
        """

        phone = username  # SimpleJWT envoie username, pas phone

        if phone is None or password is None:
            return None

        try:
            user = UserModel.objects.get(phone=phone)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

