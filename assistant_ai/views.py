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

# -----------------------------
# Langue et auto-correction
# -----------------------------
def _normalize_lang(val) -> str:
    s = (val or "fr").strip().lower()
    return "wo" if s.startswith("wo") else "fr"

# Fautes/variantes courantes normalisées après passage en minuscules et
# (dans le routeur) suppression des accents. Tu peux enrichir la liste.
AUTOCORRECT = {
    "aprgne": "epargne",
    "eparg": "epargne",
    "epagne": "epargne",
    "epargne investissement": "epargne investissement",  # garde la forme stable
    "fonctionnalite": "fonctionnalites",
    "fonction": "fonctionnalites",
    "kredi": "credit",
    "keram": "credit",
    "deppoo": "deppoo",      # Wolof ascii-isé (inoffensif)
    "jappando": "jappandoo", # variante wolof
}



# -------------------------------------------------------------------
# Noyau IA : routage d’intentions + fallback LLM
# -------------------------------------------------------------------

def _route_intent_and_answer(user, message: str, lang: str) -> str:
    """
    Routage par intentions (features, stats, howto, conseils, paiements, notifications,
    compte/sécurité, légal, support) avec correction d'orthographe simple et
    normalisation d'accents. Fallback LLM forcé en FR/WO. Réponses toujours
    nettoyées (suppression des astérisques).
    """
    import unicodedata

    # -------- helpers locaux --------
    def _norm_text(s: str) -> str:
        s = (s or "").strip()
        s = unicodedata.normalize("NFKD", s)
        s = s.encode("ascii", "ignore").decode("ascii")  # remove accents
        s = s.lower()
        # espaces multiples -> un espace
        return " ".join(s.split())

    def _apply_autocorrect(s: str) -> str:
        for src, dst in AUTOCORRECT.items():
            s = s.replace(src, dst)
        return s

    def _dispatch(intent_id: str) -> str:
        """
        Appelle le handler correspondant si présent dans le module,
        sinon renvoie un message par défaut (FR/WO).
        """
        mapping = {
            "features.overview":               ("explain_features_overview",       (lang,)),
            "features.epargne_credit":         ("explain_epargne_credit",          (lang,)),
            "features.epargne_investissement": ("explain_epargne_investissement",  (lang,)),
            "features.tontine":                ("explain_tontine",                  (lang,)),
            "stats.my_group":                  ("show_group_stats",                 (user, lang)),
            "howto.add_member":                ("howto_add_member",                 (lang,)),
            "howto.create_group":              ("howto_create_group",               (lang,)),
            "howto.record_payment":            ("howto_record_payment",             (lang,)),
            "advice.tontine_management":       ("advice_tontine",                   (lang,)),
            "payments.setup":                  ("payments_setup",                   (lang,)),
            "notifications.reminders":         ("notifications_reminders",          (lang,)),
            "account.security":                ("account_security",                 (lang,)),
            "legal.compliance":                ("legal_links",                      (lang,)),
            "support.bug":                     ("support_bug",                      (lang,)),
        }
        fn_name, args = mapping.get(intent_id, (None, None))
        if fn_name:
            fn = globals().get(fn_name)
            if callable(fn):
                try:
                    return _strip_stars(fn(*args))
                except Exception:
                    pass  # on tombera sur le fallback message ci-dessous

        # fallback très court par défaut selon intent
        defaults_fr = {
            "features.overview": "Voici un aperçu des fonctionnalités principales de YaayESS.",
            "features.epargne_credit": "Fonction Épargne et Crédit: groupes, versements, demandes de crédit, remboursements.",
            "features.epargne_investissement": "Épargne Investissement: placer une partie de l’épargne sur des produits dédiés.",
            "features.tontine": "Tontine: tours, tirage, enregistrement des paiements, suivi de l’historique.",
            "stats.my_group": "Connecte-toi pour voir les statistiques de tes groupes.",
            "howto.add_member": "Ajouter un membre: Groupe > Membres > Ajouter, puis invitation.",
            "howto.create_group": "Créer un groupe: Nouveau groupe, nom, module, paramètres, enregistrer.",
            "howto.record_payment": "Enregistrer un versement: Paiements > Ajouter, membre, date, montant, enregistrer.",
            "advice.tontine_management": "Conseils: dates claires, rappels, montants standardisés, preuves vérifiées.",
            "payments.setup": "Paiements: lier PayDunya, tester en sandbox, activer webhooks, vérifier reçus.",
            "notifications.reminders": "Rappels: planifier avant échéance par email/WhatsApp, activer relances.",
            "account.security": "Sécurité: mot de passe, 2FA, export/suppression des données depuis les paramètres.",
            "legal.compliance": "Voir legal/terms, legal/privacy et legal/cookies dans le menu Légal.",
            "support.bug": "Support: décrire le problème, joindre capture et URL; réponse par email.",
        }
        defaults_wo = {
            "features.overview": "Ci ñu ngi lay jox peñc ci li YaayESS mën a def.",
            "features.epargne_credit": "Dëppoo ak Këram: gann, dëpp, laaj kredi, delloo xaalis.",
            "features.epargne_investissement": "Dëppoo Jàppandoo: dugal dëpp ci jëf jëf jàppandoo.",
            "features.tontine": "Tontine: tur yi, jalgati, bind fay, topp xarnu.",
            "stats.my_group": "Duggalal sa konte ngir gis jëf jëf yu sa gann.",
            "howto.add_member": "Yokk jëmmal: Gann > Jëmmal yi > Yokk, yonnee invitation.",
            "howto.create_group": "Sos gann: butoŋ, tur, mbir, jikko yi, denc.",
            "howto.record_payment": "Bind dëpp: Fayu > Yokk, jëmmal, bes, montan, denc.",
            "advice.tontine_management": "Ndimbal: taxawal bes, yégle, def montan bu benn, seet réele yi.",
            "payments.setup": "Fayu: boole PayDunya, tolof ci sandbox, toggal webhook, seet réesi.",
            "notifications.reminders": "Yégle: teg kanam bes ci imeel/WhatsApp, yónnee bu bopp.",
            "account.security": "Kaarange: soppi baatujàll, toggal 2FA, génn far done ci jikko yi.",
            "legal.compliance": "Jàng tektal yi: legal/terms, legal/privacy, legal/cookies.",
            "support.bug": "Ndimbal: wax jafe jafe bi, yokk nataal ak URL.",
        }
        base = defaults_wo if lang == "wo" else defaults_fr
        return _strip_stars(base.get(intent_id, ""))

    def _fallback_llm_clean(user_msg: str) -> str:
        # fallback LLM identique à ta version, mais on nettoie la sortie
        client = _get_client()
        system_base = (
            "Tu es l’assistant officiel de la plateforme YaayESS. "
            "Explique clairement les fonctionnalités, fournis des détails pratiques, "
            "résume des statistiques quand c’est pertinent (sans données sensibles), "
            "et donne des conseils concrets."
        )
        system_prompt = (
            system_base + " Réponds UNIQUEMENT en wolof (wo), sans traduction."
            if lang == "wo" else
            system_base + " Réponds en français."
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )
        return _strip_stars(completion.choices[0].message.content)

    # -------- pipeline d'analyse --------
    lang = _normalize_lang(lang)
    raw = message or ""
    m = _apply_autocorrect(_norm_text(raw))

    # fautes courantes supplémentaires
    AUTOCORRECT_LOCAL = {
        "aprgne": "epargne",
        "eparg": "epargne",
        "fonctionnalite": "fonctionnalites",
        "fonction": "fonctionnalites",
        "kredi": "credit",
        "keram": "credit",
        "deppoo": "deppoo",  # homogénéise si besoin
        "jappando": "jappandoo",
    }
    for k, v in AUTOCORRECT_LOCAL.items():
        m = m.replace(k, v)

    # -------- intents & triggers --------
    intents = [
        ("features.overview",               ["fonctionnalites", "features", "que propose", "presente la plateforme", "cest quoi yaayess", "yaayess c est quoi", "li nekk ci yaayess", "mbiri jamono", "li yaayess def"]),
        ("features.epargne_credit",         ["epargne credit", "epargne & credit", "credit", "remboursement", "aprgne credit", "kredi", "deppoo ak keram", "deppoo ak keram"]),
        ("features.epargne_investissement", ["epargne investissement", "placement", "investir", "jappandoo", "deppoo jappandoo"]),
        ("features.tontine",                ["tontine", "tirage", "tour de tontine", "gagnant tontine", "jalgati", "tur yi", "naŋ", "nang", "ñaŋ"]),
        ("stats.my_group",                  ["statistique", "stats", "bilan", "tableau de bord", "xam xaalis", "jef jef", "sant stats"]),
        ("howto.add_member",                ["ajouter un membre", "inviter un membre", "ajout membre", "yokk jemmal", "nande ku bees"]),
        ("howto.create_group",              ["creer un groupe", "nouveau groupe", "demarrer un groupe", "sos gann", "defar gann", "door gann"]),
        ("howto.record_payment",            ["enregistrer un versement", "preuve de paiement", "saisir paiement", "bind depp", "yokk depp", "xaatim fay"]),
        ("advice.tontine_management",       ["conseil", "astuce", "mieux gerer une tontine", "conseils tontine", "ndimbal tontine", "tallal tontine"]),
        ("payments.setup",                  ["paydunya", "payer", "recu", "webhook", "callback", "fayu"]),
        ("notifications.reminders",         ["rappel", "notifications", "whatsapp", "sms", "relance"]),
        ("account.security",                ["mot de passe", "securite", "2fa", "fermer mon compte", "supprimer mes donnees", "kaarange", "far sama konte"]),
        ("legal.compliance",                ["conditions d utilisation", "politique de confidentialite", "rgpd", "cgu", "legal", "privacy"]),
        ("support.bug",                     ["bug", "erreur", "probleme", "assistance", "jafe jafe"]),
    ]

    # -------- matching --------
    for intent_id, keys in intents:
        if any(k in m for k in keys):
            return _dispatch(intent_id)

    # -------- fallback LLM --------
    return _fallback_llm_clean(raw)

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
# -----------------------------
# Helpers CORS / utilitaires
# -----------------------------
from django.conf import settings

