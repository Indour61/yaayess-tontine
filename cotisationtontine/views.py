from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from .utils import envoyer_invitation  # à implémenter pour Twilio/SMS
from django.db import models


# ✅ Page d’accueil qui redirige vers le dashboard
def landing_view(request):
    # Ici tu peux mettre du contenu statique ou rediriger
    return render(request, 'cotisationtontine/dashboard.html')


# ✅ Dashboard principal
@login_required
def dashboard_tontine_simple(request):
    # Si tu veux des données spécifiques au dashboard, tu peux les passer ici
    action_logs = []  # exemple, charge tes logs réels si tu en as
    return render(request, 'cotisationtontine/dashboard.html', {
        'action_logs': action_logs,
    })


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from cotisationtontine.forms import GroupForm
from cotisationtontine.models import Group, GroupMember, Invitation
from accounts.utils import envoyer_invitation  # Assurez-vous que cette fonction existe

@login_required
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
            # ✅ Créer le groupe
            group = form.save(commit=False)
            group.admin = request.user
            group.save()

            # ✅ Ajoute l'admin comme membre du groupe
            GroupMember.objects.get_or_create(group=group, user=request.user)

            # ✅ Génère une invitation avec expiration (48h)
            invitation = Invitation.objects.create(
                group=group,
                phone=request.user.phone,
                expire_at=timezone.now() + timedelta(days=2)
            )

            # ✅ Crée un lien d'invitation sécurisé
            lien_invitation = request.build_absolute_uri(
                reverse("accounts:inscription_et_rejoindre", args=[invitation.token])
            )

            # ✅ Simule l'envoi de l'invitation (WhatsApp ou SMS)
            envoyer_invitation(request.user.phone, lien_invitation)

            # ✅ Message de confirmation
            messages.success(request, f"Groupe « {group.nom} » créé avec succès et vous avez été ajouté comme membre.")

            # ✅ Redirection vers le dashboard Tontine
            return redirect("cotisationtontine:dashboard_tontine_simple")
    else:
        form = GroupForm()

    return render(
        request,
        "cotisationtontine/ajouter_groupe.html",
        {"form": form, "title": "Créer un groupe"}
    )

from cotisationtontine.utils import envoyer_invitation
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from datetime import timedelta

from .utils import envoyer_invitation  # fonction d’envoi

from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Group, GroupMember
from accounts.models import CustomUser  # ou le modèle utilisateur que tu utilises

@login_required
def ajouter_membre_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Vérification des droits : seul l'admin du groupe peut ajouter
    if group.admin != request.user:
        messages.error(request, "⚠️ Vous n'avez pas les droits pour ajouter un membre à ce groupe.")
        return redirect("cotisationtontine:dashboard_tontine_simple")

    if request.method == "POST":
        phone = request.POST.get("phone")
        nom = request.POST.get("nom")

        if not phone:
            messages.error(request, "Veuillez renseigner un numéro de téléphone.")
            return redirect("cotisationtontine:ajouter_membre", group_id=group_id)

        # Vérifier si un utilisateur existe déjà
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={"nom": nom or phone}
        )

        # Ajouter dans GroupMember si pas déjà présent
        group_member, gm_created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
        )

        if gm_created:
            messages.success(request, f"✅ {user.nom} a bien été ajouté au groupe {group.nom}.")
        else:
            messages.info(request, f"ℹ️ {user.nom} est déjà membre de ce groupe.")

        return redirect("cotisationtontine:group_detail", group_id=group.id)

    return render(request, "cotisationtontine/ajouter_membre.html", {"group": group})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Group, GroupMember, Versement, ActionLog
from .forms import GroupForm, GroupMemberForm, VersementForm

@login_required
def dashboard(request):
    action_logs = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]
    return render(request, 'cotisationtontine/dashboard.html', {
        'action_logs': action_logs
    })
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Group  # ton modèle de groupe

@login_required
def group_list(request):
    # Selon ton modèle, adapte le filtre :
    # Si tu as un champ ManyToMany via GroupMember :
    groups = Group.objects.filter(membres__user=request.user).distinct()

    return render(request, 'cotisationtontine/group_list.html', {
        'groups': groups
    })



# ✅ Vue à garder
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Group, GroupMember, Versement, ActionLog


