from django.core.management.base import BaseCommand, CommandError
from epargnecredit.models import Group, epargnecredit, Versement

class Command(BaseCommand):
    help = 'Remet à zéro les montants et supprime toutes les cotisations et versements d\'un groupe donné'

    def add_arguments(self, parser):
        parser.add_argument('group_id', type=int, help='ID du groupe à réinitialiser')

    def handle(self, *args, **options):
        group_id = options['group_id']

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise CommandError(f"Groupe avec l'ID {group_id} non trouvé.")

        membres = group.membres.all()

        # Remettre à zéro les montants des membres (si champ 'montant' existe)
        for membre in membres:
            membre.montant = 0
            membre.save()

        # Supprimer les cotisations et versements liés au groupe
        nb_cotis, _ = epargnecredit.objects.filter(member__group=group).delete()
        nb_versements, _ = Versement.objects.filter(member__group=group).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Réinitialisation du groupe {group.nom} (ID: {group_id}) réussie.\n"
            f"- Montants des membres remis à zéro.\n"
            f"- {nb_cotis} cotisations supprimées.\n"
            f"- {nb_versements} versements supprimés."
        ))
