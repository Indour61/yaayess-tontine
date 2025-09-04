import os
import uuid
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from gtts import gTTS
from gtts.lang import tts_langs
from openai import OpenAI

# ---- OpenAI client (lit OPENAI_API_KEY depuis l'env / settings) ----
client = OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", None))

# ---- Détection dynamique des langues gTTS (fallback si 'wo' indisponible) ----
_GTTS_LANGS = None
def _load_gtts_langs():
    global _GTTS_LANGS
    if _GTTS_LANGS is None:
        try:
            _GTTS_LANGS = {k.lower() for k in tts_langs().keys()}
        except Exception:
            _GTTS_LANGS = {"fr", "en"}  # backup minimal
    return _GTTS_LANGS

SYSTEM_PROMPT = (
    "Tu es l’assistant YaayESS. Réponds de façon claire et utile. "
    "Langues: français et wolof. Si l’utilisateur parle wolof, réponds en wolof."
)

# ---- Utilitaires ----
def _safe_lang(lang: str) -> str:
    """Retourne une langue gTTS valide; fallback -> 'fr' si non supporté."""
    desired = (lang or "fr").lower()
    if desired in _load_gtts_langs():
        return desired
    # Try some aliases
    if desired.startswith("wo"):
        # Wolof pas toujours dispo dans gTTS -> fallback fr
        print("[assistant_ai] WARN: 'wo' non supporté par gTTS. Fallback -> 'fr'.")
        return "fr"
    return "fr"

def _ext_from_mime(mime: str) -> str:
    mapping = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "video/webm": "webm",
    }
    return mapping.get((mime or "").lower(), "bin")

def synthesize(text: str, lang: str) -> str:
    """
    Génère un MP3 dans MEDIA/tts/ et retourne l'URL relative (MEDIA_URL + ...).
    """
    if not text:
        raise ValueError("Texte TTS vide.")
    lang_code = _safe_lang(lang)

    tts_dir = os.path.join(settings.MEDIA_ROOT, "tts")
    os.makedirs(tts_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(tts_dir, fname)

    tts = gTTS(text=text, lang=lang_code)
    tts.save(path)

    return f"{settings.MEDIA_URL}tts/{fname}"

def ai_reply(message: str, lang: str) -> str:
    """
    Réponse texte du modèle. Garde le modèle léger pour réactivité/coût.
    """
    if not getattr(settings, "OPENAI_API_KEY", None):
        raise RuntimeError("Clé API OpenAI manquante (OPENAI_API_KEY).")

    # --- Option A: Chat Completions (stable & simple) ---
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    )
    answer = (resp.choices[0].message.content or "").strip()

    # --- Option B: Responses API (plus moderne) ---
    # resp = client.responses.create(
    #     model="gpt-4o-mini",
    #     input=[
    #         {"role": "system", "content": SYSTEM_PROMPT},
    #         {"role": "user", "content": message},
    #     ],
    #     temperature=0.3,
    # )
    # answer = (resp.output_text or "").strip()

    if not answer:
        answer = "Désolé, je n’ai pas de réponse pour le moment."
    return answer

# ---- UI de test ----
@require_GET
def chat_ui(request):
    return render(request, "assistant_ai/chat_voice.html", {})

# ---- Chat texte -> texte + TTS ----
@csrf_protect
@require_POST
def chat_text(request):
    """
    Body JSON: {"message": "...", "lang": "fr"|"wo"}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("JSON invalide.")

    message = (payload.get("message") or "").strip()
    lang = (payload.get("lang") or "fr").strip().lower()

    if not message:
        return HttpResponseBadRequest("message manquant")

    try:
        answer = ai_reply(message, lang)
        audio_url = synthesize(answer, lang)
        return JsonResponse({"ok": True, "text": answer, "audio": audio_url})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

# ---- Chat voix -> transcription -> réponse -> TTS ----
@csrf_protect
@require_POST
def chat_voice(request):
    """
    Form-Data:
      - audio: Blob (webm/ogg/mp3/wav)
      - lang: "fr"|"wo" (facultatif)
    """
    # 1) Fichier présent ?
    if "audio" not in request.FILES:
        return HttpResponseBadRequest("Fichier audio manquant")
    audio_file = request.FILES["audio"]

    # 2) Contrôles taille/type
    max_mb = 10
    if audio_file.size > max_mb * 1024 * 1024:
        return HttpResponseBadRequest(f"Fichier trop volumineux (> {max_mb} Mo)")
    allowed_types = {"audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3", "audio/wav", "video/webm"}
    if audio_file.content_type and audio_file.content_type.lower() not in allowed_types:
        return HttpResponseBadRequest("Type de fichier non supporté")

    # 3) Langue
    lang = (request.POST.get("lang") or "fr").strip().lower()

    # 4) Sauvegarde TEMP via default_storage (nom relatif)
    ext = _ext_from_mime(audio_file.content_type)
    rel_name = f"tmp/{uuid.uuid4().hex}.{ext}"
    saved_name = default_storage.save(rel_name, ContentFile(audio_file.read()))
    abs_path = default_storage.path(saved_name)

    user_text = ""
    try:
        # 5) Transcription OpenAI (Whisper)
        with open(abs_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",  # vérifie dans tes dépendances/plans; OK pour dev
                file=f,
                # language=_safe_lang(lang),  # peut être omis pour détection auto
            )
        user_text = (getattr(transcript, "text", "") or "").strip()
        if not user_text:
            user_text = "(audio reçu mais transcription vide)"

        # 6) Réponse + TTS
        answer = ai_reply(user_text, lang)
        audio_url = synthesize(answer, lang)

        return JsonResponse({
            "ok": True,
            "user_text": user_text,
            "text": answer,
            "audio": audio_url
        })
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    finally:
        # 7) Nettoyage best effort
        try:
            if default_storage.exists(saved_name):
                default_storage.delete(saved_name)
        except Exception:
            pass

# ---- TTS direct ----
@csrf_protect
@require_POST
def tts_endpoint(request):
    """
    Body JSON: {"text": "...", "lang": "fr"|"wo"}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("JSON invalide.")

    text = (payload.get("text") or "").strip()
    lang = (payload.get("lang") or "fr").strip().lower()
    if not text:
        return HttpResponseBadRequest("text manquant")
    try:
        audio_url = synthesize(text, lang)
        return JsonResponse({"ok": True, "audio": audio_url})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
