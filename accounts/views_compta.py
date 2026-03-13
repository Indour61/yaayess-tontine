from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from cotisationtontine.models import Versement as TontineVersement
from epargnecredit.models import Versement as EpargneVersement
from epargnecredit.models import PretRemboursement


@staff_member_required
def compta_dashboard(request):

    # FRAIS TONTINE
    tontine_frais = (
        TontineVersement.objects.aggregate(
            total=Sum("frais")
        )["total"] or 0
    )

    # FRAIS EPARGNE
    epargne_frais = (
        EpargneVersement.objects.aggregate(
            total=Sum("frais")
        )["total"] or 0
    )

    # REMBOURSEMENTS CREDIT
    remboursement_frais = (
        PretRemboursement.objects.aggregate(
            total=Sum("montant")
        )["total"] or 0
    )

    # TOTAL PLATEFORME
    total_frais = tontine_frais + epargne_frais + remboursement_frais

    # FRAIS PAR MOIS
    frais_par_mois = (
        TontineVersement.objects
        .annotate(mois=TruncMonth("date_creation"))
        .values("mois")
        .annotate(total=Sum("frais"))
        .order_by("mois")
    )

    # FRAIS PAR GROUPE
    frais_par_groupe = (
        TontineVersement.objects
        .values("member__group__nom", "member__group__admin__phone")
        .annotate(total_frais=Sum("frais"))
        .order_by("-total_frais")
    )

    context = {
        "tontine_frais": tontine_frais,
        "epargne_frais": epargne_frais,
        "remboursement_frais": remboursement_frais,
        "total_frais": total_frais,
        "frais_par_mois": frais_par_mois,
        "frais_par_groupe": frais_par_groupe,
    }

    return render(request, "accounts/compta_dashboard.html", context)