@login_required
def group_detail(request, group_id):
    # Récupérer le groupe
    group = get_object_or_404(Group, id=group_id)

    # Tous les membres du groupe
    membres = group.membres.select_related('user')

    # ✅ Récupération des versements du groupe
    versements = Versement.objects.filter(member__group=group)
    total_montant = versements.aggregate(total=Sum('montant'))['total'] or 0

    # Total des versements par membre
    versements_par_membre = versements.values('member').annotate(total_montant=Sum('montant'))
    montants_membres_dict = {v['member']: v['total_montant'] for v in versements_par_membre}

    # Ajouter le montant à chaque membre
    for membre in membres:
        membre.montant = montants_membres_dict.get(membre.id, 0)

    # ✅ Vérification admin
    admin_user = group.admin
    user_is_admin = request.user == admin_user or getattr(request.user, "is_super_admin", False)

    # ✅ Historique des actions
    actions = ActionLog.objects.filter(group=group).order_by('-date') if hasattr(ActionLog, "group") else []

    # ✅ Lien d'invitation absolu correct pour WhatsApp ou email
    invite_url = request.build_absolute_uri(
        reverse('accounts:inscription_et_rejoindre', args=[group.code_invitation])
    )

    # Stocker dernier lien généré dans la session (optionnel)
    if user_is_admin:
        request.session['last_invitation_link'] = invite_url

    context = {
        'group': group,
        'membres': membres,
        'versements': versements,
        'total_montant': total_montant,
        'admin_user': admin_user,
        'actions': actions,
        'user_is_admin': user_is_admin,
        'invite_url': invite_url,
        'last_invitation_link': request.session.get('last_invitation_link'),
    }

    return render(request, 'cotisationtontine/group_detail.html', context)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Group

@login_required
def group_list_view(request):
    """
    Affiche la liste des groupes :
    - Tous les groupes si super admin
    - Sinon, seulement ceux créés par l'utilisateur
    """
    if request.user.is_super_admin:
        groupes = Group.objects.all()
    else:
        groupes = Group.objects.filter(admin=request.user)

    return render(request, 'cotisationtontine/group_list.html', {
        'groupes': groupes
    })



from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import ActionLog

@login_required
def dashboard_epargne_credit(request):
    # Récupérer les dernières actions de l’utilisateur connecté
    action_logs = ActionLog.objects.filter(user=request.user).order_by('-date')[:10]

    return render(request, 'cotisationtontine/dashboard.html', {
        'action_logs': action_logs
    })



def editer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Éditer membre {membre_id} du groupe {group_id}")

def supprimer_membre_view(request, group_id, membre_id):
    return HttpResponse(f"Supprimer membre {membre_id} du groupe {group_id}")


def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    # Ici tu réinitialises les versements/crédits selon ta logique
    messages.info(request, f"Cycle réinitialisé pour le groupe {group.nom} (à implémenter).")
    return redirect("cotisationtontine:group_detail", group_id=group.id)


@login_required
def initier_versement(request, member_id):
    member = get_object_or_404(GroupMember, id=member_id)
    group_id = member.group.id  # ID du groupe pour la redirection

    if request.method == 'POST':
        try:
            montant_saisi = float(request.POST.get('montant', 0))
            if montant_saisi <= 0:
                return JsonResponse({"error": "Montant doit être supérieur à 0"}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Montant invalide"}, status=400)

        methode = request.POST.get('methode', 'paydunya').lower()

        if methode == 'caisse':
            Versement.objects.create(
                member=member,
                montant=montant_saisi,
                frais=0,
                methode="CAISSE",
                transaction_id="CAISSE-" + str(member.id)
            )
            member.montant += Decimal(montant_saisi)
            member.save()

            messages.success(request, f"Versement de {montant_saisi} FCFA enregistré via Caisse.")
            # 🔹 Redirection vers le détail du groupe
            return redirect('cotisationtontine:group_detail', group_id=group_id)

        # --- PayDunya ---
        frais_pourcent = montant_saisi * 0.02
        frais_fixe = 50
        frais_total = int(round(frais_pourcent + frais_fixe))
        montant_total = int(round(montant_saisi + frais_total))

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
                    "name": "Versement épargne",
                    "quantity": 1,
                    "unit_price": montant_total,
                    "total_price": montant_total,
                    "description": f"Versement membre {member.user.nom} (frais: {frais_total} FCFA)"
                }],
                "description": f"Paiement épargne (+{frais_total} FCFA de frais)",
                "total_amount": montant_total,
                # 🔹 Callback et return vers la page du groupe
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

            data = response.json()
            if data.get("response_code") == "00":
                Versement.objects.create(
                    member=member,
                    montant=montant_saisi,
                    frais=frais_total,
                    methode="PAYDUNYA",
                    transaction_id=data.get("token")
                )
                # 🔹 Redirection vers la page du groupe après PayDunya
                return redirect(f"/groups/{group_id}/")
            else:
                return JsonResponse({"error": "Échec du paiement", "details": data.get("response_text")}, status=400)

        except requests.exceptions.RequestException as e:
            return JsonResponse({"error": "Erreur réseau PayDunya", "details": str(e)}, status=500)

    return render(request, "cotisationtontine/initier_versement.html", {"member": member})


