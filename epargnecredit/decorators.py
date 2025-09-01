from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def validation_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        # On bloque seulement pour l'option Épargne & Crédit
        if getattr(request.user, "is_validated", False) is False:
            messages.error(request, "⛔ Votre compte doit être validé par l’administrateur avant d’accéder à Épargne & Crédit.")
            return redirect('accounts:attente_validation')
        return view_func(request, *args, **kwargs)
    return _wrapped
