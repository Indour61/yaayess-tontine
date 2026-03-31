from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from decimal import Decimal
import json

from accounts.models import CustomUser

# TONTINE
from cotisationtontine.models import Group as TontineGroup, GroupMember as TontineMember, Versement as TontineVersement

# EPARGNE
from epargnecredit.models import Group as EpargneGroup, GroupMember as EpargneMember
from epargnecredit.models import Versement as EpargneVersement, PretRemboursement


@staff_member_required
def saas_dashboard(request):

    # =====================================================
    # 👥 STATISTIQUES GLOBALES (FUSION)
    # =====================================================

    total_users = CustomUser.objects.count()

    total_groups = (
        TontineGroup.objects.count() +
        EpargneGroup.objects.count()
    )

    total_members = (
        TontineMember.objects.count() +
        EpargneMember.objects.count()
    )

    versements_tontine = TontineVersement.objects.count()
    versements_epargne = EpargneVersement.objects.count()

    total_versements = versements_tontine + versements_epargne

    # =====================================================
    # 💰 REVENUS
    # =====================================================

    revenus_tontine = (
        TontineVersement.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))["total"] or Decimal("0")
    )

    revenus_epargne = (
        EpargneVersement.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))["total"] or Decimal("0")
    )

    # 🔁 remboursement crédit (1%)
    remboursements = PretRemboursement.objects.filter(statut="VALIDE")

    revenus_remboursement = (
        remboursements.aggregate(total=Sum("montant"))["total"] or Decimal("0")
    ) * Decimal("0.01")

    revenus_plateforme = (
        revenus_tontine +
        revenus_epargne +
        revenus_remboursement
    )

    # =====================================================
    # 📈 EVOLUTION REVENUS (GLOBAL)
    # =====================================================

    historique = {}

    def merge_monthly(queryset):
        qs = queryset.annotate(month=TruncMonth("date_creation")) \
            .values("month") \
            .annotate(total=Sum("frais"))

        for item in qs:
            key = item["month"]
            historique[key] = historique.get(key, Decimal("0")) + (item["total"] or Decimal("0"))

    merge_monthly(TontineVersement.objects.filter(statut="VALIDE"))
    merge_monthly(EpargneVersement.objects.filter(statut="VALIDE"))

    months = []
    revenus_mensuels = []

    for k, v in sorted(historique.items()):
        months.append(k.strftime("%b %Y"))
        revenus_mensuels.append(float(v))

    # =====================================================
    # 🌍 UTILISATEURS PAR PAYS (GLOBAL)
    # =====================================================

    users_by_country = (
        CustomUser.objects
        .values("pays")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    users_country_labels = [u["pays"] or "Inconnu" for u in users_by_country]
    users_country_data = [u["total"] for u in users_by_country]

    # =====================================================
    # 🌍 GROUPES PAR PAYS (GLOBAL)
    # =====================================================

    tontine_groups_country = (
        TontineGroup.objects
        .values("admin__pays")
        .annotate(total=Count("id"))
    )

    epargne_groups_country = (
        EpargneGroup.objects
        .values("admin__pays")
        .annotate(total=Count("id"))
    )

    country_data = {}

    for g in tontine_groups_country:
        pays = g["admin__pays"] or "Inconnu"
        country_data[pays] = country_data.get(pays, 0) + g["total"]

    for g in epargne_groups_country:
        pays = g["admin__pays"] or "Inconnu"
        country_data[pays] = country_data.get(pays, 0) + g["total"]

    groups_country_labels = list(country_data.keys())
    groups_country_data = list(country_data.values())

    # =====================================================
    # 💰 REVENUS PAR PAYS (GLOBAL)
    # =====================================================

    revenus_country = {}

    def merge_country(queryset):
        qs = queryset.values("member__user__pays") \
            .annotate(total=Sum("frais"))

        for item in qs:
            pays = item["member__user__pays"] or "Inconnu"
            revenus_country[pays] = revenus_country.get(pays, 0) + float(item["total"] or 0)

    merge_country(TontineVersement.objects.filter(statut="VALIDE"))
    merge_country(EpargneVersement.objects.filter(statut="VALIDE"))

    revenus_country_labels = list(revenus_country.keys())
    revenus_country_data = list(revenus_country.values())

    # =====================================================
    # 🏆 DERNIERS GROUPES (GLOBAL)
    # =====================================================

    groups = []

    for g in TontineGroup.objects.all()[:5]:
        g.type = "tontine"
        groups.append(g)

    for g in EpargneGroup.objects.all()[:5]:
        g.type = "epargne"
        groups.append(g)



    # =====================================================
    # CONTEXT
    # =====================================================

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

        "months": json.dumps(months),
        "revenus_mensuels": json.dumps(revenus_mensuels),

        "users_country_labels": json.dumps(users_country_labels),
        "users_country_data": json.dumps(users_country_data),

        "groups_country_labels": json.dumps(groups_country_labels),
        "groups_country_data": json.dumps(groups_country_data),

        "revenus_country_labels": json.dumps(revenus_country_labels),
        "revenus_country_data": json.dumps(revenus_country_data),
    }

    return render(request, "admin_saas/dashboard.html", context)


from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages



from django.http import HttpResponse

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

from cotisationtontine.models import Group as TontineGroup
from epargnecredit.models import Group as EpargneGroup


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from cotisationtontine.models import Group as TontineGroup
from epargnecredit.models import Group as EpargneGroup


@staff_member_required
def toggle_group_access(request, type, group_id):

    # 🔍 Sélection du bon modèle
    if type == "tontine":
        group = get_object_or_404(TontineGroup, id=group_id)

    elif type == "epargne":
        group = get_object_or_404(EpargneGroup, id=group_id)

    else:
        messages.error(request, "❌ Type invalide")
        return redirect("accounts:saas_dashboard")

    # 🔒 Vérification champ
    if not hasattr(group, "is_active"):
        messages.error(request, "⚠️ Champ is_active manquant")
        return redirect("accounts:saas_dashboard")

    # 🔄 Toggle
    group.is_active = not group.is_active
    group.save(update_fields=["is_active"])

    # ✅ Message UX
    status = "activé" if group.is_active else "désactivé"

    messages.success(
        request,
        f"{'✅' if group.is_active else '⛔'} Groupe '{group.nom}' ({type}) {status}"
    )

    return redirect("accounts:saas_dashboard")