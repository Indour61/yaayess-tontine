from django.urls import path
from . import views

# API / JWT
from .api_views import LoginAPI
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer

# Views API
from .views import MeView, RegisterAPIView, LoginAPIView

# Admin / SaaS
from .views_admin import saas_dashboard, toggle_group_access

# Compta / Reçus
from .views_compta import compta_dashboard
from .views_recus import mes_recus


# 🔐 JWT personnalisé (connexion avec téléphone)
class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


app_name = 'accounts'


urlpatterns = [

    # 🔥 LANDING PAGE (IMPORTANT)
    path('', views.landing_view, name='landing'),

    # 🔐 Auth classique
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),

    # 🔗 Rejoindre groupe
    path('rejoindre/<str:code>/', views.inscription_et_rejoindre, name='inscription_et_rejoindre'),

    # ⏳ Attente validation
    path('attente-validation/', views.attente_validation, name='attente_validation'),

    # 👤 Profil utilisateur API
    path('me/', MeView.as_view(), name='api_me'),

    # 🔌 API Auth
    path("api/register/", RegisterAPIView.as_view(), name="api_register"),

    # ⚠️ Nettoyage : garder UNE seule route login API
    path("api/login/", LoginAPIView.as_view(), name="api_login"),

    # 🔐 JWT Token
    path("api/token/", PhoneTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 🏢 SaaS Admin
    path("super-admin/dashboard/", saas_dashboard, name="saas_dashboard"),
    path("super-admin/toggle-group/<int:group_id>/", toggle_group_access, name="toggle_group_access"),

    # (option simplifiée)
    path("saas-dashboard/", saas_dashboard, name="saas_dashboard_alt"),
    path("toggle-group/<int:group_id>/", toggle_group_access, name="toggle_group_access_alt"),

    # 👥 Groupe
    path("create-group/", views.create_group, name="create_group"),

    # 💰 Comptabilité
    path("compta-dashboard/", compta_dashboard, name="compta_dashboard"),

    # 🧾 Reçus
    path("mes-recus/", mes_recus, name="mes_recus"),
]
