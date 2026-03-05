from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class PhoneBackend(ModelBackend):
    """
    Authentification avec téléphone + mot de passe.
    Le téléphone est passé via le paramètre standard `username`.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        phone = username or kwargs.get("phone")
        if phone is None or password is None:
            return None

        try:
            user = UserModel.objects.get(phone=phone)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None



