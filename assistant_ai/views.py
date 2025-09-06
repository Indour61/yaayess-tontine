# assistant_ai/views.py

import os
import io
import re
import uuid
import json
from typing import Optional

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.middleware.csrf import get_token
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.db.models import Sum, Count

# IA / Audio
from openai import OpenAI
from gtts import gTTS
from gtts.lang import tts_langs

# Domain models
from epargnecredit.models import EpargneCredit, Group as EpargneGroup
from cotisationtontine.models import CotisationTontine, Group as TontineGroup


# -------------------------------------------------------------------
# Constantes / Helpers
# -------------------------------------------------------------------

MAX_UPLOAD_MB = 25

def _json_error(msg: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": msg}, status=status)

def _get_client() -> OpenAI:
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY manquante dans les settings/env.")
    return OpenAI(api_key=api_key)

def _gtts_supports(lang: str) -> bool:
    try:
        return lang.lower() in {k.lower() for k in tts_langs().keys()}
    except Exception:
        return lang.lower() in {"fr", "en"}

def _ext_from_mime(ctype: str) -> str:
    ctype = (ctype or "").lower()
    if "webm" in ctype:
        return "webm"
    if "ogg" in ctype:
        return "ogg"
    if "mpeg" in ctype or ctype.endswith("/mp3"):
        return "mp3"
    if "wav" in ctype:
        return "wav"
    if ctype.endswith("/aac") or ctype.endswith("/mp4"):
        return "m4a"
    return ""

def _fmt_money(amount) -> str:
    try:
        v = int(amount or 0)
    except Exception:
        v = 0
    return f"{v:,}".replace(",", " ") + " FCFA"

def _strip_stars(text: Optional[str]) -> str:
    """Supprime tous les astérisques (Markdown ** / *) et espaces multiples, puis trim."""
    return re.sub(r"\s{2,}", " ", re.sub(r"\*+", "", text or "")).strip()

def _normalize_lang(lang: Optional[str]) -> str:
    """Normalise la langue côté API ('wo', 'wolof', 'wo-sn' -> 'wo')."""
    l = (lang or "fr").strip().lower()
    if l in {"wo", "wolof", "wo-sn"}:
        return "wo"
    if l.startswith("fr"):
        return "fr"
    return "fr"


# -------------------------------------------------------------------
# Noyau IA : routage d’intentions + fallback LLM
# -------------------------------------------------------------------

def _route_intent_and_answer(user, message: str, lang: str) -> str:
    """
    Route : statistiques / fonctionnalités / conseils / fallback LLM.
    Répond en wolof si lang == 'wo', sinon en français.
    """
    lang = _normalize_lang(lang)
    m = (message or "").lower()

    # 1) Statistiques
    if any(k in m for k in ["statistique", "stats", "bilan", "chiffre", "tableau de bord"]):
        total_epargne = (EpargneCredit.objects
                         .filter(member__user=user)
                         .aggregate(Sum("montant"))["montant__sum"] or 0)

        total_tontine = (CotisationTontine.objects
                         .filter(member__user=user)
                         .aggregate(Sum("montant"))["montant__sum"] or 0)

        groups_admin_ec = EpargneGroup.objects.filter(admin=user)
        groups_admin_tn = TontineGroup.objects.filter(admin=user)
        nb_groupes_admin = groups_admin_ec.count() + groups_admin_tn.count()

        membres_ec = (EpargneGroup.objects
                      .filter(admin=user)
                      .aggregate(Count("groupmember"))["groupmember__count"] or 0)

        membres_tn = (TontineGroup.objects
                      .filter(admin=user)
                      .aggregate(Count("groupmember"))["groupmember__count"] or 0)

        fr = (
            "📊 Statistiques personnelles\n"
            f"- Total Épargne : {_fmt_money(total_epargne)}\n"
            f"- Total Tontine : {_fmt_money(total_tontine)}\n\n"
            "👤 Administration (si applicable)\n"
            f"- Groupes administrés : {nb_groupes_admin}\n"
            f"- Membres (Épargne & Crédit) : {membres_ec}\n"
            f"- Membres (Cotisation Tontine) : {membres_tn}"
        )
        wo = (
            "📊 Jëf jëf (statistiques)\n"
            f"- Dëppoo (Épargne) : {_fmt_money(total_epargne)}\n"
            f"- Tontine : {_fmt_money(total_tontine)}\n\n"
            "👤 Say taxawaalu (admin)\n"
            f"- Gann yi nga teye : {nb_groupes_admin}\n"
            f"- Yeneen (Épargne & Crédit) : {membres_ec}\n"
            f"- Yeneen (Tontine) : {membres_tn}"
        )
        return wo if lang == "wo" else fr

    # 2) Fonctionnalités
    if any(k in m for k in ["fonctionnalité", "fonctionnalites", "features", "fonction"]):
        fr = (
            "✅ Fonctionnalités YaayESS\n"
            "1) Épargne & Crédit : créer un groupe, ajouter des membres, enregistrer des versements, demander/valider des crédits, suivre les remboursements.\n"
            "2) Cotisation Tontine : gestion des tours, tirage au sort, historiques, paiements gagnant.\n"
            "3) Invitations : lien d’invitation pour rejoindre un groupe, pré-sélection de l’option.\n"
            "4) Paiements : intégration PayDunya (sandbox/live), reçus, callbacks.\n"
            "5) Tableaux de bord : filtres, exports, alertes de retard, notifications WhatsApp/SMS (simulées en dev)."
        )
        wo = (
            "✅ Mbiri jamono (Fonctionnalités) YaayESS\n"
            "1) Dëppoo ak Këram : sosloob gann, yokk jëmmal, bind dëpp, laaj/degël kredi, topp delloo xaalis.\n"
            "2) Tontine : toppi tur yi, jalgati (tirage), xarnu ak jaar-jaar, fayu ku gën.\n"
            "3) Invitations : link ngir dugg ci gann, tann waaxtu bi (option) jëm kanam.\n"
            "4) Fayu : PayDunya (sandbox/live), reçus, callbacks.\n"
            "5) Dashbord : seetal, export, yéglee jàppante, notif WhatsApp/SMS (simulé ci dev)."
        )
        return wo if lang == "wo" else fr

    # 3) Conseils
    if any(k in m for k in ["conseil", "astuce", "meilleur"]):
        fr = (
            "💡 Conseils de gestion\n"
            "- Fixe des dates limites claires et communique-les à l’avance.\n"
            "- Utilise les rappels automatiques pour réduire les retards.\n"
            "- Standardise les montants pour simplifier le suivi.\n"
            "- Exporte régulièrement tes statistiques pour les réunions.\n"
            "- Sépare bien les droits : seul l’admin valide les crédits."
        )
        wo = (
            "💡 Ndimbal ci say gann\n"
            "- Toxal biir bees bu weesu te xamloo ñépp.\n"
            "- Jëfandikoo yégle yi ngir yeexal jàppante yi.\n"
            "- Def mbir bu benn (montant bu bees) ngir sellal topptal gi.\n"
            "- Exportal say jëf jëf ngir waa mbooloo.\n"
            "- Taxawal sa admin rekk moo degël kredi."
        )
        return wo if lang == "wo" else fr

    # 4) Fallback LLM — forcer la langue
    client = _get_client()
    system_base = (
        "Tu es l’assistant officiel de la plateforme YaayESS. "
        "Explique clairement les fonctionnalités, fournis des détails pratiques, "
        "résume des statistiques quand c’est pertinent (sans données sensibles), "
        "et donne des conseils concrets."
    )
    if lang == "wo":
        system_prompt = system_base + " Réponds UNIQUEMENT en wolof (wo), sans traduction."
    else:
        system_prompt = system_base + " Réponds en français."

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.2,
    )
    return completion.choices[0].message.content


