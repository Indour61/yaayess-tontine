from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from epargnecredit.models import Group, GroupMember, Versement, ActionLog


def landing_view(request):
    """
    Page d'accueil qui redirige vers le dashboard si l'utilisateur est connecté,
    ou affiche une page de présentation sinon.
    """
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('epargnecredit:dashboard_epargne_credit')

    # Sinon, afficher la page d'accueil publique
    return render(request, 'landing.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

#from epargnecredit.models import Group, Versement, ActionLogEC  # adapter selon tes modèles
from epargnecredit.models import Group, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from .models import Group, GroupMember, Versement, ActionLog

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from .models import Group, Versement, ActionLog


@login_required
def dashboard_epargne_credit(request):
    """
    Dashboard principal avec aperçu des groupes, activités récentes et statistiques.
    """

    # Groupes dont l'utilisateur est administrateur
    groupes_admin = Group.objects.filter(admin=request.user)

    # Groupes dont l'utilisateur est membre (via relation membres_ec)
    groupes_membre = Group.objects.filter(
        membres_ec=request.user
    ).exclude(admin=request.user).distinct()

    # Dernières actions de l'utilisateur
    dernieres_actions = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]

    # Total des versements de l'utilisateur
    total_versements = Versement.objects.filter(
        member__user=request.user
    ).aggregate(total=Sum('montant'))['total'] or 0

    # Nombre total de groupes où l'utilisateur est membre
    total_groupes = groupes_membre.count() + groupes_admin.count()

    # Récupérer les versements récents (30 derniers jours)
    date_limite = timezone.now() - timedelta(days=30)
    versements_recents = Versement.objects.filter(
        member__user=request.user,
        date__gte=date_limite
    ).select_related('member__user', 'member__group').order_by('-date')[:5]

    # Statistiques des groupes administrés
    stats_groupes_admin = []
    for groupe in groupes_admin:
        total_membres = groupe.membres_ec.count()
        total_versements_groupe = Versement.objects.filter(
            member__group=groupe
        ).aggregate(total=Sum('montant'))['total'] or 0
        stats_groupes_admin.append({
            'groupe': groupe,
            'membres_count': total_membres,
            'versements_total': total_versements_groupe
        })

    context = {
        "groupes_admin": groupes_admin,
        "groupes_membre": groupes_membre,
        "dernieres_actions": dernieres_actions,
        "total_versements": total_versements,
        "total_groupes": total_groupes,
        "versements_recents": versements_recents,
        "stats_groupes_admin": stats_groupes_admin,
    }

    return render(request, "epargnecredit/dashboard.html", context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from decimal import Decimal

from epargnecredit.forms import GroupForm, GroupMemberForm, VersementForm
from epargnecredit.models import Group, GroupMember, Invitation, Versement, ActionLog
from accounts.models import CustomUser
from accounts.utils import envoyer_invitation


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse
from epargnecredit.forms import GroupForm, GroupMemberForm
from epargnecredit.models import Group, GroupMember
from accounts.models import CustomUser
from epargnecredit.utils import envoyer_invitation  # ta fonction de simulation WhatsApp/SMS

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse

from .forms import GroupForm
from .models import Group, GroupMember
from .utils import envoyer_invitation  # ta fonction de simulation WhatsApp/SMS

@login_required
@transaction.atomic
def ajouter_groupe_view(request):
    """
    Création d'un nouveau groupe par un utilisateur connecté :
    1️⃣ Création du groupe avec l'utilisateur comme admin
    2️⃣ Ajout de l'admin comme membre
    3️⃣ Génération d'un lien d'invitation
    4️⃣ Envoi de l'invitation (simulation WhatsApp ou SMS)
    """
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            try:
                # ✅ Créer le groupe
                group = form.save(commit=False)
                group.admin = request.user
                group.save()

                # ✅ Ajoute l'admin comme membre du groupe
                GroupMember.objects.create(
                    group=group,
                    user=request.user,
                    montant=0
                )

                # ✅ Crée un lien d'invitation sécurisé
                lien_invitation = request.build_absolute_uri(
                    reverse("accounts:inscription_et_rejoindre", args=[str(group.code_invitation)])
                )

                # ✅ Simule l'envoi de l'invitation
                envoyer_invitation(request.user.phone, lien_invitation)

                messages.success(
                    request,
                    f"Groupe « {group.nom} » créé avec succès et vous avez été ajouté comme membre."
                )
                return redirect("epargnecredit:dashboard_epargne_credit")

            except Exception as e:
                messages.error(request, f"Erreur lors de la création du groupe : {str(e)}")
    else:
        form = GroupForm()

    return render(
        request,
        "epargnecredit/ajouter_groupe.html",
        {"form": form, "title": "Créer un groupe"}
    )

@login_required
@transaction.atomic
def ajouter_membre_view(request, group_id):
    """
    Ajouter un membre à un groupe existant.
    Seul l'administrateur du groupe peut ajouter des membres.
    """
    group = get_object_or_404(Group, id=group_id)

    if group.admin != request.user:
        messages.error(request, "⚠️ Vous n'avez pas les droits pour ajouter un membre à ce groupe.")
        return redirect("epargnecredit:dashboard_epargne_credit")

    if request.method == "POST":
        form = GroupMemberForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            nom = form.cleaned_data["nom"]

            # Crée ou récupère l'utilisateur
            user, created_user = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={"nom": nom or f"Utilisateur {phone}"}
            )

            if not created_user and user.nom != nom:
                messages.warning(
                    request,
                    f"⚠️ Ce numéro est déjà associé à {user.nom}. Le nom fourni ({nom}) a été ignoré."
                )
                nom = user.nom

            # Vérifie si le membre existe déjà
            if GroupMember.objects.filter(group=group, user=user).exists():
                messages.info(request, f"ℹ️ {user.nom} est déjà membre du groupe {group.nom}.")
                return redirect("epargnecredit:group_detail", group_id=group.id)

            # Vérifie si le nom existe déjà dans le groupe avec un autre numéro
            existing_members_same_name = GroupMember.objects.filter(
                group=group,
                user__nom=nom
            ).exclude(user__phone=phone)
            alias = None
            if existing_members_same_name.exists():
                messages.warning(
                    request,
                    f"⚠️ Le nom '{nom}' existe déjà dans le groupe avec un autre numéro. "
                    f"Un alias sera créé pour éviter la confusion."
                )
                alias = f"{nom} ({phone})"

            # Ajout du membre
            group_member = GroupMember.objects.create(
                group=group,
                user=user,
                montant=0,
                alias=alias
            )

            # Message de confirmation
            messages.success(
                request,
                f"✅ {alias if alias else user.nom} a été ajouté au groupe {group.nom}."
            )

            # TODO: Simuler envoi WhatsApp ou SMS
            # message = f"Bonjour {user.nom}, vous avez été ajouté au groupe {group.nom} sur YaayESS. Connectez-vous avec votre numéro {phone}."
            # envoyer_invitation(phone, message)

            return redirect("epargnecredit:group_detail", group_id=group.id)
    else:
        form = GroupMemberForm()

    return render(
        request,
        "epargnecredit/ajouter_membre.html",
        {"group": group, "form": form}
    )

