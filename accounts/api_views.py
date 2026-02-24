from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from .serializers import UserSerializer

class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        user = authenticate(request, username=phone, password=password)

        if user:
            return Response({
                "status": "success",
                "user": UserSerializer(user).data
            })

        return Response({"status": "error", "message": "Identifiants invalides"})