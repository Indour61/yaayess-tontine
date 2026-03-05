from rest_framework.permissions import BasePermission
from django.apps import apps


class IsGroupMemberObject(BasePermission):
    """
    Vérifie que l'utilisateur appartient au groupe
    de l'objet manipulé.
    """

    def has_object_permission(self, request, view, obj):

        if not request.user.is_authenticated:
            return False

        if request.user.is_super_admin:
            return True

        app_label = obj._meta.app_label
        GroupMember = apps.get_model(app_label, "GroupMember")

        return GroupMember.objects.filter(
            user=request.user,
            group=obj.group,
            actif=True
        ).exists()


class IsGroupMemberByURL(BasePermission):
    """
    Vérifie que l'utilisateur appartient au groupe
    passé via group_id dans l'URL.
    """

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.is_super_admin:
            return True

        group_id = view.kwargs.get("group_id")

        if not group_id:
            return False

        queryset = view.get_queryset()
        app_label = queryset.model._meta.app_label
        GroupMember = apps.get_model(app_label, "GroupMember")

        return GroupMember.objects.filter(
            user=request.user,
            group_id=group_id,
            actif=True
        ).exists()

