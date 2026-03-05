from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from accounts.models import CustomUser


class MobileLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        user = authenticate(username=phone, password=password)

        if not user:
            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "phone": user.phone,
                "nom": user.nom,
                "option": user.option,
                "is_validated": user.is_validated,
                "is_super_admin": user.is_super_admin,
            }
        })