#@csrf_exempt
def versement_callback(request):
    try:
        data = json.loads(request.body)
        token = data.get("token")
    except Exception:
        return JsonResponse({"error": "Payload invalide"}, status=400)

    try:
        versement = Versement.objects.get(transaction_id=token)
        versement.statut = "valide"
        versement.save()
        return JsonResponse({"message": "✅ Versement confirmé"})
    except Versement.DoesNotExist:
        return JsonResponse({"error": "❌ Versement introuvable"}, status=404)

def versement_merci(request):
    return render(request, "cotisationtontine/versement_merci.html")

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db import transaction
import random
from cotisationtontine.models import Group, Tirage, GroupMember

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
    return render(request, 'cotisationtontine/tirage_resultat.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from .models import Group, GroupMember, CotisationTontine, Tirage, TirageHistorique

@login_required
@transaction.atomic
def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Autoriser admin ou superuser
    if request.user != group.admin and not request.user.is_superuser:
        messages.error(request, "Seul l'administrateur ou un superutilisateur peut réinitialiser le cycle.")
        return redirect('cotisationtontine:group_detail', group_id=group.id)

    # ✅ Afficher une confirmation avant la réinitialisation
    if request.method != 'POST':
        return render(request, 'cotisationtontine/confirm_reset.html', {'group': group})

    # ✅ Vérifier que tous les membres ont déjà gagné
    membres = set(group.membres.all())
    gagnants_actuels = {tirage.gagnant for tirage in group.tirages.all() if tirage.gagnant}
    gagnants_historiques = {tirage.gagnant for tirage in group.tirages_historiques.all() if tirage.gagnant}

    tous_les_gagnants = gagnants_actuels.union(gagnants_historiques)
    membres_non_gagnants = membres - tous_les_gagnants

    if membres_non_gagnants:
        noms = ", ".join(m.user.username for m in membres_non_gagnants)
        messages.warning(request, f"Les membres suivants n'ont pas encore gagné : {noms}.")
        return redirect('cotisationtontine:group_detail', group_id=group.id)

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
    CotisationTontine.objects.filter(member__group=group).delete()

    # ✅ Marquer la date du nouveau cycle
    group.date_reset = timezone.now()
    if hasattr(group, 'cycle_en_cours'):
        group.cycle_en_cours = True
    group.save()

    messages.success(request, "✅ Cycle réinitialisé avec succès. Les membres peuvent recommencer les versements.")
    return redirect('cotisationtontine:group_detail', group_id=group.id)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from cotisationtontine.models import Group, CotisationTontine, Versement, GroupMember
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse


@login_required
def reset_cycle_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Vérifie si l'utilisateur connecté est l'admin du groupe
    if group.admin != request.user:
        messages.error(request, "Vous n'avez pas la permission de réinitialiser ce groupe.")
        return redirect('dashboard_tontine_simple')

    if request.method == 'POST':
        # Remettre à zéro les montants
        for membre in group.membres.all():
            membre.montant = 0
            membre.save()

        # Supprimer les cotisations et versements
        CotisationTontine.objects.filter(member__group=group).delete()
        Versement.objects.filter(member__group=group).delete()

        # Date de reset
        group.date_reset = timezone.now()
        group.save()

        messages.success(request, f"✅ Le cycle du groupe « {group.nom} » a été réinitialisé avec succès.")
        return redirect('cotisationtontine:group_detail', group_id=group.id)

    return render(request, 'cotisationtontine/confirm_reset_cycle.html', {'group': group})


def tirage_resultat_view(request, group_id):
    # logiquement, on affiche les résultats ici
    return render(request, 'cotisationtontine/tirage_resultat.html', {'group_id': group_id})

# cotisationtontine/views.py

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
    return render(request, "cotisationtontine/historique_cycles.html", context)


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
                    "name": "Paiement gagnant Tontine",
                    "quantity": 1,
                    "unit_price": montant_total_avec_frais_int,
                    "total_price": montant_total_avec_frais_int,
                    "description": f"Paiement {gagnant.user.nom} - Frais {frais_total_int} FCFA"
                }],
                "description": f"Versement gagnant (+{frais_total_int} FCFA de frais)",
                "total_amount": montant_total_avec_frais_int,
                "callback_url": f"{base_url}cotisationtontine/paiement_gagnant/callback/",
                "return_url": f"{base_url}cotisationtontine/paiement_gagnant/merci/"
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

    return render(request, 'cotisationtontine/payer_gagnant.html', {
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
    return render(request, 'cotisationtontine/paiement_gagnant_merci.html')


from django.shortcuts import render
from .models import PaiementGagnant

def liste_paiements_gagnants(request):
    paiements = PaiementGagnant.objects.select_related('gagnant__user', 'group').order_by('-date_paiement')
    return render(request, 'cotisationtontine/paiement_gagnant.html', {
        'paiements': paiements
    })

# cotisationtontine/views.py

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

    return render(request, "cotisationtontine/historique_actions.html", {
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
