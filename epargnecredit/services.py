# epargnecredit/services.py (par ex.)
from .models import Group, GroupMember

def add_to_remboursement_group(member: GroupMember):
    """Ajoute le membre au groupe de remboursement de son groupe parent si pas déjà présent."""
    remb = member.group.get_remboursement_group()
    if remb and not GroupMember.objects.filter(group=remb, user=member.user).exists():
        GroupMember.objects.create(group=remb, user=member.user, montant=0)
