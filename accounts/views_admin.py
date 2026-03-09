from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth

from accounts.models import CustomUser, Group, Member, Versement

from cotisationtontine.models import Group

@staff_member_required
def saas_dashboard(request):

    # statistiques
    total_users = CustomUser.objects.count()

    total_groups = Group.objects.count()

    total_members = Member.objects.count()

    total_versements = Versement.objects.count()

    revenus_plateforme = Versement.objects.aggregate(
        total=Sum("commission")
    )["total"] or 0

    # groupes clients

    groups = Group.objects.select_related("admin").order_by("-date_creation")[:20]
    context = {
        "total_users": total_users,
        "total_groups": total_groups,
        "total_members": total_members,
        "total_versements": total_versements,
        "revenus_plateforme": revenus_plateforme,
        "groups": groups,
    }

    return render(request, "admin_saas/dashboard.html", context)


@staff_member_required
def toggle_group_access(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    if group.is_active:
        group.is_active = False
        messages.warning(request, f"Groupe {group.nom} bloqué.")
    else:
        group.is_active = True
        messages.success(request, f"Groupe {group.nom} activé.")

    group.save()

    return redirect("accounts:saas_dashboard")

