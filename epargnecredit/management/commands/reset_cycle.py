from django.core.management.base import BaseCommand, CommandError
#from epargnecredit.models import Group, GroupMember
from django.utils import timezone


class Command(BaseCommand):
    help = 'Réinitialise un cycle pour un groupe si tous les membres ont atteint le montant de base'

    def add_arguments(self, parser):
        parser.add_argument('group_id', type=int, help='ID du groupe à réinitialiser')

    def handle(self, *args, **kwargs):
        group_id = kwargs['group_id']

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            raise CommandError(f"Groupe avec ID {group_id} introuvable.")

        membres = group.membres.all()

        if not membres.exists():
            self.stdout.write(self.style.WARNING("Aucun membre dans ce groupe."))
            return

        # Vérifier que tous les membres ont atteint le montant de base
        membres_incomplets = []
        for membre in membres:
            if not hasattr(membre, 'etat_versement') or membre.etat_versement != 'Atteint':
                membres_incomplets.append(membre)

        if membres_incomplets:
            self.stdout.write(self.style.WARNING("Tous les membres n'ont pas encore atteint le montant de base."))
            for m in membres_incomplets:
                self.stdout.write(f"- {m.user.username}")
            return

        # Réinitialiser les données
        for membre in membres:
            membre.montant = 0
            membre.save()

        group.date_reset = timezone.now()
        group.save()

        self.stdout.write(
            self.style.SUCCESS(f"✅ Cycle du groupe '{group.nom}' (ID {group.id}) réinitialisé avec succès."))
