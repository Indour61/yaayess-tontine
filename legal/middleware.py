# middlewares/terms_gate.py
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch

# ⚙️ Active/désactive la barrière via settings.TERMS_GATE_ENABLED (False par défaut)
TERMS_GATE_ENABLED = getattr(settings, "TERMS_GATE_ENABLED", False)

# Noms d'URL à exempter si resolver_match est disponible
EXEMPT_NAMES = {
    "login",
    "logout",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
    "admin:index",
    # "terms",        # ← tu peux enlever si tu as supprimé cette page
    # "terms_accept", # ← ne dépend plus de ce nom
}

# Prefixes de chemins à exempter (admin, static, media, API publiques, etc.)
EXEMPT_PATH_PREFIXES = (
    "/admin/",
    "/static/",
    "/media/",
    "/favicon.ico",
    "/robots.txt",
)

class TermsGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # On tente de résoudre l'URL d'acceptation une seule fois au démarrage.
        # Si elle n'existe pas, accept_url = None, donc AUCUNE redirection ne sera faite.
        try:
            self.accept_url = reverse("terms_accept")
        except NoReverseMatch:
            self.accept_url = None

    def __call__(self, request):
        # Si la barrière est désactivée → ne rien faire
        if not TERMS_GATE_ENABLED:
            return self.get_response(request)

        path = request.path or "/"

        # Exemption par préfixes (admin, static, media…)
        for prefix in EXEMPT_PATH_PREFIXES:
            if path.startswith(prefix):
                return self.get_response(request)

        # Exemption par nom d'url si on a un resolver_match
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match and resolver_match.url_name in EXEMPT_NAMES:
            return self.get_response(request)

        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            current = getattr(settings, "TERMS_VERSION", "")
            accepted = (
                getattr(user, "terms_version", "") == current
                and bool(getattr(user, "terms_accepted_at", None))
            )

            # ❗ Si l'utilisateur n'a pas accepté ET qu'une route terms_accept existe, on redirige.
            # Si la route n'existe pas (self.accept_url is None), on laisse passer (pas de crash).
            if not accepted and self.accept_url:
                # Évite la boucle de redirection si on est déjà sur la page d'acceptation
                if path != self.accept_url:
                    return redirect(self.accept_url)

        return self.get_response(request)
