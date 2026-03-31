from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

# MODELS
from accounts.models import CustomUser

from cotisationtontine.models import Versement as TontineVersement, Group as TontineGroup
from epargnecredit.models import Versement as EpargneVersement, PretRemboursement, Group as EpargneGroup


# =========================================================
# 💰 DASHBOARD SIMPLE (ADMIN)
# =========================================================

@staff_member_required
def compta_dashboard(request):

    tontine_frais = TontineVersement.objects.filter(
        statut__iexact="VALIDE"
    ).aggregate(total=Sum("frais"))["total"] or Decimal("0")

    epargne_frais = EpargneVersement.objects.filter(
        statut__iexact="VALIDE"
    ).aggregate(total=Sum("frais"))["total"] or Decimal("0")

    remboursements = PretRemboursement.objects.filter(
        statut__iexact="VALIDE"
    )

    total_remboursements = remboursements.aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")

    remboursement_frais = total_remboursements * Decimal("0.01")

    total_frais = tontine_frais + epargne_frais + remboursement_frais

    context = {
        "tontine_frais": tontine_frais,
        "epargne_frais": epargne_frais,
        "remboursement_frais": remboursement_frais,
        "total_frais": total_frais,
    }

    return render(request, "accounts/compta_dashboard.html", context)


# =========================================================
# 🚀 DASHBOARD GLOBAL FINTECH
# =========================================================

@login_required
def compta_dashboard_global(request):

    mois_filtre = request.GET.get("mois")

    # ================================
    # 🔹 QUERYSETS
    # ================================
    tontine = TontineVersement.objects.filter(statut__iexact="VALIDE")
    epargne = EpargneVersement.objects.filter(statut__iexact="VALIDE")
    remboursement = PretRemboursement.objects.filter(statut__iexact="VALIDE")

    # ================================
    # 🔍 FILTRE PAR MOIS
    # ================================
    if mois_filtre:
        try:
            date_obj = datetime.strptime(mois_filtre, "%Y-%m")

            tontine = tontine.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

            epargne = epargne.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

            remboursement = remboursement.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )

        except:
            pass

    # ================================
    # 💰 KPIs FINANCIERS
    # ================================
    total_tontine = tontine.aggregate(total=Sum("frais"))["total"] or Decimal("0")
    total_epargne = epargne.aggregate(total=Sum("frais"))["total"] or Decimal("0")

    total_remboursements = remboursement.aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")

    total_remboursement = total_remboursements * Decimal("0.01")

    total_plateforme = total_tontine + total_epargne + total_remboursement

    # ================================
    # 👥 KPIs BUSINESS (CORRIGÉ)
    # ================================
    total_groupes = (
        TontineGroup.objects.count() +
        EpargneGroup.objects.count()
    )

    total_users = CustomUser.objects.count()

    revenu_moyen_par_groupe = (
        total_plateforme / total_groupes if total_groupes else Decimal("0")
    )

    # ================================
    # 📊 COMMISSIONS PAR GROUPE
    # ================================
    data = {}

    def merge(queryset):
        for item in queryset.values("member__group__nom").annotate(total=Sum("frais")):
            group = item["member__group__nom"]
            data[group] = data.get(group, Decimal("0")) + (item["total"] or Decimal("0"))

    merge(tontine)
    merge(epargne)

    commissions_par_groupe = [
        {"group": k, "total": v}
        for k, v in sorted(data.items(), key=lambda x: x[1], reverse=True)
    ]

    # ================================
    # 📅 HISTORIQUE MENSUEL
    # ================================
    historique = {}

    def merge_monthly(queryset):
        qs = queryset.annotate(mois=TruncMonth("date_creation")) \
            .values("mois") \
            .annotate(total=Sum("frais"))

        for item in qs:
            key = item["mois"]
            historique[key] = historique.get(key, Decimal("0")) + (item["total"] or Decimal("0"))

    merge_monthly(tontine)
    merge_monthly(epargne)

    commissions_par_groupe_mois = [
        {
            "mois": k,
            "total": v
        }
        for k, v in sorted(historique.items())
    ]

    # ================================
    # 🔥 TOP GROUPES
    # ================================
    top_groupes = commissions_par_groupe[:5]

    # ================================
    # CONTEXT
    # ================================
    context = {
        "total_tontine": total_tontine,
        "total_epargne": total_epargne,
        "total_remboursement": total_remboursement,
        "total_plateforme": total_plateforme,

        "total_groupes": total_groupes,
        "total_users": total_users,
        "revenu_moyen_par_groupe": round(revenu_moyen_par_groupe, 2),

        "commissions_par_groupe": commissions_par_groupe,
        "commissions_par_groupe_mois": commissions_par_groupe_mois,
        "top_groupes": top_groupes,

        "mois_filtre": mois_filtre,
    }

    return render(request, "accounts/compta_dashboard_global.html", context)

