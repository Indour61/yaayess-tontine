from functools import wraps
from django.core.exceptions import PermissionDenied
from cotisationtontine.models import GroupMember

def admin_required(view_func):
    """
    Vérifie que l'utilisateur est super_admin
    ou admin DU GROUPE concerné.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")

        # Super admin accès total
        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)

        group_id = kwargs.get("group_id")
        if not group_id:
            raise PermissionDenied("Groupe non spécifié.")

        is_admin = GroupMember.objects.filter(
            user=request.user,
            group_id=group_id,
            role='ADMIN',
            actif=True
        ).exists()

        if not is_admin:
            raise PermissionDenied("Accès réservé aux administrateurs de ce groupe.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def membre_required(view_func):
    """
    Vérifie que l'utilisateur est membre
    DU GROUPE concerné.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):

        if not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté.")

        if request.user.is_super_admin:
            return view_func(request, *args, **kwargs)

        group_id = kwargs.get("group_id")
        if not group_id:
            raise PermissionDenied("Groupe non spécifié.")

        is_membre = GroupMember.objects.filter(
            user=request.user,
            group_id=group_id,
            actif=True
        ).exists()

        if not is_membre:
            raise PermissionDenied("Accès réservé aux membres de ce groupe.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view

