from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum

from .models import Group, GroupMember, Versement
from .serializers import (
    GroupSerializer,
    GroupMemberSerializer,
    VersementSerializer,
    VersementCreateSerializer,
    DashboardSerializer
)


# =====================================================
# DASHBOARD GLOBAL (Mobile)
# GET /api/epargne/dashboard/
# =====================================================

class DashboardEpargneAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        groupes = Group.objects.filter(
            groupmember__user=user
        ).distinct()

        versements = Versement.objects.filter(
            member__user=user
        ).select_related("member__group", "member__user")

        data = {
            "groupes": GroupSerializer(groupes, many=True).data,
            "versements": VersementSerializer(versements, many=True).data,
        }

        return Response(data)


# =====================================================
# LISTE GROUPES UTILISATEUR
# GET /api/epargne/groupes/
# =====================================================

class UserGroupsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groupes = Group.objects.filter(
            groupmember__user=request.user
        ).distinct()

        serializer = GroupSerializer(groupes, many=True)
        return Response(serializer.data)


# =====================================================
# LISTE MEMBRES D'UN GROUPE
# GET /api/epargne/group/<id>/membres/
# =====================================================

class GroupMembersAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        membres = GroupMember.objects.filter(
            group_id=group_id
        ).select_related("user", "group")

        serializer = GroupMemberSerializer(membres, many=True)
        return Response(serializer.data)


# =====================================================
# LISTE VERSEMENTS UTILISATEUR
# GET /api/epargne/versements/
# =====================================================

class UserVersementsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        versements = Versement.objects.filter(
            member__user=request.user
        ).select_related("member__group", "member__user")

        serializer = VersementSerializer(versements, many=True)
        return Response(serializer.data)


# =====================================================
# CREER VERSEMENT
# POST /api/epargne/versement/create/
# =====================================================

class CreateVersementAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VersementCreateSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Versement créé avec succès"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# STATISTIQUES SIMPLES UTILISATEUR
# GET /api/epargne/stats/
# =====================================================

class UserStatsAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_verse = Versement.objects.filter(
            member__user=request.user,
            statut="validé"
        ).aggregate(total=Sum("montant"))["total"] or 0

        total_groupes = Group.objects.filter(
            groupmember__user=request.user
        ).distinct().count()

        return Response({
            "total_versements_valides": total_verse,
            "nombre_groupes": total_groupes
        })