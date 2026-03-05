from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# ==========================================
# 🔹 Serializer utilisateur (API /me/)
# ==========================================
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "nom",
            "alias",
            "email",
            "option",
            "is_validated",
            "is_super_admin",
            "is_staff",
        ]


# ==========================================
# 🔹 JWT personnalisé basé sur phone
# ==========================================
class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = User.USERNAME_FIELD  # normalement "phone"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🔐 Claims personnalisés
        token["user_id"] = user.id
        token["phone"] = user.phone
        token["option"] = user.option
        token["is_super_admin"] = getattr(user, "is_super_admin", False)
        token["is_validated"] = getattr(user, "is_validated", False)

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_active:
            raise serializers.ValidationError("Compte désactivé.")

        # 🔎 Vérifie si validation requise (ex: Épargne)
        requires_validation = (
            self.user.option == "2"
            and not getattr(self.user, "is_validated", False)
        )

        data["requires_validation"] = requires_validation

        # 🔹 Données utilisateur renvoyées au frontend
        data["user"] = {
            "id": self.user.id,
            "phone": self.user.phone,
            "nom": getattr(self.user, "nom", ""),
            "alias": getattr(self.user, "alias", ""),
            "email": getattr(self.user, "email", ""),
            "option": self.user.option,
            "is_validated": getattr(self.user, "is_validated", False),
            "is_super_admin": getattr(self.user, "is_super_admin", False),
        }

        return data