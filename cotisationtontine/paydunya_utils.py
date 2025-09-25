# cotisationtontine/paydunya_utils.py
import os
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings

def _get_setting_or_env(name: str, default: str = "") -> str:
    """
    Cherche d'abord dans settings.PAYDUNYA_* puis dans l'ENV (PAYDUNYA_*).
    Ex: name="MASTER_KEY" -> settings.PAYDUNYA_MASTER_KEY ou os.getenv("PAYDUNYA_MASTER_KEY")
    """
    attr = f"PAYDUNYA_{name}"
    val = getattr(settings, attr, None)
    if val is None:
        val = os.getenv(attr, default)
    return (val or "").strip()

def paydunya_conf() -> dict:
    """
    Renvoie:
      - env: "sandbox" | "prod"
      - master_key, private_key, token (OBLIGATOIRES)
      - public_key (optionnelle pour l’appel HTTP checkout)
      - store_name/tagline/website_url (facultatifs)
    """
    # settings.PAYDUNYA peut surcharger, sinon .env
    s_cfg = getattr(settings, "PAYDUNYA", {}) or {}

    env = (s_cfg.get("env") or s_cfg.get("mode") or _get_setting_or_env("ENV", "sandbox")).lower()
    if env in ("production", "live"):
        env = "prod"
    if env not in ("sandbox", "prod"):
        env = "sandbox"

    cfg = {
        "env": env,
        "master_key": (s_cfg.get("master_key") or _get_setting_or_env("MASTER_KEY")),
        "private_key": (s_cfg.get("private_key") or _get_setting_or_env("PRIVATE_KEY")),
        "token": (s_cfg.get("token") or _get_setting_or_env("TOKEN")),
        "public_key": (s_cfg.get("public_key") or _get_setting_or_env("PUBLIC_KEY")),  # optionnelle
        "store_name": s_cfg.get("store_name", getattr(settings, "PAYDUNYA_STORE_NAME", "YaayESS")),
        "store_tagline": s_cfg.get("store_tagline", getattr(settings, "PAYDUNYA_STORE_TAGLINE", "Plateforme de gestion financière")),
        "website_url": s_cfg.get("website_url", getattr(settings, "PAYDUNYA_WEBSITE_URL", "https://yaayess.com")),
    }

    for k in ("master_key", "private_key", "token"):
        if not cfg[k]:
            raise RuntimeError(f"Clé PAYDUNYA manquante: {k}")

    return cfg

def paydunya_headers(cfg: dict) -> dict:
    # PUBLIC-KEY non requise pour l’API checkout
    return {
        "Content-Type": "application/json",
        "PAYDUNYA-MASTER-KEY": cfg["master_key"],
        "PAYDUNYA-PRIVATE-KEY": cfg["private_key"],
        "PAYDUNYA-TOKEN": cfg["token"],
    }

def paydunya_base_url(cfg: dict) -> str:
    return "https://app.paydunya.com/api/v1" if cfg.get("env") == "prod" else "https://app.paydunya.com/sandbox-api/v1"

def as_fcfa_int(x) -> int:
    if isinstance(x, Decimal):
        d = x
    else:
        d = Decimal(str(x))
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
