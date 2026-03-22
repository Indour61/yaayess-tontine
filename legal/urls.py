from django.views.generic import TemplateView
from django.urls import path
from . import views

app_name = "legal"

urlpatterns = [
    path("terms/",   TemplateView.as_view(template_name="legal/terms.html"),   name="terms"),
    path("privacy/", TemplateView.as_view(template_name="legal/privacy.html"), name="privacy"),
    path("cookies/", TemplateView.as_view(template_name="legal/cookies.html"), name="cookies"),

    path('terms/', views.terms_view, name='terms'),
]

