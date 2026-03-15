from . import views
from .api_views import LoginAPI
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.jwt_serializer import PhoneTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import MeView
from .views import RegisterAPIView
from .views import LoginAPIView
from .views_admin import saas_dashboard, toggle_group_access
from django.urls import path
from .views_compta import compta_dashboard

from .views_recus import mes_recus

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

    path("api/register/", RegisterAPIView.as_view(), name="api_register"),


    path("api/login/", LoginAPIView.as_view(), name="api_login"),

    path(
        "super-admin/dashboard/",
        saas_dashboard,
        name="saas_dashboard"
    ),

    path(
        "super-admin/toggle-user/<int:user_id>/",
        toggle_group_access,
        name="toggle_group_access"
    ),
    path(
        "saas-dashboard/",
        saas_dashboard,
        name="saas_dashboard"
    ),

    path(
        "toggle-group/<int:group_id>/",
        toggle_group_access,
        name="toggle_group_access"
    ),

    path("create-group/", views.create_group, name="create_group"),

    path("compta-dashboard/", compta_dashboard, name="compta_dashboard"),

    path("mes-recus/", mes_recus, name="mes_recus"),
]


