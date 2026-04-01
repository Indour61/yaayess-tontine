from decimal import Decimal
from datetime import datetime

from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib.admin.views.decorators import staff_member_required

# MODELS
from accounts.models import CustomUser
from cotisationtontine.models import Versement as TontineVersement, Group as TontineGroup
from epargnecredit.models import Versement as EpargneVersement, PretRemboursement, Group as EpargneGroup


@staff_member_required
def compta_dashboard(request):

    mois_filtre = request.GET.get("mois")

    # ================================
    # 🔹 BASE QUERYSETS (GLOBAL - PAS DE RESET)
    # ================================
    tontine_qs = TontineVersement.objects.filter(statut__iexact="VALIDE")
    epargne_qs = EpargneVersement.objects.filter(statut__iexact="VALIDE")
    remboursement_qs = PretRemboursement.objects.filter(statut__iexact="VALIDE")

    # ================================
    # 🔍 FILTRE PAR MOIS (OPTIONNEL)
    # ================================
    if mois_filtre:
        try:
            date_obj = datetime.strptime(mois_filtre, "%Y-%m")

            tontine_qs = tontine_qs.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

            epargne_qs = epargne_qs.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

            remboursement_qs = remboursement_qs.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

        except ValueError:
            mois_filtre = None  # évite bug UI

    # ================================
    # 💰 KPI FINANCIERS
    # ================================
    total_tontine = tontine_qs.aggregate(
        total=Sum("frais")
    )["total"] or Decimal("0")

    total_epargne = epargne_qs.aggregate(
        total=Sum("frais")
    )["total"] or Decimal("0")

    total_remboursements_brut = remboursement_qs.aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")

    # 👉 Commission 1%
    total_remboursement = total_remboursements_brut * Decimal("0.01")

    # 👉 TOTAL GLOBAL
    total_plateforme = total_tontine + total_epargne + total_remboursement

    # ================================
    # 👥 KPIs BUSINESS
    # ================================
    total_groupes = TontineGroup.objects.count() + EpargneGroup.objects.count()
    total_users = CustomUser.objects.count()

    revenu_moyen_par_groupe = (
        total_plateforme / total_groupes if total_groupes > 0 else Decimal("0")
    )

    # ================================
    # 📊 COMMISSIONS PAR GROUPE
    # ================================
    data = {}

    def merge_group(queryset):
        for item in queryset.values("member__group__nom").annotate(total=Sum("frais")):
            group = item["member__group__nom"] or "Sans nom"
            data[group] = data.get(group, Decimal("0")) + (item["total"] or Decimal("0"))

    merge_group(tontine_qs)
    merge_group(epargne_qs)

    commissions_par_groupe = sorted(
        [{"group": k, "total": v} for k, v in data.items()],
        key=lambda x: x["total"],
        reverse=True
    )

    # ================================
    # 📅 HISTORIQUE MENSUEL
    # ================================
    historique = {}

    def merge_month(queryset):
        qs = queryset.annotate(mois=TruncMonth("date_creation")) \
                     .values("mois") \
                     .annotate(total=Sum("frais"))

        for item in qs:
            key = item["mois"]
            historique[key] = historique.get(key, Decimal("0")) + (item["total"] or Decimal("0"))

    merge_month(tontine_qs)
    merge_month(epargne_qs)

    commissions_par_groupe_mois = sorted(
        [{"mois": k, "total": v} for k, v in historique.items()],
        key=lambda x: x["mois"] or datetime.min
    )

    # ================================
    # 🔥 TOP GROUPES
    # ================================
    top_groupes = commissions_par_groupe[:5]

    # ================================
    # 📦 CONTEXT
    # ================================
    context = {
        "tontine_frais": total_tontine,
        "epargne_frais": total_epargne,
        "remboursement_frais": total_remboursement,
        "total_frais": total_plateforme,

        "total_groupes": total_groupes,
        "total_users": total_users,
        "revenu_moyen_par_groupe": round(revenu_moyen_par_groupe, 2),

        "commissions_par_groupe": commissions_par_groupe,
        "commissions_par_groupe_mois": commissions_par_groupe_mois,
        "top_groupes": top_groupes,

        "mois_filtre": mois_filtre,
    }

    return render(request, "accounts/compta_dashboard.html", context)