def synthesize(text: str, lang: str) -> str:
    """
    gTTS → enregistre un MP3 via default_storage et retourne une URL servie par MEDIA_URL.
    NB: gTTS ne supporte pas 'wo' ; fallback sûr en 'fr' (pas d’erreur).
    """
    t = (text or "").strip()
    if not t:
        return ""

    use_lang = _normalize_lang(lang)
    if not _gtts_supports(use_lang):
        use_lang = "fr"  # fallback audio pour éviter les erreurs

    t = t[:3000]  # limite pratique

    fn = f"tts/{uuid.uuid4().hex}.mp3"
    try:
        tts = gTTS(t, lang=use_lang)
        if hasattr(default_storage, "path"):
            blob_path = default_storage.save(fn, ContentFile(b""))
            abs_path = default_storage.path(blob_path)
            tts.save(abs_path)
        else:
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            default_storage.save(fn, ContentFile(buf.getvalue()))
    except Exception:
        return ""

    media_url = getattr(settings, "MEDIA_URL", "/media/")
    if not media_url.endswith("/"):
        media_url += "/"
    return f"{media_url}{fn}"


def ai_reply(message: str, lang: str) -> str:
    """Point unique pour les endpoints non authentifiés."""
    return _route_intent_and_answer(user=None, message=message, lang=lang)


# -------------------------------------------------------------------
# UI (GET)
# -------------------------------------------------------------------

