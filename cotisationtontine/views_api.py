from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Group, GroupMember, Versement, ActionLog
from .serializers import (
    GroupSerializer,
    GroupMemberSerializer,
    VersementSerializer,
    ActionLogSerializer
)


class IsSuperAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_super_admin
        )


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True

        if hasattr(obj, "group"):
            return request.user.is_super_admin or obj.group.admin == request.user

        return False


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):

        group = serializer.save(admin=self.request.user)

        GroupMember.objects.create(
            group=group,
            user=self.request.user
        )

        ActionLog.objects.create(
            user=self.request.user,
            action=f"Création du groupe {group.nom}"
        )


class GroupMemberViewSet(viewsets.ModelViewSet):

    queryset = GroupMember.objects.select_related("user", "group").all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):

        member = serializer.save()

        ActionLog.objects.create(
            user=self.request.user,
            action=f"Ajout membre {member.user} au groupe {member.group.nom}"
        )


class VersementViewSet(viewsets.ModelViewSet):

    queryset = Versement.objects.select_related("member").all()
    serializer_class = VersementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):

        versement = serializer.save()

        ActionLog.objects.create(
            user=self.request.user,
            action=f"Versement {versement.montant} ajouté"
        )


class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = ActionLog.objects.select_related("user").all()
    serializer_class = ActionLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]