from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Group, GroupMember, Versement, ActionLog


from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from .models import Group, GroupMember, Versement, ActionLog

@login_required
def group_list_view(request):
    """
    Affiche la liste des groupes :
    - Tous les groupes si super admin
    - Sinon, seulement ceux créés par l'utilisateur ou ceux où il est membre
    """
    if getattr(request.user, "is_super_admin", False):
        groupes = Group.objects.all()
    else:
        # Utilisation du nouveau related_name 'members'
        groupes = Group.objects.filter(
            Q(admin=request.user) |
            Q(members__user=request.user)
        ).distinct()

    return render(request, 'epargnecredit/group_list.html', {'groupes': groupes})


@login_required
def group_detail(request, group_id):
    """
    Détails d'un groupe :
    - Liste des membres
    - Versements
    - Dernières actions
    - Invitation (si admin)
    """
    group = get_object_or_404(Group, id=group_id)

    # Vérification d'accès
    if not (
        group.admin == request.user or
        GroupMember.objects.filter(group=group, user=request.user).exists() or
        getattr(request.user, "is_super_admin", False)
    ):
        messages.error(request, "⚠️ Vous n'avez pas accès à ce groupe.")
        return redirect("epargnecredit:group_list")

    # Membres avec leurs infos
    membres = group.members.select_related('user')

    # Tous les versements liés à ce groupe
    versements = Versement.objects.filter(
        member__group=group
    ).select_related('member', 'member__user').order_by('date')

    # Montant total des versements du groupe
    total_montant = versements.aggregate(total=Sum('montant'))['total'] or 0

    # Total par membre
    versements_par_membre = versements.values('member').annotate(total_montant=Sum('montant'))
    montants_membres_dict = {v['member']: v['total_montant'] for v in versements_par_membre}

    # Dernier versement par membre
    dernier_versement_membres_dict = {}
    for membre in membres:
        dernier = versements.filter(member=membre).order_by('-date').first()
        dernier_versement_membres_dict[membre.id] = dernier
        # Ajouter le total au membre pour affichage
        membre.montant = montants_membres_dict.get(membre.id, 0)

    # Vérifier si l'utilisateur est admin du groupe ou super admin
    user_is_admin = (request.user == group.admin) or getattr(request.user, "is_super_admin", False)

    # Récupérer les 10 dernières actions liées à ce groupe
    actions = ActionLog.objects.filter(group=group).order_by('-date')[:10]

    # Générer le lien d'invitation
    invite_url = request.build_absolute_uri(
        reverse('accounts:inscription_et_rejoindre', args=[str(group.code_invitation)])
    )

    # Sauvegarder dans la session pour un accès rapide
    if user_is_admin:
        request.session['last_invitation_link'] = invite_url

    context = {
        'group': group,
        'membres': membres,
        'dernier_versement_membres_dict': dernier_versement_membres_dict,
        'total_montant': total_montant,
        'admin_user': group.admin,
        'actions': actions,
        'user_is_admin': user_is_admin,
        'invite_url': invite_url,
        'last_invitation_link': request.session.get('last_invitation_link'),
    }

    return render(request, 'epargnecredit/group_detail.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from decimal import Decimal
import requests
import json

from epargnecredit.models import GroupMember, Versement


@login_required
@transaction.atomic
def initier_versement(request, member_id):
    """
    Initier un versement pour un membre d'un groupe (Caisse ou PayDunya)
    """
    member = get_object_or_404(GroupMember, id=member_id)
    group_id = member.group.id

    # Vérifier que l'utilisateur a le droit d'effectuer un versement pour ce membre
    if request.user != member.user and request.user != member.group.admin and not getattr(request.user, "is_super_admin", False):
        messages.error(request, "⚠️ Vous n'avez pas les droits pour effectuer un versement pour ce membre.")
        return redirect("epargnecredit:group_detail", group_id=group_id)

    if request.method == 'POST':
        try:
            montant_saisi = Decimal(request.POST.get('montant', '0'))
            if montant_saisi <= 0:
                messages.error(request, "Le montant doit être supérieur à 0.")
                return redirect("epargnecredit:initier_versement", member_id=member_id)
        except (TypeError, ValueError, Decimal.InvalidOperation):
            messages.error(request, "Montant invalide.")
            return redirect("epargnecredit:initier_versement", member_id=member_id)

        methode = request.POST.get('methode', 'paydunya').lower()

        # --- Si paiement en caisse ---
        if methode == 'caisse':
            Versement.objects.create(
                member=member,
                montant=montant_saisi,
                frais=0,
                methode="CAISSE",
                transaction_id=f"CAISSE-{member.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                statut="valide"
            )
            member.montant += montant_saisi
            member.save()

            messages.success(request, f"✅ Versement de {montant_saisi} FCFA enregistré via Caisse.")
            return redirect('epargnecredit:group_detail', group_id=group_id)

        # --- Si paiement PayDunya ---
        frais_pourcent = montant_saisi * Decimal('0.02')
        frais_fixe = Decimal('50')
        frais_total = int(round(frais_pourcent + frais_fixe))
        montant_total = int(round(montant_saisi + frais_total))

        base_url = settings.NGROK_BASE_URL.rstrip('/') + '/' if settings.DEBUG and getattr(settings, 'NGROK_BASE_URL', None) else request.build_absolute_uri('/')

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "PAYDUNYA-MASTER-KEY": settings.PAYDUNYA_KEYS["master_key"],
            "PAYDUNYA-PRIVATE-KEY": settings.PAYDUNYA_KEYS["private_key"],
            "PAYDUNYA-PUBLIC-KEY": settings.PAYDUNYA_KEYS["public_key"],
            "PAYDUNYA-TOKEN": settings.PAYDUNYA_KEYS["token"],
        }

        payload = {
            "invoice": {
                "items": [{
                    "name": "Versement épargne",
                    "quantity": 1,
                    "unit_price": montant_total,
                    "total_price": montant_total,
                    "description": f"Versement membre {member.user.nom} (frais: {frais_total} FCFA)"
                }],
                "description": f"Paiement épargne (+{frais_total} FCFA de frais)",
                "total_amount": montant_total,
                "callback_url": f"{base_url}groups/versement/callback/",
                "return_url": f"{base_url}groups/{group_id}/"
            },
            "store": {
                "name": "YaayESS",
                "tagline": "Plateforme de gestion financière",
                "website_url": "https://yaayess.com"
            },
            "custom_data": {
                "member_id": member.id,
                "user_id": request.user.id,
                "montant_saisi": int(montant_saisi),
                "frais_total": frais_total
            }
        }

        try:
            response = requests.post(
                "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create",
                headers=headers,
                json=payload,
                timeout=15
            )

            if response.status_code != 200:
                messages.error(request, f"Erreur PayDunya (HTTP {response.status_code}): {response.text}")
                return redirect("epargnecredit:initier_versement", member_id=member_id)

            try:
                data = response.json()
            except json.JSONDecodeError:
                messages.error(request, "Réponse invalide de PayDunya (format JSON incorrect)")
                return redirect("epargnecredit:initier_versement", member_id=member_id)

            if not isinstance(data, dict):
                messages.error(request, "Réponse invalide de PayDunya (format incorrect)")
                return redirect("epargnecredit:initier_versement", member_id=member_id)

            response_code = data.get("response_code")
            if response_code == "00":
                Versement.objects.create(
                    member=member,
                    montant=montant_saisi,
                    frais=frais_total,
                    methode="PAYDUNYA",
                    transaction_id=data.get("token", ""),
                    statut="en_attente"
                )

                invoice_url = data.get("response_text", {}).get("invoice_url", f"/groups/{group_id}/")
                return redirect(invoice_url)
            else:
                error_message = data.get("response_text", "Erreur inconnue")
                messages.error(request, f"Échec du paiement: {error_message}")
                return redirect("epargnecredit:initier_versement", member_id=member_id)

        except requests.exceptions.RequestException as e:
            messages.error(request, f"Erreur réseau PayDunya: {str(e)}")
            return redirect("epargnecredit:initier_versement", member_id=member_id)
        except Exception as e:
            messages.error(request, f"Erreur inattendue: {str(e)}")
            return redirect("epargnecredit:initier_versement", member_id=member_id)

    return render(request, "epargnecredit/initier_versement.html", {"member": member})


