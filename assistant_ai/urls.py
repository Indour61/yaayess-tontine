from . import views
from django.urls import path
from .views import health, chat_ui, chat_text, chat_voice, tts_endpoint


app_name = "assistant_ai"

urlpatterns = [
#    path("", views.chat_ui, name="chat_ui"),             # /ai/
#    path("text/", views.chat_text, name="chat_text"),    # /ai/text/
#    path("voice/", views.chat_voice, name="chat_voice"), # /ai/voice/
#    path("tts/", views.tts_endpoint, name="tts"),        # /ai/tts/
    path("health/", health, name="health"),  # GET: /ai/health/
    path("ui/", chat_ui, name="chat_ui"),  # GET: /ai/ui/
    path("text/", chat_text, name="chat_text"),  # POST: /ai/text/
    path("voice/", chat_voice, name="chat_voice"),  # POST: /ai/voice/
    path("tts/", tts_endpoint, name="tts"),  # POST: /ai/tts/

]