def _get_allowed_origins():
    # Définis dans settings.py : AI_CORS_ORIGINS = ["https://127.0.0.1:8000", "https://localhost:8000"]
    fallback = ["https://127.0.0.1:8000", "http://127.0.0.1:8000", "http://localhost:8000", "https://localhost:8000"]
    return getattr(settings, "AI_CORS_ORIGINS", fallback)

def _with_cors(request, resp):
    origin = request.headers.get("Origin") or ""
    if origin and origin in _get_allowed_origins():
        resp["Access-Control-Allow-Origin"] = origin
        resp["Vary"] = "Origin"
        # Credentials requis si tu envoies le cookie CSRF
        resp["Access-Control-Allow-Credentials"] = "true"
        resp["Access-Control-Expose-Headers"] = "Content-Type"
    return resp

def _preflight_response(request):
    resp = HttpResponse(status=204)
    origin = request.headers.get("Origin") or ""
    if origin and origin in _get_allowed_origins():
        resp["Access-Control-Allow-Origin"] = origin
        resp["Access-Control-Allow-Credentials"] = "true"
    resp["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
    resp["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    resp["Access-Control-Max-Age"] = "86400"
    return resp

def _to_bool(v):
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in {"1", "true", "yes", "on"}

def _guess_ext_from_name(name: str) -> str:
    try:
        base = (name or "").lower()
        for ext in ("webm", "ogg", "mp3", "wav", "m4a", "aac"):
            if base.endswith("." + ext):
                return ext
    except Exception:
        pass
    return ""

# -----------------------------
# UI
# -----------------------------
@require_GET
@ensure_csrf_cookie
def chat_ui(request):
    """
    UI de test (GET) → templates/assistant_ai/chat_voice.html
    Force la création du token et le passe au template.
    """
    token = get_token(request)
    return render(request, "assistant_ai/chat_voice.html", {"csrf_token": token})

# -----------------------------
# API : Texte / Voix / TTS
# -----------------------------
@csrf_protect
@require_http_methods(["GET", "POST", "OPTIONS"])
def chat_text(request):
    """
    GET      → ping + mode d'emploi
    POST     → JSON: {"message": "...", "lang": "fr"|"wo", "tts": true|false}
               Réponse: {"ok": true, "text": "...", "audio": "/media/tts/xxx.mp3" | ""}
    OPTIONS  → préflight CORS
    """
    # Préflight CORS
    if request.method == "OPTIONS":
        return _preflight_response(request)

    # Petit guide GET
    if request.method == "GET":
        resp = JsonResponse({
            "ok": True,
            "endpoint": "/ai/text/",
            "usage": "POST JSON {message, lang, tts?}",
            "example": "curl -k -X POST https://127.0.0.1:8000/ai/text/ "
                       "-H 'Content-Type: application/json' "
                       "-d '{\"message\":\"Bonjour\",\"lang\":\"fr\",\"tts\":true}'"
        })
        return _with_cors(request, resp)

    # POST
    try:
        raw = (request.body or b"").decode("utf-8").strip()
        if not raw:
            return _with_cors(request, _json_error("Corps JSON manquant.", 400))
        payload = json.loads(raw)
    except Exception:
        return _with_cors(request, _json_error("JSON invalide.", 400))

    message = (payload.get("message") or "").strip()
    lang = _normalize_lang(payload.get("lang"))
    # Par défaut on garde le TTS actif pour rester compatible avec ton JS
    tts_flag = payload.get("tts")
    tts_flag = True if tts_flag is None else _to_bool(tts_flag)

    if not message:
        return _with_cors(request, _json_error("Paramètre 'message' manquant.", 400))
    if len(message) > 4000:
        message = message[:4000]

    try:
        answer = ai_reply(message, lang)
        clean_answer = _strip_stars(answer)
        audio_url = synthesize(clean_answer, lang) if tts_flag else ""
        resp = JsonResponse({"ok": True, "text": clean_answer, "audio": audio_url})
        return _with_cors(request, resp)
    except RuntimeError as e:
        return _with_cors(request, _json_error(str(e), 500))
    except Exception as e:
        return _with_cors(request, _json_error(f"Erreur interne: {e}", 500))


@csrf_protect
@require_POST
def chat_voice(request):
    """
    Form-Data:
      - audio: Blob (webm/ogg/mp3/wav/m4a/aac)
      - lang: "fr"|"wo" (facultatif)
    """
    # Fichier présent ?
    if "audio" not in request.FILES:
        return _with_cors(request, _json_error("Fichier audio manquant.", 400))
    audio_file = request.FILES["audio"]

    # Contrôle taille
    if audio_file.size and audio_file.size > MAX_UPLOAD_MB * 1024 * 1024:
        return _with_cors(request, _json_error(f"Fichier trop volumineux (> {MAX_UPLOAD_MB} Mo).", 400))

    # Type MIME
    ctype = (getattr(audio_file, "content_type", None) or "").lower()
    allowed_types = {
        "audio/webm", "video/webm",
        "audio/ogg", "application/ogg",
        "audio/mpeg", "audio/mp3",
        "audio/wav",
        "audio/mp4", "audio/aac",
    }
    # On tolère content_type vide/non standard mais on checke l'extension
    if ctype and ctype not in allowed_types:
        pass

    lang = _normalize_lang(request.POST.get("lang"))

    # Déterminer l'extension de sauvegarde
    ext = _ext_from_mime(ctype) or _guess_ext_from_name(getattr(audio_file, "name", "")) or "bin"
    rel_name = f"tmp/{uuid.uuid4().hex}.{ext}"

    # Sauvegarde temporaire
    saved_name = default_storage.save(rel_name, ContentFile(audio_file.read()))
    abs_path = default_storage.path(saved_name) if hasattr(default_storage, "path") else None

    user_text = ""
    try:
        client = _get_client()

        # Transcription Whisper
        if not abs_path:
            with default_storage.open(saved_name, "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        else:
            with open(abs_path, "rb") as f:
                transcript = client.audio.transcriptions.create(model="whisper-1", file=f)

        user_text = (getattr(transcript, "text", "") or "").strip() or "(audio reçu mais transcription vide)"

        answer = ai_reply(user_text, lang)
        clean_answer = _strip_stars(answer)
        audio_url = synthesize(clean_answer, lang)

        resp = JsonResponse({
            "ok": True,
            "user_text": user_text,
            "text": clean_answer,
            "audio": audio_url,
        })
        return _with_cors(request, resp)
    except RuntimeError as e:
        return _with_cors(request, _json_error(str(e), 500))
    except Exception as e:
        return _with_cors(request, _json_error(f"Erreur interne: {e}", 500))
    finally:
        # Nettoyage best effort
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
        return _with_cors(request, _json_error("JSON invalide.", 400))

    text = (payload.get("text") or "").strip()
    lang = _normalize_lang(payload.get("lang"))
    if not text:
        return _with_cors(request, _json_error("Paramètre 'text' manquant.", 400))

    try:
        clean_text = _strip_stars(text)
        audio_url = synthesize(clean_text, lang)
        resp = JsonResponse({"ok": True, "audio": audio_url})
        return _with_cors(request, resp)
    except Exception as e:
        return _with_cors(request, _json_error(f"Erreur interne: {e}", 500))

# -------------------------------------------------------------------
# Chat contextuel (connecté) avec stats DB (POST depuis un formulaire)
# -------------------------------------------------------------------

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import time
import json

@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def assistant_ai(request):
    """
    Chat connecté : rend le template en GET, répond en JSON en POST.
    - Accepte POST application/json ou form-data (message, lang, tts)
    - Normalise la langue (fr/wo), nettoie la réponse (sans *)
    - Retourne éventuellement l'URL audio (gTTS) si tts=True/1
    - Expose l'intention détectée si une fonction classify(message, lang) existe
    """
    if request.method == "GET":
        return render(request, "assistant_ai/chat.html")

    # --------- Lecture d'entrée (JSON ou Form) ---------
    try:
        if request.content_type and "application/json" in request.content_type:
            payload = json.loads((request.body or b"").decode("utf-8") or "{}")
            raw_message = (payload.get("message") or "").strip()
            lang = payload.get("lang")
            tts_flag = bool(payload.get("tts") or payload.get("speak"))
        else:
            raw_message = (request.POST.get("message") or "").strip()
            lang = request.POST.get("lang")
            tts_flag = (str(request.POST.get("tts", "")).lower() in {"1", "true", "on", "yes"})
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON invalide."}, status=400)

    lang = _normalize_lang(lang)
    if not raw_message:
        return JsonResponse({"ok": False, "error": "Merci d’écrire un message."}, status=400)
    if len(raw_message) > 4000:
        raw_message = raw_message[:4000]

    # --------- Suggestions rapides ---------
    SUGG_FR = [
        "Explique-moi les fonctionnalités de YaayESS",
        "C’est quoi Épargne et Crédit",
        "Comment ajouter un membre",
        "Montre-moi les statistiques de mon groupe",
        "Configurer les rappels WhatsApp",
    ]
    SUGG_WO = [
        "Li nekk ci YaayESS",
        "Kredi ak dëppoo noonu",
        "Nande ku bees ci gann",
        "Sant sama jëf jëf",
        "Teg yégle WhatsApp",
    ]
    suggestions = SUGG_WO if lang == "wo" else SUGG_FR

    # --------- Routage + génération ---------
    started = time.time()
    intent_id = None
    try:
        # Intent (si classify est défini quelque part)
        classify_fn = globals().get("classify")
        if callable(classify_fn):
            try:
                intent_id = classify_fn(raw_message, lang)
            except Exception:
                intent_id = None

        answer = _route_intent_and_answer(user=request.user, message=raw_message, lang=lang)
        clean_answer = _strip_stars(answer)  # enlève tout * éventuel

        audio_url = ""
        if tts_flag:
            audio_url = synthesize(clean_answer, lang) or ""

        took_ms = int((time.time() - started) * 1000)

        return JsonResponse({
            "ok": True,
            "response": clean_answer,
            "audio": audio_url,
            "lang": lang,
            "intent": intent_id,
            "took_ms": took_ms,
            "suggestions": suggestions,
        })
    except RuntimeError as e:
        # ex: clé API manquante
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Erreur interne: {e}"}, status=500)


from django.views.decorators.http import require_GET

@require_GET
def health(request):
    """Endpoint de liveness/readiness simple."""
    is_auth = bool(getattr(request, "user", None) and request.user.is_authenticated)
    return JsonResponse({
        "ok": True,
        "service": "assistant_ai",
        "version": "1.0",
        "authenticated": is_auth
    })

# =========================
# Handlers d'intentions FR/WO
# =========================

def _sel(lang: str, fr: str, wo: str) -> str:
    """Sélecteur de langue simple (wo sinon fr)."""
    return wo if (lang or "").lower().startswith("wo") else fr


def explain_features_overview(lang: str) -> str:
    fr = (
        "YaayESS propose deux modules principaux: Épargne et Crédit, et Cotisation Tontine. "
        "Tu peux créer des groupes, inviter des membres, enregistrer des versements, demander et valider des crédits, "
        "suivre les remboursements. L’assistant IA répond aux questions et la plateforme peut envoyer des rappels. "
        "Les paiements s’appuient sur des prestataires comme PayDunya et des tableaux de bord permettent de suivre l’activité."
    )
    wo = (
        "YaayESS am na ñaar yu mag: Dëppoo ak Këram ak Tontine. "
        "Mën nga sos gann, yokk jëmmal, bind dëpp, laaj ak degël kredi, "
        "toppi delloo xaalis. Ndimbal IA dina tontu sa laaj, platform bi mën na yónnee yégle. "
        "Fayu yi ci kaw PayDunya la, te dashbord yi di wone jëf jëf."
    )
    return _sel(lang, fr, wo)


def explain_epargne_credit(lang: str) -> str:
    fr = (
        "Épargne et Crédit: crée un groupe, ajoute des membres et saisis les versements. "
        "Un membre peut demander un crédit, l’administrateur valide ou refuse, puis les remboursements sont suivis et rappelés. "
        "Tu vois l’historique, les montants restants et peux exporter les données."
    )
    wo = (
        "Dëppoo ak Këram: sos gann, yokk jëmmal, bind dëpp. "
        "Ku nekk mën na laaj kredi, admin moo koy degël walla di ko wacce, ci topp la ñuy delloo xaalis. "
        "Mën nga gis xarnu, xëtu xaalis yi te génn done yi."
    )
    return _sel(lang, fr, wo)


def explain_epargne_investissement(lang: str) -> str:
    fr = (
        "Épargne Investissement permet de placer une partie de l’épargne sur des produits d’investissement si l’option est activée. "
        "Tu définis un objectif, un montant périodique, suis les performances et peux éditer un relevé. "
        "Les risques et conditions dépendent du produit choisi."
    )
    wo = (
        "Dëppoo Jàppandoo mooy dugal sa dëpp ci jëf jëf jàppandoo bu ñu toggal. "
        "Tann sa jikko, xaalis bu weer-weer, topp jàmmu, te mën nga génne réele. "
        "Risk ak ndigal yi dale na ci mbirum jëf jëf bi nga tann."
    )
    return _sel(lang, fr, wo)


def explain_tontine(lang: str) -> str:
    fr = (
        "Tontine: configure les tours, fais le tirage, enregistre les paiements et suis l’historique. "
        "L’application identifie le gagnant à payer, gère les retards et peut envoyer des rappels automatiques."
    )
    wo = (
        "Tontine: tàlleel tur yi, def jalgati, bind fay yi, topp xarnu. "
        "App bi dina wone ku war a ñaŋ, jàppante yi di am te yégle yi mën nañu yónnee seen bopp."
    )
    return _sel(lang, fr, wo)


def show_group_stats(user, lang: str) -> str:
    # Si non connecté, message générique
    if not user or not getattr(user, "is_authenticated", False):
        fr_nc = "Connecte-toi pour voir les statistiques de tes groupes."
        wo_nc = "Duggalal sa konte ngir gis jëf jëf yu sa gann."
        return _sel(lang, fr_nc, wo_nc)

    # Agrégats principaux
    total_epargne = (EpargneCredit.objects
                     .filter(member__user=user)
                     .aggregate(Sum("montant"))["montant__sum"] or 0)
    total_tontine = (CotisationTontine.objects
                     .filter(member__user=user)
                     .aggregate(Sum("montant"))["montant__sum"] or 0)

    groups_admin_ec = EpargneGroup.objects.filter(admin=user)
    groups_admin_tn = TontineGroup.objects.filter(admin=user)
    nb_groupes_admin = groups_admin_ec.count() + groups_admin_tn.count()

    # Compteurs membres côté admin (ajuste si related_name diffère)
    membres_ec = (EpargneGroup.objects
                  .filter(admin=user)
                  .aggregate(Count("groupmember"))["groupmember__count"] or 0)
    membres_tn = (TontineGroup.objects
                  .filter(admin=user)
                  .aggregate(Count("groupmember"))["groupmember__count"] or 0)

    fr = (
        "Statistiques personnelles\n"
        f"- Total Épargne: {_fmt_money(total_epargne)}\n"
        f"- Total Tontine: {_fmt_money(total_tontine)}\n\n"
        "Administration\n"
        f"- Groupes administrés: {nb_groupes_admin}\n"
        f"- Membres Épargne et Crédit: {membres_ec}\n"
        f"- Membres Cotisation Tontine: {membres_tn}"
    )
    wo = (
        "Jëf jëf\n"
        f"- Dëppoo: {_fmt_money(total_epargne)}\n"
        f"- Tontine: {_fmt_money(total_tontine)}\n\n"
        "Taxawaalu\n"
        f"- Gann yi nga teye: {nb_groupes_admin}\n"
        f"- Jëmmal Épargne ak Këram: {membres_ec}\n"
        f"- Jëmmal Tontine: {membres_tn}"
    )
    return _sel(lang, fr, wo)


def howto_add_member(lang: str) -> str:
    fr = (
        "Ajouter un membre: ouvre Groupe, puis Membres, clique sur Ajouter. "
        "Saisis le nom et le contact, choisis le rôle, envoie l’invitation. "
        "Le membre apparaît dès qu’il accepte."
    )
    wo = (
        "Yokk jëmmal: dem ci Gann, jëmmal yi, cuqal Yokk. "
        "Duggal tur ak jokkondiral, tann role, yonnee invitation. "
        "Jëmmal bi dina feeñ bu mu nangu."
    )
    return _sel(lang, fr, wo)


def howto_create_group(lang: str) -> str:
    fr = (
        "Créer un groupe: clique sur Nouveau groupe, donne un nom, choisis le module "
        "Épargne et Crédit ou Tontine, règle le montant et la fréquence, enregistre."
    )
    wo = (
        "Sos gann: cuqal Sos gann, jox ko tur, tann mbir "
        "Dëppoo ak Këram walla Tontine, regol montan ak diine, denc."
    )
    return _sel(lang, fr, wo)


def howto_record_payment(lang: str) -> str:
    fr = (
        "Enregistrer un versement: ouvre Paiements, clique sur Ajouter versement, "
        "choisis le membre et la date, saisis le montant, enregistre. "
        "Ajoute une preuve si nécessaire."
    )
    wo = (
        "Bind dëpp: dem ci Fayu, cuqal Yokk dëpp, "
        "tann jëmmal ak bes, duggal montan, denc. "
        "Mën nga yokk réele boo ko soxla."
    )
    return _sel(lang, fr, wo)


def advice_tontine(lang: str) -> str:
    fr = (
        "Conseils tontine: fixe des dates limites claires, partage le calendrier à l’avance, "
        "utilise les rappels, standardise les montants, vérifie les preuves, consigne tout dans l’historique."
    )
    wo = (
        "Ndimbal tontine: taxawal bes yu xamme, yégle jëmu kanam, "
        "jëfandikoo yégle yi, def montan bu benn, seet réele yi, bind lépp ci xarnu."
    )
    return _sel(lang, fr, wo)


def payments_setup(lang: str) -> str:
    fr = (
        "Intégration paiements: lie ton compte PayDunya dans Paramètres Paiements, "
        "teste en sandbox, active les webhooks, vérifie les reçus et statuts, puis passe en production."
    )
    wo = (
        "Boole fayu: boole sa PayDunya ci Tann Fayu, "
        "tolof ci sandbox, toggal webhook, seet réesi ak xaal, ginnaaw loolu dem ci prod."
    )
    return _sel(lang, fr, wo)


def notifications_reminders(lang: str) -> str:
    fr = (
        "Rappels: programme des rappels avant l’échéance par email ou WhatsApp, "
        "définis la fréquence et le message, active les relances automatiques pour les retards."
    )
    wo = (
        "Yégle: teg yégle kanam bes ci imeel walla WhatsApp, "
        "tann diine ak wax, toggal yónnee bu bopp ngir jàppante yi."
    )
    return _sel(lang, fr, wo)


def account_security(lang: str) -> str:
    fr = (
        "Sécurité du compte: change régulièrement ton mot de passe, active la double authentification, "
        "télécharge tes données si besoin, et demande la suppression du compte depuis les paramètres."
    )
    wo = (
        "Kaarange konte: soppi baatujàll bu yaggul, toggal 2FA, "
        "génn say done su soxla, te laaj far konte ci jikko yi."
    )
    return _sel(lang, fr, wo)


def legal_links(lang: str) -> str:
    fr = (
        "Consulte les documents légaux dans le menu Légal. "
        "Conditions d’utilisation sur l’URL legal/terms et Politique de confidentialité sur legal/privacy. "
        "La gestion des cookies est disponible sur legal/cookies."
    )
    wo = (
        "Jàng tektal yi ci menu Legal. "
        "Ci jàmmu ne ci legal/terms, sutura jëfandikookat ne ci legal/privacy, "
        "ak toppante cookies ci legal/cookies."
    )
    return _sel(lang, fr, wo)


def support_bug(lang: str) -> str:
    fr = (
        "Support: décris le problème, joins une capture, indique l’heure et l’URL. "
        "Nous revenons vers toi par email après analyse."
    )
    wo = (
        "Ndimbal: wax jafe jafe bi, yokk nataal, wax waxtu ak URL. "
        "Dinañu la tontu ci imeel ginnaaw seetlu."
    )
    return _sel(lang, fr, wo)

