from django.urls import path
from . import views
from .api_views import LoginAPI
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import MeView


class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer

app_name = 'accounts'

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    # Correction du nom pour qu'il soit cohérent
    path('rejoindre/<str:code>/', views.inscription_et_rejoindre, name='inscription_et_rejoindre'),

    path("attente-validation/", views.attente_validation, name="attente_validation"),
    path("api/login/", LoginAPI.as_view(), name="api_login"),
    path('me/', MeView.as_view(), name='api_me'),
]