@csrf_exempt
def versement_callback(request):
    """
    Callback PayDunya pour confirmer un versement
    """
    try:
        data = json.loads(request.body)
        token = data.get("token")
    except Exception:
        return JsonResponse({"error": "Payload invalide"}, status=400)

    try:
        versement = Versement.objects.get(transaction_id=token)
        versement.statut = "valide"
        versement.save()

        member = versement.member
        member.montant += versement.montant
        member.save()

        return JsonResponse({"message": "✅ Versement confirmé"})
    except Versement.DoesNotExist:
        return JsonResponse({"error": "❌ Versement introuvable"}, status=404)


def versement_merci(request):
    """
    Page de remerciement après un versement
    """
    return render(request, "epargnecredit/versement_merci.html")

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import ActionLog
from epargnecredit.models import Group, GroupMember
#from accounts.models import Group, Member
from cotisationtontine.models import CotisationTontine  # Si utilisé pour versements

@login_required
def dashboard(request):
    # ✅ Récupérer le groupe de l'utilisateur
    try:
        group = Group.objects.get(admin=request.user)
    except Group.DoesNotExist:
        group = None

    # ✅ Membres du groupe
    membres = Member.objects.filter(group=group) if group else []

    # ✅ Logs d'actions (limités à 10)
    action_logs = ActionLog.objects.filter(group=group).order_by('-date')[:10]

    # ✅ Total des versements validés (si CotisationTontine utilisé pour Épargne)
    total_versements = 0
    if group:
        total_versements = CotisationTontine.objects.filter(
            member__group=group,
            statut="valide"
        ).aggregate(total=Sum('montant'))['total'] or 0

    # ✅ Passer les données au template
    return render(request, 'epargnecredit/dashboard.html', {
        'group': group,
        'membres': membres,
        'action_logs': action_logs,
        'total_versements': total_versements
    })


