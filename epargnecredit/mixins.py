# epargnecredit/mixins.py
from django.views import View
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse, resolve

ATTENTE_VALIDATION_NAME = "accounts:attente_validation"
LOGIN_NAME = "accounts:login"

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or \
           request.headers.get("accept", "").startswith("application/json")

def _is_on_attente_page(request):
    try:
        match = resolve(request.path_info)
        return f"{match.namespace}:{match.url_name}" == ATTENTE_VALIDATION_NAME
    except Exception:
        return False

class ValidationRequiredMixin(View):
    """
    À mixer sur les vues CBV d'Épargne & Crédit.
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            login_url = reverse(LOGIN_NAME)
            return redirect(f"{login_url}?next={request.get_full_path()}")

        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return super().dispatch(request, *args, **kwargs)

        if getattr(user, "option", None) == "2" and not getattr(user, "is_validated", False):
            if _is_on_attente_page(request):
                return super().dispatch(request, *args, **kwargs)

            msg = "⛔ Votre compte doit être validé par l’administrateur avant d’accéder à Épargne & Crédit."
            if _is_ajax(request):
                return JsonResponse({"detail": msg, "code": "account_not_validated"}, status=403)

            messages.error(request, msg)
            return redirect(ATTENTE_VALIDATION_NAME)

        return super().dispatch(request, *args, **kwargs)
