from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.apps import apps

from accounts.permissions import IsOptionOne
from accounts.object_permissions import IsGroupMemberObject
from .models import Versement
from .serializers import VersementSerializer


# =====================================================
# VERSEMENT VIEWSET (SECURISÉ MULTI-TENANT)
# =====================================================

class VersementViewSet(ModelViewSet):

    serializer_class = VersementSerializer
    permission_classes = [
        IsAuthenticated,
        IsOptionOne,
        IsGroupMemberObject,
    ]

    def get_queryset(self):
        user = self.request.user

        if not user.is_active:
            return Versement.objects.none()

        if user.is_super_admin:
            return Versement.objects.all()

        return Versement.objects.filter(
            group__groupmember__user=user,
            group__groupmember__actif=True
        ).distinct()

    def _check_group_permission(self, group):
        if self.request.user.is_super_admin:
            return

        if not group.groupmember_set.filter(
            user=self.request.user,
            actif=True
        ).exists():
            raise PermissionDenied("Accès interdit à ce groupe.")

    def perform_create(self, serializer):
        group = serializer.validated_data.get("group")

        if not group:
            raise PermissionDenied("Groupe invalide.")

        self._check_group_permission(group)
        serializer.save()

    def perform_update(self, serializer):
        group = serializer.validated_data.get(
            "group",
            serializer.instance.group
        )

        self._check_group_permission(group)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_group_permission(instance.group)
        instance.delete()


# =====================================================
# GROUP DETAIL API (DASHBOARD TONTINE)
# =====================================================

class GroupDetailAPI(APIView):
    permission_classes = [IsAuthenticated, IsOptionOne]

    def get(self, request, group_id):

        Group = apps.get_model("cotisationtontine", "Group")
        GroupMember = apps.get_model("cotisationtontine", "GroupMember")

        group = get_object_or_404(Group, id=group_id)

        # 🔐 Isolation multi-tenant stricte
        if not request.user.is_super_admin:
            is_member = GroupMember.objects.filter(
                user=request.user,
                group=group,
                actif=True
            ).exists()

            if not is_member:
                return Response(
                    {"error": "Accès interdit"},
                    status=403
                )

        members = GroupMember.objects.filter(
            group=group,
            actif=True
        ).select_related("user")

        members_data = []
        total = 0

        for m in members:
            montant = getattr(m, "montant", 0) or 0
            total += montant

            members_data.append({
                "name": m.user.nom,
                "telephone": m.user.phone,
                "montant_verse": montant,
                # ✅ VRAIE LOGIQUE ADMIN
                "is_admin": group.admin_id == m.user_id,
            })

        return Response({
            "group_name": group.nom,
            "date_creation": group.date_creation,
            "montant_base": group.montant_base,
            "members_count": members.count(),
            "total": total,
            "members": members_data,
        })