def editer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Éditer membre {membre_id} du groupe {group_id}")

def supprimer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Supprimer membre {membre_id} du groupe {group_id}")


def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Ici tu réinitialises les versements/crédits selon ta logique
    messages.info(request, f"Cycle réinitialisé pour le groupe {group.nom} (à implémenter).")
    return redirect("epargnecredit:group_detail", group_id=group.id)

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db import transaction
import random
from epargnecredit.models import Group, Tirage, GroupMember

@login_required
def tirage_au_sort_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Vérifier que seul l'admin ou un superuser peut tirer au sort
    if request.user != group.admin and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    def membres_eligibles_pour_tirage(group):
        membres = list(group.membres.filter(actif=True, exit_liste=False))
        total = len(membres)

        if total <= 1:
            return membres  # tout le monde éligible

        # Exclure le prochain gagnant s'il est défini et qu'il reste plus de 2 membres
        if group.prochain_gagnant and total > 2:
            membres = [m for m in membres if m.id != group.prochain_gagnant.id]

        return membres

    membres_eligibles = membres_eligibles_pour_tirage(group)

    gagnant = None
    montant_total = 0

    if membres_eligibles:
        gagnant = random.choice(membres_eligibles)

        # 💡 Si c'est le premier tirage, on fixe le montant pour tous les gagnants
        if group.montant_fixe_gagnant is None:
            montant_total = group.montant_base * group.membres.filter(actif=True, exit_liste=False).count()
            group.montant_fixe_gagnant = montant_total
            group.save()
        else:
            montant_total = group.montant_fixe_gagnant

        with transaction.atomic():
            # Enregistrer le tirage
            Tirage.objects.create(
                group=group,
                gagnant=gagnant,
                membre=gagnant,
                montant=montant_total,
            )

            # Déterminer le prochain gagnant à ignorer
            total_apres_tirage = group.membres.filter(actif=True, exit_liste=False).count() - 1
            if total_apres_tirage > 2:
                group.prochain_gagnant = gagnant
            else:
                group.prochain_gagnant = None
            group.save()

    context = {
        'group': group,
        'gagnant': gagnant,
        'montant_total': montant_total,
    }
    return render(request, 'epargnecredit/tirage_resultat.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Group, GroupMember, EpargneCredit, Tirage, TirageHistorique


@login_required
@transaction.atomic
def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Autoriser admin ou superuser
    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Seul l'administrateur ou un superutilisateur peut réinitialiser le cycle.")
        return redirect('epargnecredit:group_detail', group_id=group.id)

    # ✅ Afficher une confirmation avant la réinitialisation
    if request.method != 'POST':
        return render(request, 'epargnecredit/confirm_reset.html', {'group': group})

    # ✅ Vérifier que tous les membres ont déjà gagné
    membres = set(group.membres.all())
    gagnants_actuels = {tirage.gagnant for tirage in group.tirages.all() if tirage.gagnant}
    gagnants_historiques = {tirage.gagnant for tirage in group.tirages_historiques.all() if tirage.gagnant}

    tous_les_gagnants = gagnants_actuels.union(gagnants_historiques)
    membres_non_gagnants = membres - tous_les_gagnants

    if membres_non_gagnants:
        noms = ", ".join(m.user.username for m in membres_non_gagnants)
        messages.warning(request, f"Les membres suivants n'ont pas encore gagné : {noms}.")
        return redirect('epargnecredit:group_detail', group_id=group.id)

    # ✅ Archiver les tirages en cours
    tirages_actuels = group.tirages.all()
    TirageHistorique.objects.bulk_create([
        TirageHistorique(
            group=group,
            gagnant=tirage.gagnant,
            montant=tirage.montant,
            date_tirage=tirage.date_tirage or timezone.now()
        )
        for tirage in tirages_actuels
    ])

    # ✅ Supprimer les données du cycle en cours
    tirages_actuels.delete()
    epargnecredit.objects.filter(member__group=group).delete()

    # ✅ Marquer la date du nouveau cycle
    group.date_reset = timezone.now()
    if hasattr(group, 'cycle_en_cours'):
        group.cycle_en_cours = True
    group.save()

    messages.success(request, "✅ Cycle réinitialisé avec succès. Les membres peuvent recommencer les versements.")
    return redirect('epargnecredit:group_detail', group_id=group.id)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Group, GroupMember, EpargneCredit, Tirage, TirageHistorique
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse


@login_required
def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Vérifie si l'utilisateur connecté est l'admin du groupe
    if group.admin != request.user:
        messages.error(request, "Vous n'avez pas la permission de réinitialiser ce groupe.")
        return redirect('dashboard_epargne_credit')

    if request.method == 'POST':
        # Remettre à zéro les montants
        for membre in group.membres.all():
            membre.montant = 0
            membre.save()

        # Supprimer les cotisations et versements
        epargnecredit.objects.filter(member__group=group).delete()
        Versement.objects.filter(member__group=group).delete()

        # Date de reset
        group.date_reset = timezone.now()
        group.save()

        messages.success(request, f"✅ Le cycle du groupe « {group.nom} » a été réinitialisé avec succès.")
        return redirect('epargnecredit:group_detail', group_id=group.id)

    return render(request, 'epargnecredit/confirm_reset_cycle.html', {'group': group})


def tirage_resultat_view(request, group_id):
    # logiquement, on affiche les résultats ici
    return render(request, 'epargnecredit/tirage_resultat.html', {'group_id': group_id})

# epargnecredit/views.py

from django.shortcuts import render, get_object_or_404
#from .models import Group, Cycle
from django.contrib.auth.decorators import login_required

@login_required
def historique_cycles_view(request, group_id):
    """
    Affiche l'historique des cycles passés d'un groupe.
    """
    group = get_object_or_404(Group, id=group_id)

    # Récupération des cycles archivés (ex: statut = "fini")
    anciens_cycles = (
        Cycle.objects.filter(group=group)
        .exclude(date_fin__isnull=True)  # On garde que les cycles terminés
        .prefetch_related(
            "etapes__tirage__beneficiaire__user"
        )  # Optimise les requêtes
        .order_by("-date_debut")
    )

    context = {
        "group": group,
        "anciens_cycles": anciens_cycles
    }
    return render(request, "epargnecredit/historique_cycles.html", context)


import logging
import requests
import json
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Group, Tirage, PaiementGagnant

logger = logging.getLogger(__name__)

@login_required
def payer_gagnant(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Récupérer le dernier tirage gagnant
    dernier_tirage = Tirage.objects.filter(group=group).order_by('-date_tirage').first()

    if not dernier_tirage or not dernier_tirage.gagnant:
        messages.error(request, "Aucun gagnant défini pour ce groupe.")
        return redirect('group_detail', group_id=group.id)

    gagnant = dernier_tirage.gagnant

    # 💡 Utiliser le montant fixe si défini, sinon le calculer
    if group.montant_fixe_gagnant is not None:
        montant_total = group.montant_fixe_gagnant
    else:
        montant_total = group.montant_base * group.membres.filter(actif=True, exit_liste=False).count()

    if request.method == 'POST':
        montant_total = Decimal(montant_total)

        frais_pourcent = montant_total * Decimal('0.02')
        frais_fixe = Decimal('50')
        frais_total = (frais_pourcent + frais_fixe).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        montant_total_avec_frais = (montant_total + frais_total).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        montant_total_avec_frais_int = int(montant_total_avec_frais)
        frais_total_int = int(frais_total)

        if settings.DEBUG and getattr(settings, 'NGROK_BASE_URL', None):
            base_url = settings.NGROK_BASE_URL.rstrip('/') + '/'
        else:
            base_url = request.build_absolute_uri('/')

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "PAYDUNYA-MASTER-KEY": settings.PAYDUNYA_KEYS["master_key"],
            "PAYDUNYA-PRIVATE-KEY": settings.PAYDUNYA_KEYS["private_key"],
            "PAYDUNYA-PUBLIC-KEY": settings.PAYDUNYA_KEYS["public_key"],
            "PAYDUNYA-TOKEN": settings.PAYDUNYA_KEYS["token"],
        }

        payload = {
            "invoice": {
                "items": [{
                    "name": "Paiement gagnant epargnecredit",
                    "quantity": 1,
                    "unit_price": montant_total_avec_frais_int,
                    "total_price": montant_total_avec_frais_int,
                    "description": f"Paiement {gagnant.user.nom} - Frais {frais_total_int} FCFA"
                }],
                "description": f"Versement gagnant (+{frais_total_int} FCFA de frais)",
                "total_amount": montant_total_avec_frais_int,
                "callback_url": f"{base_url}epargnecredit/paiement_gagnant/callback/",
                "return_url": f"{base_url}epargnecredit/paiement_gagnant/merci/"
            },
            "store": {
                "name": "YaayESS",
                "tagline": "Plateforme de gestion financière",
                "website_url": "https://yaayess.com"
            },
            "custom_data": {
                "group_id": group.id,
                "gagnant_id": gagnant.id,
                "montant_saisi": int(montant_total),
                "frais_total": frais_total_int
            }
        }

        try:
            logger.info("⏳ Envoi requête PayDunya...")
            response = requests.post(
                "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create",
                headers=headers,
                json=payload,
                timeout=15
            )
            logger.info(f"✅ Statut HTTP PayDunya : {response.status_code}")

            if response.status_code != 200:
                messages.error(request, f"Erreur PayDunya : {response.text}")
                return redirect('group_detail', group_id=group.id)

            data = response.json()
            logger.debug(f"🧾 Réponse JSON PayDunya : {json.dumps(data, indent=2)}")

            if data.get("response_code") == "00":
                PaiementGagnant.objects.create(
                    group=group,
                    gagnant=gagnant,
                    montant=montant_total,
                    statut='EN_ATTENTE',
                    transaction_id=data.get("token"),
                    message="Paiement en attente validation PayDunya"
                )
                return redirect(data.get("response_text"))  # Redirection vers PayDunya
            else:
                messages.error(request, f"Échec création paiement : {data.get('response_text')}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau PayDunya: {e}")
            messages.error(request, f"Erreur réseau PayDunya: {str(e)}")

        return redirect('group_detail', group_id=group.id)

    return render(request, 'epargnecredit/payer_gagnant.html', {
        'group': group,
        'gagnant': gagnant,
        'montant_total': montant_total,
    })

import json
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import PaiementGagnant

logger = logging.getLogger(__name__)

@csrf_exempt  # PayDunya ne peut pas envoyer le CSRF token
def paiement_gagnant_callback(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    try:
        data = json.loads(request.body)
        logger.info(f"Callback PayDunya reçu: {json.dumps(data)}")

        token = data.get('token')
        status = data.get('status')  # Ex: "PAID", "FAILED", etc.
        response_code = data.get('response_code')
        response_text = data.get('response_text', '')

        if not token:
            return JsonResponse({"error": "Token manquant"}, status=400)

        # Chercher le PaiementGagnant par transaction_id (token)
        paiement = PaiementGagnant.objects.filter(transaction_id=token).first()
        if not paiement:
            logger.error(f"PaiementGagnant introuvable pour token={token}")
            return JsonResponse({"error": "Paiement introuvable"}, status=404)

        # Mettre à jour le statut selon la réponse
        if response_code == "00" and status == "PAID":
            paiement.statut = 'SUCCES'
        else:
            paiement.statut = 'ECHEC'

        paiement.message = response_text
        paiement.save()

        logger.info(f"PaiementGagnant {token} mis à jour avec statut {paiement.statut}")

        return JsonResponse({"success": True})

    except json.JSONDecodeError:
        logger.error("Corps JSON invalide dans callback PayDunya")
        return JsonResponse({"error": "JSON invalide"}, status=400)
    except Exception as e:
        logger.error(f"Erreur inattendue dans callback PayDunya: {e}")
        return JsonResponse({"error": "Erreur serveur"}, status=500)

from django.shortcuts import render

def paiement_gagnant_merci(request):
    return render(request, 'epargnecredit/paiement_gagnant_merci.html')


from django.shortcuts import render
from .models import PaiementGagnant

def liste_paiements_gagnants(request):
    paiements = PaiementGagnant.objects.select_related('gagnant__user', 'group').order_by('-date_paiement')
    return render(request, 'epargnecredit/paiement_gagnant.html', {
        'paiements': paiements
    })

# epargnecredit/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ActionLog

@login_required
def historique_actions_view(request):
    """
    Affiche l'historique des actions enregistrées dans ActionLog.
    """
    # Récupération des logs déjà triés via Meta.ordering
    logs = ActionLog.objects.select_related("user")

    return render(request, "epargnecredit/historique_actions.html", {
        "logs": logs
    })


from django.db.models import Count


def membres_eligibles_pour_tirage(group):
    # Récupère le dernier tirage et son gagnant
    dernier_tirage = group.tirages.order_by('-date').first()  # adapte selon ton related_name
    membres = group.members.all()  # adapte selon ton related_name

    # Si le groupe a 1 membre ou moins, tous sont éligibles (pas d'exclusion)
    if membres.count() <= 1:
        return membres

    # Sinon, exclut le dernier gagnant du tirage
    if dernier_tirage:
        membres = membres.exclude(id=dernier_tirage.gagnant.id)

    return membres
