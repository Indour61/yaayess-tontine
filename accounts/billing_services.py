from django.db.models import Sum
from datetime import date
from cotisationtontine.models import Versement
from epargnecredit.models import Epargne, CreditRepayment, Group
from .models import Invoice

def generate_monthly_invoices(month, year):

    groupes = Group.objects.all()

    for group in groupes:

        cotisations = Versement.objects.filter(
            group=group,
            date__month=month,
            date__year=year
        ).aggregate(total=Sum('montant'))['total'] or 0

        epargnes = Epargne.objects.filter(
            group=group,
            date__month=month,
            date__year=year
        ).aggregate(total=Sum('montant'))['total'] or 0

        remboursements = CreditRepayment.objects.filter(
            credit__group=group,
            date__month=month,
            date__year=year
        ).aggregate(total=Sum('montant'))['total'] or 0

        total = cotisations + epargnes + remboursements

        Invoice.objects.update_or_create(
            group=group,
            mois=date(year, month, 1),
            defaults={
                "montant_cotisation": cotisations,
                "montant_epargne": epargnes,
                "montant_remboursement": remboursements,
                "total": total
            }
        )