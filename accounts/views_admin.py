from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count
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
        .get("total") or Decimal("0")
    )

    # -----------------------------
    # REVENUS EPARGNE
    # -----------------------------

    revenus_epargne = (
        VersementEpargne.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))
        .get("total") or Decimal("0")
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
    # EVOLUTION REVENUS
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
    # UTILISATEURS PAR PAYS
    # -----------------------------

    users_by_country = (
        CustomUser.objects
        .values("pays")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    users_country_labels = [u["pays"] or "Inconnu" for u in users_by_country]
    users_country_data = [u["total"] for u in users_by_country]

    # -----------------------------
    # GROUPES PAR PAYS
    # -----------------------------

    groups_by_country = (
        Group.objects
        .values("admin__pays")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    groups_country_labels = [g["admin__pays"] or "Inconnu" for g in groups_by_country]
    groups_country_data = [g["total"] for g in groups_by_country]

    # -----------------------------
    # REVENUS PAR PAYS
    # -----------------------------

    revenus_country = (
        Versement.objects
        .filter(statut="VALIDE")
        .values("member__user__pays")
        .annotate(total=Sum("frais"))
        .order_by("-total")
    )

    revenus_country_labels = [r["member__user__pays"] or "Inconnu" for r in revenus_country]
    revenus_country_data = [float(r["total"] or 0) for r in revenus_country]

    # -----------------------------
    # DERNIERS GROUPES
    # -----------------------------

    groups = (
        Group.objects
        .select_related("admin")
        .order_by("-date_creation")[:10]
    )

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

        # statistiques SaaS avancées
        "users_country_labels": users_country_labels,
        "users_country_data": users_country_data,

        "groups_country_labels": groups_country_labels,
        "groups_country_data": groups_country_data,

        "revenus_country_labels": revenus_country_labels,
        "revenus_country_data": revenus_country_data,
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

