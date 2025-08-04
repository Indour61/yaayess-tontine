from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Group, GroupMember, Invitation, Versement, ActionLog
from .serializers import (
    GroupSerializer, GroupMemberSerializer, InvitationSerializer,
    VersementSerializer, ActionLogSerializer
)

# ------------------------
# 🔒 Permissions DRF
# ------------------------
class IsSuperAdmin(permissions.BasePermission):
    """Seul un super_admin a un accès total."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_super_admin)

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permet lecture à tous les membres du groupe,
    mais modification uniquement à l'admin du groupe ou au super_admin.
    """
    def has_object_permission(self, request, view, obj):
        # lecture autorisée
        if request.method in permissions.SAFE_METHODS:
            return True
        # édition seulement pour admin du groupe ou super_admin
        if hasattr(obj, 'group'):
            # Vérifier rôle
            is_admin_group = GroupMember.objects.filter(group=obj.group, user=request.user, role='ADMIN').exists()
            return request.user.is_super_admin or is_admin_group
        return False

# ------------------------
# ✅ ViewSets
# ------------------------

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        # Lorsqu'on crée un groupe, l'utilisateur devient ADMIN automatiquement
        group = serializer.save()
        GroupMember.objects.create(group=group, user=self.request.user, role='ADMIN')
        ActionLog.objects.create(user=self.request.user, action=f"Création du groupe {group.nom}")

class GroupMemberViewSet(viewsets.ModelViewSet):
    queryset = GroupMember.objects.select_related('user', 'group').all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        member = serializer.save()
        ActionLog.objects.create(user=self.request.user, action=f"Ajout membre {member.user.nom} au groupe {member.group.nom}")

    def perform_destroy(self, instance):
        ActionLog.objects.create(user=self.request.user, action=f"Suppression membre {instance.user.nom} du groupe {instance.group.nom}")
        instance.delete()

class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        invitation = serializer.save()
        ActionLog.objects.create(user=self.request.user, action=f"Invitation envoyée à {invitation.phone} pour {invitation.group.nom}")

class VersementViewSet(viewsets.ModelViewSet):
    queryset = Versement.objects.select_related('member').all()
    serializer_class = VersementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        versement = serializer.save()
        ActionLog.objects.create(user=self.request.user, action=f"Versement {versement.montant} ajouté pour {versement.member.user.nom}")

class CreditViewSet(viewsets.ModelViewSet):
#    queryset = Credit.objects.select_related('member').all()
#    serializer_class = CreditSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approuver(self, request, pk=None):
        credit = get_object_or_404(Credit, pk=pk)
        # Vérifier droits admin
        is_admin_group = GroupMember.objects.filter(group=credit.member.group, user=request.user, role='ADMIN').exists()
        if not (request.user.is_super_admin or is_admin_group):
            return Response({'detail': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)
        credit.statut = 'APPROVED'
        credit.date_approbation = timezone.now()
        credit.save()
        ActionLog.objects.create(user=request.user, action=f"Crédit {credit.id} approuvé")
        return Response({'detail': 'Crédit approuvé.'})

class RemboursementViewSet(viewsets.ModelViewSet):
#    queryset = Remboursement.objects.select_related('credit').all()
#    serializer_class = RemboursementSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def perform_create(self, serializer):
        remboursement = serializer.save()
        ActionLog.objects.create(user=self.request.user, action=f"Remboursement {remboursement.montant} ajouté pour crédit {remboursement.credit.id}")

class ActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Lecture seule, accessible uniquement au super_admin.
    """
    queryset = ActionLog.objects.select_related('user').all()
    serializer_class = ActionLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]

