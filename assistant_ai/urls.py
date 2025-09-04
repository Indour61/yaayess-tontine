from django.urls import path
from . import views

app_name = "assistant_ai"

urlpatterns = [
    path("", views.chat_ui, name="chat_ui"),             # /ai/
    path("text/", views.chat_text, name="chat_text"),    # /ai/text/
    path("voice/", views.chat_voice, name="chat_voice"), # /ai/voice/
    path("tts/", views.tts_endpoint, name="tts"),        # /ai/tts/
]
