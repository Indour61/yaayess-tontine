from django.core.management.base import BaseCommand
from cotisationtontine.models import Group, GroupMember, CotisationTontine, Tirage
from django.utils.timezone import now
from cotisationtontine.models import HistoriqueAction


class Command(BaseCommand):
    help = "Réinitialise les cotisations et le tirage au sort d’un groupe donné"

    def add_arguments(self, parser):
        parser.add_argument('group_id', type=int, help='ID du groupe à réinitialiser')

    def handle(self, *args, **options):
        group_id = options['group_id']

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Groupe avec ID {group_id} introuvable."))
            return

        # Supprimer les cotisations
        cotisations = CotisationTontine.objects.filter(member__group=group)
        nb_cotisations = cotisations.count()
        cotisations.delete()

        # Supprimer les tirages
        tirages = Tirage.objects.filter(group=group)
        nb_tirages = tirages.count()
        tirages.delete()

        # Remettre les montants à zéro
        membres = GroupMember.objects.filter(group=group)
        nb_membres = membres.count()
        for membre in membres:
            membre.montant = 0
            membre.save()

        self.stdout.write(self.style.SUCCESS(f"\nGroupe : {group.nom} (ID: {group.id})"))
        self.stdout.write(f"📅 Date de réinitialisation : {now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"👥 Membres dans le groupe : {nb_membres}")
        self.stdout.write(f"🎲 Tirages archivés : {nb_tirages}")
        self.stdout.write(f"💸 Cotisations supprimées : {nb_cotisations}")
        self.stdout.write("===========================================")


HistoriqueAction.objects.create(
    group=group,
    action='RESET_CYCLE',
    description=(
        f"Réinitialisation manuelle du cycle via la commande reset_cycle.\n"
        f"Nombre de membres : {member_count}.\n"
        f"Cotisations supprimées : {cotisation_count}.\n"
        f"Tirages archivés : {tirage_count}."
    )
)
