from functools import wraps
from django.core.exceptions import PermissionDenied
from cotisationtontine.models import GroupMember

def admin_required(view_func):
    """
    Vérifie que l'utilisateur est super_admin ou admin d'au moins un groupe.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        # Vérifie si l'utilisateur est admin dans un de ses groupes
        is_admin = GroupMember.objects.filter(user=request.user, role='ADMIN', actif=True).exists()
        if not is_admin:
            raise PermissionDenied("Accès réservé aux administrateurs.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def membre_required(view_func):
    """
    Vérifie que l'utilisateur est membre d'au moins un groupe.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)
        is_membre = GroupMember.objects.filter(user=request.user, actif=True).exists()
        if not is_membre:
            raise PermissionDenied("Accès réservé aux membres.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
