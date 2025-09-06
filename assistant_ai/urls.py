# assistant_ai/urls.py
from django.urls import path
from . import views

app_name = "assistant_ai"

urlpatterns = [
    # Décommente la ligne suivante seulement si tu as bien défini views.health
    # path("health/", views.health, name="health"),

    path("ui/", views.chat_ui, name="chat_ui"),           # GET : /ai/ui/
    path("text/", views.chat_text, name="chat_text"),     # GET/POST/OPTIONS : /ai/text/
    path("voice/", views.chat_voice, name="chat_voice"),  # POST : /ai/voice/
    path("tts/", views.tts_endpoint, name="tts"),         # POST : /ai/tts/
    path("chat/", views.assistant_ai, name="assistant_ai")# POST : /ai/chat/
]

