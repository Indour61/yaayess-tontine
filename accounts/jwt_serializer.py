from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework import serializers


class PhoneTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'phone'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 🔥 Ajout des infos personnalisées
        token['phone'] = user.phone
        token['nom'] = user.nom
        token['option'] = user.option
        token['is_super_admin'] = user.is_super_admin
        token['is_staff'] = user.is_staff

        return token

    def validate(self, attrs):
        phone = attrs.get("phone")
        password = attrs.get("password")

        user = authenticate(username=phone, password=password)

        if not user:
            raise serializers.ValidationError("Numéro ou mot de passe incorrect")

        refresh = self.get_token(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

