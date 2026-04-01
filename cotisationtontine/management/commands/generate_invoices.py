from django.core.management.base import BaseCommand
from django.db.models import Sum
from datetime import datetime, date

from cotisationtontine.models import Versement
from epargnecredit.models import Group
from accounts.models import Invoice


COMMISSION_RATE = Decimal("0.02")

class Command(BaseCommand):
    help = "Générer les factures mensuelles (COMMISSIONS)"

    def handle(self, *args, **kwargs):

        now = datetime.now()
        month = now.month
        year = now.year

        groupes = Group.objects.all()

        for group in groupes:

            total_versements = Versement.objects.filter(
                member__group_id=group.id,
                statut="VALIDE",
                date_creation__month=month,
                date_creation__year=year
            ).aggregate(total=Sum('montant'))['total'] or 0

            # 💰 CALCUL COMMISSION
            commission = total_versements * COMMISSION_RATE

            invoice, created = Invoice.objects.update_or_create(
                group=group,
                mois=date(year, month, 1),
                defaults={
                    "montant_cotisation": 0,
                    "montant_epargne": 0,
                    "montant_remboursement": 0,
                    "total": commission  # 👈 uniquement commission
                }
            )

            if created:
                self.stdout.write(f"🆕 Facture commission : {group.nom} → {commission} FCFA")
            else:
                self.stdout.write(f"♻ Mise à jour : {group.nom} → {commission} FCFA")

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Factures commissions générées ({month}/{year})"
        ))