@require_GET
@ensure_csrf_cookie
def chat_ui(request):
    """
    UI de test (GET) → templates/assistant_ai/chat_voice.html
    Force la création du token et le passe au template.
    """
    token = get_token(request)
    return render(request, "assistant_ai/chat_voice.html", {"csrf_token": token})


# -------------------------------------------------------------------
# API : Texte / Voix / TTS
# -------------------------------------------------------------------

@csrf_protect
@require_http_methods(["GET", "POST", "OPTIONS"])
def chat_text(request):
    """
    GET      → ping + mode d'emploi
    POST     → JSON: {"message": "...", "lang": "fr"|"wo"}
               Réponse: {"ok": true, "text": "...", "audio": "/media/tts/xxx.mp3"}
    OPTIONS  → préflight CORS
    """
    if request.method == "OPTIONS":
        resp = HttpResponse(status=204)
        resp["Access-Control-Allow-Origin"] = "https://127.0.0.1:8000"
        resp["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        resp["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        return resp

    if request.method == "GET":
        return JsonResponse({
            "ok": True,
            "endpoint": "/ai/text/",
            "usage": "POST JSON {message, lang}",
            "example": "curl -k -X POST https://127.0.0.1:8000/ai/text/ "
                       "-H 'Content-Type: application/json' "
                       "-d '{\"message\":\"Bonjour\",\"lang\":\"fr\"}'"
        })

    # POST
    raw = (request.body or b"").decode("utf-8").strip()
    if not raw:
        return _json_error("Corps JSON manquant.", 400)

    try:
        payload = json.loads(raw)
    except Exception:
        return _json_error("JSON invalide.", 400)

    message = (payload.get("message") or "").strip()
    lang = _normalize_lang(payload.get("lang"))

    if not message:
        return _json_error("Paramètre 'message' manquant.", 400)

    try:
        answer = ai_reply(message, lang)
        clean_answer = _strip_stars(answer)          # remove *
        audio_url = synthesize(clean_answer, lang)   # TTS sur texte nettoyé
        return JsonResponse({"ok": True, "text": clean_answer, "audio": audio_url})
    except RuntimeError as e:
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
    if "audio" not in request.FILES:
        return _json_error("Fichier audio manquant.", 400)
    audio_file = request.FILES["audio"]

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
        pass

    lang = _normalize_lang(request.POST.get("lang"))

    ext = _ext_from_mime(ctype) or "bin"
    rel_name = f"tmp/{uuid.uuid4().hex}.{ext}"
    saved_name = default_storage.save(rel_name, ContentFile(audio_file.read()))
    abs_path = default_storage.path(saved_name) if hasattr(default_storage, "path") else None

    user_text = ""
    try:
        client = _get_client()

        # Transcription Whisper
        if not abs_path:
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

        answer = ai_reply(user_text, lang)
        clean_answer = _strip_stars(answer)
        audio_url = synthesize(clean_answer, lang)

        return JsonResponse({
            "ok": True,
            "user_text": user_text,
            "text": clean_answer,
            "audio": audio_url,
        })
    except RuntimeError as e:
        return _json_error(str(e), 500)
    except Exception as e:
        return _json_error(f"Erreur interne: {e}", 500)
    finally:
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
        payload = json.loads((request.body or b"").decode("utf-8"))
    except Exception:
        return _json_error("JSON invalide.", 400)

    text = (payload.get("text") or "").strip()
    lang = _normalize_lang(payload.get("lang"))
    if not text:
        return _json_error("Paramètre 'text' manquant.", 400)

    try:
        clean_text = _strip_stars(text)
        audio_url = synthesize(clean_text, lang)
        return JsonResponse({"ok": True, "audio": audio_url})
    except Exception as e:
        return _json_error(f"Erreur interne: {e}", 500)


# -------------------------------------------------------------------
# Chat contextuel (connecté) avec stats DB (POST depuis un formulaire)
# -------------------------------------------------------------------

@login_required
def assistant_ai(request):
    """
    Vue chat (POST depuis un <form>) qui connait request.user et renvoie
    une réponse contextualisée (stats, fonctionnalités, conseils).
    """
    if request.method == "POST":
        message = (request.POST.get("message") or "").strip()
        lang = _normalize_lang(request.POST.get("lang"))
        if not message:
            return JsonResponse({"response": "Merci d’écrire un message."})

        answer = _route_intent_and_answer(user=request.user, message=message, lang=lang)
        clean_answer = _strip_stars(answer)
        return JsonResponse({"response": clean_answer})

    return render(request, "assistant_ai/chat.html")


from django.views.decorators.http import require_GET

@require_GET
def health(request):
    # endpoint de liveness/readiness
    return JsonResponse({"ok": True, "service": "assistant_ai", "version": "1.0"})
