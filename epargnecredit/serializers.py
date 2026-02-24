from rest_framework import serializers
from .models import Group, GroupMember, Versement, ActionLog


# =====================================================
# GROUP SERIALIZER
# =====================================================

class GroupSerializer(serializers.ModelSerializer):
    total_membres = serializers.SerializerMethodField()
    total_versements = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'id',
            'nom',
            'date_creation',
            'total_membres',
            'total_versements',
        ]

    def get_total_membres(self, obj):
        return obj.groupmember_set.filter(actif=True).count()

    def get_total_versements(self, obj):
        return sum(
            v.montant for v in
            Versement.objects.filter(member__group=obj, statut="validé")
        )


# =====================================================
# GROUP MEMBER SERIALIZER
# =====================================================

class GroupMemberSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.nom', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    group_nom = serializers.CharField(source='group.nom', read_only=True)

    class Meta:
        model = GroupMember
        fields = [
            'id',
            'group',
            'group_nom',
            'user',
            'user_nom',
            'user_phone',
            'role',
            'actif',
            'date_ajout'
        ]


# =====================================================
# VERSEMENT SERIALIZER (Lecture)
# =====================================================

class VersementSerializer(serializers.ModelSerializer):
    member_nom = serializers.CharField(source='member.user.nom', read_only=True)
    group_nom = serializers.CharField(source='member.group.nom', read_only=True)

    class Meta:
        model = Versement
        fields = [
            'id',
            'group_nom',
            'member_nom',
            'montant',
            'date',
            'statut',
            'methode',
            'transaction_id'
        ]


# =====================================================
# VERSEMENT CREATE SERIALIZER (Ecriture)
# =====================================================

class VersementCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Versement
        fields = [
            'member',
            'montant',
            'methode'
        ]

    def create(self, validated_data):
        validated_data["statut"] = "en_attente"
        return super().create(validated_data)


# =====================================================
# ACTION LOG SERIALIZER
# =====================================================

class ActionLogSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.nom', read_only=True)

    class Meta:
        model = ActionLog
        fields = [
            'id',
            'user_nom',
            'action',
            'date'
        ]


# =====================================================
# DASHBOARD GLOBAL SERIALIZER (Mobile)
# =====================================================

class DashboardSerializer(serializers.Serializer):
    groupes = GroupSerializer(many=True)
    versements = VersementSerializer(many=True)