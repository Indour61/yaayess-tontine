from django.urls import path
from . import views
from .views_compta import compta_dashboard
from .views_recus import mes_recus
from .views_admin import saas_dashboard, toggle_group_access

from .views import (
    signup_view,
    verify_otp_view,
    resend_otp_view,
    invoices_dashboard,
    invoice_pdf,
    MeView,
    RegisterAPIView,
    LoginAPIView,
)

from .api_views import LoginAPI

from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer


# 🔐 JWT personnalisé
class PhoneTokenObtainPairView(TokenObtainPairView):
    serializer_class = PhoneTokenObtainPairSerializer


app_name = "accounts"


urlpatterns = [

    # 🔥 LANDING
    path("", views.landing_view, name="landing"),

    # 🔐 AUTH
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("signup/", signup_view, name="signup"),

    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("resend-otp/", resend_otp_view, name="resend_otp"),

    # 🔗 GROUPE
    path("rejoindre/<str:code>/", views.inscription_et_rejoindre, name="inscription_et_rejoindre"),
    path("attente-validation/", views.attente_validation, name="attente_validation"),

    # 👤 USER API
    path("me/", MeView.as_view(), name="api_me"),

    # 🔌 API AUTH
    path("api/register/", RegisterAPIView.as_view(), name="api_register"),
    path("api/login/", LoginAPIView.as_view(), name="api_login"),

    # 🔐 JWT
    path("api/token/", PhoneTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # 🏢 ADMIN SAAS
    path("super-admin/dashboard/", saas_dashboard, name="saas_dashboard"),
    path("super-admin/toggle-group/<str:type>/<int:group_id>/", toggle_group_access, name="toggle_group_access"),

    # 🔁 VERSION SIMPLE ADMIN
    path("saas-dashboard/", saas_dashboard, name="saas_dashboard_alt"),
    path("toggle-group/<int:group_id>/", toggle_group_access, name="toggle_group_access_alt"),

    # 👥 GROUPE
    path("create-group/", views.create_group, name="create_group"),

    # 💰 COMPTA
    path("compta-dashboard/", compta_dashboard, name="compta_dashboard"),

    # 🧾 REÇUS
    path("mes-recus/", mes_recus, name="mes_recus"),

    # 🧾 FACTURES
    path("factures/", invoices_dashboard, name="invoices_dashboard"),
    path("invoice/<int:invoice_id>/pdf/", invoice_pdf, name="invoice_pdf"),
]