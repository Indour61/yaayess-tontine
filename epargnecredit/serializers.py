from rest_framework import serializers
from .models import Group, GroupMember, Versement, ActionLog


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'nom', 'date_creation']


class GroupMemberSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.nom', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'group', 'user', 'user_nom', 'user_phone', 'role', 'actif', 'date_ajout']



class VersementSerializer(serializers.ModelSerializer):
    member_nom = serializers.CharField(source='member.user.nom', read_only=True)
    group_nom = serializers.CharField(source='member.group.nom', read_only=True)

    class Meta:
        model = Versement
        fields = [
            'id', 'member', 'member_nom', 'group_nom',
            'montant', 'date', 'statut', 'methode', 'transaction_id'
        ]


class ActionLogSerializer(serializers.ModelSerializer):
    user_nom = serializers.CharField(source='user.nom', read_only=True)

    class Meta:
        model = ActionLog
        fields = ['id', 'user', 'user_nom', 'action', 'date']
