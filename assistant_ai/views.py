# assistant_ai/views.py
import os
import uuid
import json
from typing import Optional

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.shortcuts import render
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from gtts import gTTS
from gtts.lang import tts_langs
from openai import OpenAI

# -------------------------------------------------------------------
# Constantes / Config
# -------------------------------------------------------------------
API_KEY = getattr(settings, "OPENAI_API_KEY", None)
MEDIA_TTS_SUBDIR = "tts"
MAX_TTS_CHARS = 2000         # protège gTTS des textes trop longs
MAX_UPLOAD_MB = 10           # taille audio max en Mo

SYSTEM_PROMPT = (
    "Tu es l’assistant YaayESS. Réponds de façon claire et utile. "
    "Langues: français et wolof. Si l’utilisateur parle wolof, réponds en wolof."
)

# -------------------------------------------------------------------
# OpenAI client (lazily)
# -------------------------------------------------------------------
_client: Optional[OpenAI] = None

def _get_client() -> OpenAI:
    global _client
    if not API_KEY:
        raise RuntimeError("Clé API OpenAI manquante (OPENAI_API_KEY).")
    if _client is None:
        _client = OpenAI(api_key=API_KEY)
    return _client

# -------------------------------------------------------------------
# gTTS langs (détection dynamique, cachée)
# -------------------------------------------------------------------
_GTTS_LANGS = None
def _load_gtts_langs():
    global _GTTS_LANGS
    if _GTTS_LANGS is None:
        try:
            _GTTS_LANGS = {k.lower() for k in tts_langs().keys()}
        except Exception:
            _GTTS_LANGS = {"fr", "en"}  # backup minimal
    return _GTTS_LANGS

# -------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------
def _safe_lang(lang: str) -> str:
    """Retourne une langue gTTS valide; fallback -> 'fr' si non supporté."""
    desired = (lang or "fr").strip().lower()
    if desired in _load_gtts_langs():
        return desired
    if desired.startswith("wo"):
        # Wolof pas toujours dispo dans gTTS -> fallback fr
        print("[assistant_ai] WARN: 'wo' non supporté par gTTS. Fallback -> 'fr'.")
        return "fr"
    return "fr"

def _ext_from_mime(mime: str) -> str:
    mapping = {
        "audio/webm": "webm",
        "video/webm": "webm",
        "audio/ogg": "ogg",
        "application/ogg": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/mp4": "m4a",
        "audio/aac": "aac",
    }
    return mapping.get((mime or "").lower(), "bin")

def _json_error(message: str, status: int = 400):
    return JsonResponse({"ok": False, "error": message}, status=status)

def synthesize(text: str, lang: str) -> str:
    """
    Génère un MP3 dans MEDIA/tts/ et retourne l'URL relative (MEDIA_URL + ...).
    """
    if not text:
        raise ValueError("Texte TTS vide.")
    # coupe s'il est trop long (sécurité gTTS)
    tts_text = text[:MAX_TTS_CHARS]

    lang_code = _safe_lang(lang)
    tts_dir = os.path.join(settings.MEDIA_ROOT, MEDIA_TTS_SUBDIR)
    os.makedirs(tts_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(tts_dir, fname)

    tts = gTTS(text=tts_text, lang=lang_code)
    tts.save(path)

    return f"{settings.MEDIA_URL}{MEDIA_TTS_SUBDIR}/{fname}"

def ai_reply(message: str, lang: str) -> str:
    """
    Réponse texte du modèle. Modèle léger pour réactivité/coût.
    """
    if not message:
        return "Pouvez-vous préciser votre demande ?"

    client = _get_client()

    # Chat Completions
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
    )
    answer = (resp.choices[0].message.content or "").strip()
    if not answer:
        answer = "Désolé, je n’ai pas de réponse pour le moment."
    return answer

# -------------------------------------------------------------------
# Health / UI
# -------------------------------------------------------------------
@require_GET
def health(request):
    """
    Petit ping GET pour éviter le 405 et diagnostiquer rapidement.
    """
    return JsonResponse({
        "ok": True,
        "service": "assistant_ai",
        "has_api_key": bool(API_KEY),
    })
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.shortcuts import render

@require_GET
@ensure_csrf_cookie
def chat_ui(request):
    """
    UI de test (GET).
    templates/assistant_ai/chat_voice.html
    """
    # Force la création du token et passe-le au template
    token = get_token(request)
    return render(request, "assistant_ai/chat_voice.html", {"csrf_token": token})

# -------------------------------------------------------------------
# Endpoints API
# -------------------------------------------------------------------
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse

