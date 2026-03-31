from decimal import Decimal
from datetime import datetime


from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import TruncMonth

# MODELS
from accounts.models import CustomUser
from cotisationtontine.models import Versement as TontineVersement, Group as TontineGroup
from epargnecredit.models import Versement as EpargneVersement, PretRemboursement, Group as EpargneGroup
from django.contrib.admin.views.decorators import staff_member_required

# =========================================================
# 💰 DASHBOARD GLOBAL UNIQUE (CORRIGÉ)
# =========================================================

@staff_member_required
def compta_dashboard(request):

    mois_filtre = request.GET.get("mois")

    # ================================
    # 🔹 QUERYSETS (CORRIGÉ)
    # ================================
    tontine = TontineVersement.objects.filter(statut__iexact="VALIDE")
    epargne = EpargneVersement.objects.filter(statut__iexact="VALIDE")
    remboursement = PretRemboursement.objects.filter(statut__iexact="VALIDE")

    # ================================
    # 🔍 FILTRE PAR MOIS (CORRIGÉ)
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
    # 💰 KPI FINANCIERS (FIX 0 BUG)
    # ================================
    # ================================
    # 💰 KPI FINANCIERS (FIX FINAL)
    # ================================

    # TONTINE
    total_tontine = tontine.aggregate(
        total=Sum("frais")
    )["total"] or Decimal("0")

    # EPARGNE
    total_epargne = epargne.aggregate(
        total=Sum("frais")
    )["total"] or Decimal("0")

    # REMBOURSEMENTS (calcul commission)
    total_remboursements = remboursement.aggregate(
        total=Sum("montant")
    )["total"] or Decimal("0")

    # 👉 Commission dynamique (1%)
    total_remboursement = total_remboursements * Decimal("0.01")

    # 👉 TOTAL PLATEFORME
    total_plateforme = total_tontine + total_epargne + total_remboursement

    # 🔥 DEBUG (à garder temporairement)
    print("TONTINE:", total_tontine)
    print("EPARGNE:", total_epargne)
    print("REMBOURSEMENT:", total_remboursement)
    print("TOTAL:", total_plateforme)


    # ================================
    # 👥 KPIs BUSINESS
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
            group = item["member__group__nom"] or "Sans nom"
            data[group] = data.get(group, Decimal("0")) + (item["total"] or Decimal("0"))

    merge(tontine)
    merge(epargne)

    commissions_par_groupe = sorted(
        [{"group": k, "total": v} for k, v in data.items()],
        key=lambda x: x["total"],
        reverse=True
    )

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

    commissions_par_groupe_mois = sorted(
        [{"mois": k, "total": v} for k, v in historique.items()],
        key=lambda x: x["mois"]
    )

    # ================================
    # 🔥 TOP GROUPES
    # ================================
    top_groupes = commissions_par_groupe[:5]

    # ================================
    # CONTEXT FINAL
    # ================================
    context = {
        # KPI affichés en haut (IMPORTANT)
        "tontine_frais": total_tontine,
        "epargne_frais": total_epargne,
        "remboursement_frais": total_remboursement,
        "total_frais": total_plateforme,

        # BUSINESS
        "total_groupes": total_groupes,
        "total_users": total_users,
        "revenu_moyen_par_groupe": round(revenu_moyen_par_groupe, 2),

        # TABLEAUX
        "commissions_par_groupe": commissions_par_groupe,
        "commissions_par_groupe_mois": commissions_par_groupe_mois,
        "top_groupes": top_groupes,

        "mois_filtre": mois_filtre,
    }

    return render(request, "accounts/compta_dashboard.html", context)
