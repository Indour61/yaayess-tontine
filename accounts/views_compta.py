from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from cotisationtontine.models import Versement as TontineVersement
from epargnecredit.models import Versement as EpargneVersement
from epargnecredit.models import PretRemboursement


@staff_member_required
def compta_dashboard(request):

    # ===================================
    # 💰 FRAIS TONTINE
    # ===================================

    tontine_frais = (
        TontineVersement.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))["total"]
        or Decimal("0")
    )

    # ===================================
    # 💰 FRAIS EPARGNE
    # ===================================

    epargne_frais = (
        EpargneVersement.objects
        .filter(statut="VALIDE")
        .aggregate(total=Sum("frais"))["total"]
        or Decimal("0")
    )

    # ===================================
    # 💰 REMBOURSEMENTS CREDIT
    # ===================================

    total_remboursements = (
        PretRemboursement.objects.aggregate(
            total=Sum("montant")
        )["total"] or Decimal("0")
    )

    # frais plateforme 1%
    remboursement_frais = total_remboursements * Decimal("0.01")

    # ===================================
    # 💰 TOTAL PLATEFORME
    # ===================================

    total_frais = tontine_frais + epargne_frais + remboursement_frais

    # ===================================
    # 📈 FRAIS PAR MOIS (TONTINE)
    # ===================================

    frais_par_mois = (
        TontineVersement.objects
        .filter(statut="VALIDE")
        .annotate(mois=TruncMonth("date_creation"))
        .values("mois")
        .annotate(total_frais=Sum("frais"))
        .order_by("mois")
    )

    # ===================================
    # 👥 FRAIS PAR GROUPE (TONTINE)
    # ===================================

    frais_par_groupe = (
        TontineVersement.objects
        .filter(statut="VALIDE")
        .values("member__group__nom")
        .annotate(total_frais=Sum("frais"))
        .order_by("-total_frais")
    )

    # ===================================
    # 💰 REVENUS PAR TYPE
    # ===================================

    revenus_types = {
        "tontine": tontine_frais,
        "epargne": epargne_frais,
        "credit": remboursement_frais
    }

    # ===================================
    # CONTEXT TEMPLATE
    # ===================================

    context = {

        # Résumé financier
        "tontine_frais": tontine_frais,
        "epargne_frais": epargne_frais,
        "remboursement_frais": remboursement_frais,
        "total_frais": total_frais,

        # analyses
        "frais_par_mois": frais_par_mois,
        "frais_par_groupe": frais_par_groupe,

        # graphique
        "revenus_types": revenus_types,
    }

    return render(request, "accounts/compta_dashboard.html", context)


from django.db.models import Sum
from django.db.models.functions import TruncMonth
from cotisationtontine.models import Versement
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import datetime


@login_required
def compta_dashboard(request):

    mois_filtre = request.GET.get("mois")  # format: YYYY-MM

    queryset = Versement.objects.filter(statut="VALIDE")

    # 🔍 Filtre par mois
    if mois_filtre:
        try:
            date_obj = datetime.strptime(mois_filtre, "%Y-%m")
            queryset = queryset.filter(
                date_creation__year=date_obj.year,
                date_creation__month=date_obj.month
            )
        except:
            pass

    # 💰 Commissions par groupe
    commissions_par_groupe = (
        queryset
        .values("member__group__nom")
        .annotate(total_commission=Sum("frais"))
        .order_by("-total_commission")
    )

    for g in commissions_par_groupe:
        g["total_commission"] = g["total_commission"] or 0

    # 📅 Historique mensuel (toujours global)
    commissions_par_groupe_mois = (
        Versement.objects
        .filter(statut="VALIDE")
        .annotate(mois=TruncMonth("date_creation"))
        .values("member__group__nom", "mois")
        .annotate(total_commission=Sum("frais"))
        .order_by("-mois")
    )

    context = {
        "commissions_par_groupe": commissions_par_groupe,
        "commissions_par_groupe_mois": commissions_par_groupe_mois,
        "mois_filtre": mois_filtre,
    }

    return render(request, "accounts/compta_dashboard.html", context)