@csrf_protect
@require_http_methods(["GET", "POST", "OPTIONS"])
def chat_text(request):
    """
    GET      -> ping + mode d'emploi (évite 405 quand on visite l'URL dans un navigateur)
    POST     -> Body JSON: {"message": "...", "lang": "fr"|"wo"}
                Retour: {"ok": true, "text": "...", "audio": "/media/tts/xxx.mp3"}
    OPTIONS  -> préflight (si appelé depuis un autre domaine)
    """
    if request.method == "OPTIONS":
        # Réponse minimale au préflight CORS (si besoin, ajoute tes origines)
        resp = HttpResponse(status=204)
        resp["Access-Control-Allow-Origin"] = "https://127.0.0.1:8000"
        resp["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        resp["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return resp

    if request.method == "GET":
        # Petit ping/guide pour éviter 405 en visite directe
        return JsonResponse({
            "ok": True,
            "endpoint": "/ai/text/",
            "usage": "POST JSON {message, lang}",
            "example": "curl -k -X POST https://127.0.0.1:8000/ai/text/ -H 'Content-Type: application/json' -d '{\"message\":\"Bonjour\",\"lang\":\"fr\"}'"
        })

    # ---- POST JSON ----
    raw = (request.body or b"").decode("utf-8").strip()
    if not raw:
        return _json_error("Corps JSON manquant.", 400)

    try:
        payload = json.loads(raw)
    except Exception:
        return _json_error("JSON invalide.", 400)

    message = (payload.get("message") or "").strip()
    lang = (payload.get("lang") or "fr").strip().lower()

    if not message:
        return _json_error("Paramètre 'message' manquant.", 400)

    try:
        answer = ai_reply(message, lang)
        audio_url = synthesize(answer, lang)
        return JsonResponse({"ok": True, "text": answer, "audio": audio_url})
    except RuntimeError as e:
        # ex.: clé API manquante
        return _json_error(str(e), 500)
    except Exception as e:
        return _json_error(f"Erreur interne: {e}", 500)

@csrf_protect
@require_POST
def chat_voice(request):
    """
    Form-Data:
      - audio: Blob (webm/ogg/mp3/wav/m4a/aac)
      - lang: "fr"|"wo" (facultatif)
    """
    # 1) Fichier présent ?
    if "audio" not in request.FILES:
        return _json_error("Fichier audio manquant.", 400)
    audio_file = request.FILES["audio"]

    # 2) Contrôles taille/type
    if audio_file.size and audio_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        return _json_error(f"Fichier trop volumineux (> {MAX_UPLOAD_MB} Mo).", 400)

    ctype = (getattr(audio_file, "content_type", None) or "").lower()
    allowed_types = {
        "audio/webm", "video/webm",
        "audio/ogg", "application/ogg",
        "audio/mpeg", "audio/mp3",
        "audio/wav",
        "audio/mp4", "audio/aac",
    }
    if ctype and ctype not in allowed_types:
        # on tolère content_type vide/non standard
        pass

    # 3) Langue
    lang = (request.POST.get("lang") or "fr").strip().lower()

    # 4) Sauvegarde TEMP via default_storage (nom relatif)
    ext = _ext_from_mime(ctype) or "bin"
    rel_name = f"tmp/{uuid.uuid4().hex}.{ext}"
    saved_name = default_storage.save(rel_name, ContentFile(audio_file.read()))
    # Certains storages (S3) n'ont pas .path ; ici FileSystemStorage en dev
    abs_path = default_storage.path(saved_name) if hasattr(default_storage, "path") else None

    user_text = ""
    try:
        client = _get_client()

        # 5) Transcription OpenAI (Whisper)
        if not abs_path:
            # fallback: lire depuis storage.open
            with default_storage.open(saved_name, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                )
        else:
            with open(abs_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
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
    except RuntimeError as e:
        return _json_error(str(e), 500)
    except Exception as e:
        return _json_error(f"Erreur interne: {e}", 500)
    finally:
        # 7) Nettoyage best effort
        try:
            if default_storage.exists(saved_name):
                default_storage.delete(saved_name)
        except Exception:
            pass

@csrf_protect
@require_POST
def tts_endpoint(request):
    """
    Body JSON: {"text": "...", "lang": "fr"|"wo"}
    Retour: {"ok": true, "audio": "/media/tts/xxx.mp3"}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return _json_error("JSON invalide.", 400)

    text = (payload.get("text") or "").strip()
    lang = (payload.get("lang") or "fr").strip().lower()
    if not text:
        return _json_error("Paramètre 'text' manquant.", 400)

    try:
        audio_url = synthesize(text, lang)
        return JsonResponse({"ok": True, "audio": audio_url})
    except Exception as e:
        return _json_error(f"Erreur interne: {e}", 500)
