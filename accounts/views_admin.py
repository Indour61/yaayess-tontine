from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from decimal import Decimal
from accounts.models import CustomUser

# TONTINE
from cotisationtontine.models import Group, GroupMember, Versement

# EPARGNE
from epargnecredit.models import Versement as VersementEpargne
from epargnecredit.models import PretRemboursement


@staff_member_required
def saas_dashboard(request):

    # -----------------------------
    # STATISTIQUES GLOBALES
    # -----------------------------

    total_users = CustomUser.objects.count()
    total_groups = Group.objects.count()
    total_members = GroupMember.objects.count()

    versements_tontine = Versement.objects.count()
    versements_epargne = VersementEpargne.objects.count()

    total_versements = versements_tontine + versements_epargne

    # -----------------------------
    # REVENUS TONTINE
    # -----------------------------

    revenus_tontine = (
        Versement.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))
        .get("total") or 0
    )

    # -----------------------------
    # REVENUS EPARGNE
    # -----------------------------

    revenus_epargne = (
        VersementEpargne.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))
        .get("total") or 0
    )

    # -----------------------------
    # REVENUS REMBOURSEMENT CREDIT
    # -----------------------------
    remboursements = PretRemboursement.objects.filter(statut="VALIDE")

    revenus_remboursement = Decimal("0")

    for r in remboursements:
        revenus_remboursement += r.montant * Decimal("0.01")


    # -----------------------------
    # TOTAL REVENUS PLATEFORME
    # -----------------------------

    revenus_plateforme = (
        revenus_tontine +
        revenus_epargne +
        revenus_remboursement
    )

    # -----------------------------
    # EVOLUTION REVENUS (GRAPH)
    # -----------------------------

    revenus_mois = (
        Versement.objects
        .filter(statut="VALIDE")
        .annotate(month=TruncMonth("date_creation"))
        .values("month")
        .annotate(total=Sum("frais"))
        .order_by("month")
    )

    months = []
    revenus_mensuels = []

    for r in revenus_mois:
        months.append(r["month"].strftime("%b"))
        revenus_mensuels.append(float(r["total"]))

    # -----------------------------
    # DERNIERS GROUPES
    # -----------------------------

    groups = Group.objects.select_related("admin").order_by("-date_creation")[:10]

    # -----------------------------
    # CONTEXTE TEMPLATE
    # -----------------------------

    context = {

        "total_users": total_users,
        "total_groups": total_groups,
        "total_members": total_members,
        "total_versements": total_versements,

        "revenus_tontine": revenus_tontine,
        "revenus_epargne": revenus_epargne,
        "revenus_remboursement": revenus_remboursement,
        "revenus_plateforme": revenus_plateforme,

        "groups": groups,
        "months": months,
        "revenus_mensuels": revenus_mensuels,

    }

    return render(request, "admin_saas/dashboard.html", context)


# --------------------------------------------------
# ACTIVER / DESACTIVER GROUPE
# --------------------------------------------------

@staff_member_required
def toggle_group_access(request, group_id):

    group = get_object_or_404(Group, id=group_id)

    if hasattr(group, "is_active"):

        group.is_active = not group.is_active
        group.save()

        if group.is_active:
            messages.success(request, "✅ Groupe activé")
        else:
            messages.warning(request, "⛔ Groupe désactivé")

    return redirect("accounts:saas_dashboard")