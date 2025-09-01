from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    # Correction du nom pour qu'il soit cohérent
    path('rejoindre/<str:code>/', views.inscription_et_rejoindre, name='inscription_et_rejoindre'),

    path("attente-validation/", views.attente_validation, name="attente_validation"),
]

