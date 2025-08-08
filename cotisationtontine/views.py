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

from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import GroupForm
from .models import Group, GroupMember, Invitation
from .utils import envoyer_invitation  # si défini ailleurs

@login_required
def ajouter_groupe_view(request):
    if request.method == "POST":
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()

            # ✅ Ajoute le créateur comme membre du groupe
            GroupMember.objects.create(group=group, user=request.user)

            # ✅ Crée une invitation pour l’admin (optionnel ici mais logique si le système l’exige)
            invitation = Invitation.objects.create(
                group=group,
                phone=request.user.phone,
                expire_at=timezone.now() + timedelta(days=2)
            )
            lien = request.build_absolute_uri(
                reverse("accounts:login")
            ) + f"?token={invitation.token}"
            envoyer_invitation(request.user.phone, lien)

            messages.success(request, f"Groupe « {group.nom} » créé et vous êtes membre.")
            return redirect("cotisationtontine:dashboard_tontine_simple")
    else:
        form = GroupForm()

    return render(
        request,
        "cotisationtontine/ajouter_groupe.html",
        {"form": form, "title": "Créer un groupe"}
    )


from cotisationtontine.utils import envoyer_invitation
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from cotisationtontine.models import Invitation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Group, Invitation, GroupMember
from .utils import envoyer_invitation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .models import Group, GroupMember, Invitation
from .utils import envoyer_invitation


from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from datetime import timedelta

from cotisationtontine.models import Group, GroupMember, Invitation
from accounts.models import CustomUser  # modèle utilisateur
from .utils import envoyer_invitation  # fonction d’envoi

@login_required
def ajouter_membre_view(request, group_id):
    """
    Ajoute un membre en créant une invitation liée au groupe.
    Crée aussi un CustomUser s'il n'existe pas encore pour le numéro donné
    et ajoute ce membre dans GroupMember pour qu'il apparaisse immédiatement.
    """
    group = get_object_or_404(Group, id=group_id)

    # Vérification des droits : seul un ADMIN du groupe peut ajouter
    is_admin = GroupMember.objects.filter(group=group, user=request.user ).exists()
    if not is_admin:
        messages.error(request, "⚠️ Vous n'avez pas les droits pour ajouter un membre à ce groupe.")
        return redirect("cotisationtontine:dashboard_tontine_simple")

    if request.method == "POST":
        phone = request.POST.get("phone")
        nom = request.POST.get("nom")  # tu peux ajouter un champ nom dans ton formulaire
        if not phone:
            messages.error(request, "Veuillez renseigner un numéro de téléphone.")
            return redirect("cotisationtontine:ajouter_membre", group_id=group_id)

        # Vérifier si un utilisateur existe déjà pour ce téléphone
        user, created = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={"nom": nom or phone}  # nom par défaut si non fourni
        )

        # Ajouter dans GroupMember si pas déjà présent
        group_member, gm_created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
        #    defaults={'role": "MEMBRE"}  # rôle par défaut
        )

        # Créer l'invitation
        invitation = Invitation.objects.create(
            group=group,
            phone=phone,
            expire_at=timezone.now() + timedelta(days=2)
        )

        # Générer le lien d’invitation
        lien_invitation = request.build_absolute_uri(reverse("accounts:login")) + f"?token={invitation.token}"

        # Envoyer l’invitation (WhatsApp/SMS simulé)
        try:
            envoyer_invitation(phone, lien_invitation)
            messages.success(
                request,
                f"✅ Invitation envoyée à {phone}.<br>🔗 <a href='{lien_invitation}' target='_blank'>{lien_invitation}</a>"
            )
        except Exception as e:
            messages.error(
                request,
                f"❌ Impossible d’envoyer l’invitation : {e}"
            )

        # Rediriger vers le détail du groupe : le nouveau membre apparaîtra dans la liste
        return redirect("cotisationtontine:group_detail", group_id=group_id)

    # GET : afficher le formulaire d’ajout
    return render(request, "cotisationtontine/ajouter_membre.html", {
        "group": group
    })


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
from .models import Group, GroupMember, Versement

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    membres = group.membres.select_related('user')

#    user_is_admin = group.membres.filter(user=request.user, role='ADMIN').exists()

    # Versements du groupe
    versements = Versement.objects.filter(member__group=group)
    total_montant = versements.aggregate(total=Sum('montant'))['total'] or 0

    # Total des versements par membre
    versements_par_membre = versements.values('member').annotate(total_montant=Sum('montant'))
    montants_membres_dict = {v['member']: v['total_montant'] for v in versements_par_membre}

    for membre in membres:
        membre.montant = montants_membres_dict.get(membre.id, 0)

    # ✅ Ajout : stocker l'admin dans le contexte
    admin_user = group.admin  # CustomUser

    return render(request, 'cotisationtontine/group_detail.html', {
        'group': group,
        'membres': membres,
        'versements': versements,
        'total_montant': total_montant,
        'admin_user': admin_user,  # ⬅️ Ajouté
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

from cotisationtontine.models import GroupMember, Versement
import logging
import requests
import json
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

logger = logging.getLogger(__name__)

@login_required
def initier_versement(request, member_id):
    member = get_object_or_404(GroupMember, id=member_id)

    if request.method == 'POST':
        try:
            montant_saisi = float(request.POST.get('montant', 0))
            if montant_saisi <= 0:
                return JsonResponse({"error": "Montant doit être supérieur à 0"}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Montant invalide"}, status=400)

        methode = request.POST.get('methode', 'paydunya').lower()

        if methode == 'caisse':
            # ✅ Enregistrement direct sans frais
            Versement.objects.create(
                member=member,
                montant=montant_saisi,
                frais=0,
                methode="CAISSE",
                transaction_id="CAISSE-" + str(member.id)
            )
            # ✅ Mise à jour du solde dans GroupMember
            member.montant += Decimal(montant_saisi)
            member.save()

            messages.success(request, f"Versement de {montant_saisi} FCFA enregistré via Caisse.")
            return redirect('cotisationtontine:dashboard_tontine_simple')

        # ✅ Sinon : PayDunya
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
                "callback_url": f"{base_url}cotisationtontine/versement/callback/",
                "return_url": f"{base_url}cotisationtontine/versement/merci/"
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
            logger.info("⏳ Envoi de la requête à PayDunya...")
            response = requests.post(
                "https://app.paydunya.com/sandbox-api/v1/checkout-invoice/create",
                headers=headers,
                json=payload,
                timeout=15
            )
            logger.info(f"✅ Statut HTTP PayDunya : {response.status_code}")

            if response.status_code != 200:
                return JsonResponse({"error": "Erreur PayDunya", "details": response.text}, status=500)

            data = response.json()
            logger.debug(f"🧾 Réponse JSON PayDunya : {json.dumps(data, indent=2)}")

            if data.get("response_code") == "00":
                Versement.objects.create(
                    member=member,
                    montant=montant_saisi,
                    frais=frais_total,
                    methode="PAYDUNYA",
                    transaction_id=data.get("token")
                )
                return redirect(data.get("response_text"))
            else:
                return JsonResponse({"error": "Échec du paiement", "details": data.get("response_text")}, status=400)

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur réseau PayDunya: {e}")
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


from django.utils import timezone
from .models import Invitation, GroupMember

@login_required
def accepter_invitation(request, token):
    invitation = get_object_or_404(Invitation, token=token)

    if not invitation.est_valide():
        messages.error(request, "Lien d'invitation expiré ou déjà utilisé.")
        return redirect('cotisationtontine:dashboard_tontine_simple')

    group = invitation.group

    # Vérifie si l'utilisateur est déjà membre
    membre_existant = GroupMember.objects.filter(group=group, user=request.user).exists()
    if not membre_existant:
        GroupMember.objects.create(group=group, user=request.user, role='MEMBRE')

    # Marquer comme utilisée
    invitation.used = True
    invitation.save()

    messages.success(request, f"Bienvenue dans le groupe {group.nom} !")
    return redirect('cotisationtontine:group_detail', group_id=group.id)

from datetime import timedelta
from django.utils import timezone
from .models import Invitation

def creer_invitation(group, phone):
    expiration = timezone.now() + timedelta(days=7)
    invitation = Invitation.objects.create(
        group=group,
        phone=phone,
        expire_at=expiration
    )
    return invitation

from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from .models import Invitation, Group, GroupMember

@require_POST
@login_required
def creer_invitation_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # Vérifie que l'utilisateur est admin du groupe
    is_admin = GroupMember.objects.filter(group=group, user=request.user, role='ADMIN').exists()
    if not is_admin:
        messages.error(request, "Vous n'avez pas l'autorisation de générer une invitation pour ce groupe.")
        return redirect('cotisationtontine:group_detail', group_id=group.id)

    phone = request.POST.get('phone')
    if not phone:
        messages.error(request, "Numéro de téléphone requis.")
        return redirect('cotisationtontine:group_detail', group_id=group.id)

    # Créer une nouvelle invitation valide 7 jours
    expiration = timezone.now() + timedelta(days=7)
    invitation = Invitation.objects.create(
        group=group,
        phone=phone,
        expire_at=expiration
    )

    # Générer le lien
    invitation_link = request.build_absolute_uri(
        reverse('cotisationtontine:accepter_invitation', args=[str(invitation.token)])
    )

    # Stocker temporairement dans session pour affichage dans group_detail
    request.session['last_invitation_link'] = invitation_link

    messages.success(request, f"Lien d'invitation généré pour {phone}")
    return redirect('cotisationtontine:group_detail', group_id=group.id)

from django.db.models import Sum
import random


from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import random

from cotisationtontine.models import Group, Tirage

@login_required
def tirage_au_sort_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    # ✅ Vérifier que seul l'admin du groupe ou un superuser peut lancer un tirage
    if request.user != group.admin and not request.user.is_superuser:
        return render(request, '403.html', status=403)

    # ✅ Filtrer uniquement les membres actifs et non exclus
    membres_eligibles = group.membres.filter(actif=True, exit_liste=False)

    gagnant = None
    montant_total = 0

    if membres_eligibles.exists():
        # ✅ Choisir un gagnant au hasard
        gagnant = random.choice(list(membres_eligibles))

        # ✅ Calcul simplifié du montant total attendu
        montant_total = group.montant_base * membres_eligibles.count()

        # ✅ Enregistrement du tirage
        Tirage.objects.create(
            group=group,
            gagnant=gagnant,
            membre=gagnant,
            montant=montant_total,
        )

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


from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
import random, string

def inscription_par_invit(request, code):
    group = get_object_or_404(Group, code_invitation=code)

    if request.method == 'POST':
        nom = request.POST.get('nom')
        telephone = request.POST.get('telephone')

        if CustomUser.objects.filter(phone=telephone).exists():
            messages.error(request, "Ce numéro est déjà utilisé.")
        else:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = CustomUser.objects.create_user(
                phone=telephone,
                nom=nom,
                password=password,
            )
            GroupMember.objects.create(
                group=group,
                user=user,
            )
            messages.success(request, f"Bienvenue dans le groupe {group.nom} ! Vous pouvez maintenant vous connecter.")
            return redirect('accounts:login')

    return render(request, 'cotisationtontine/inscription_par_invit.html', {'group': group})

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Group, GroupMember

@login_required
def rejoindre_par_lien(request, token):
    group = get_object_or_404(Group, invitation_token=token)

    # Vérifie si l'utilisateur est déjà membre
    if GroupMember.objects.filter(group=group, user=request.user).exists():
        messages.info(request, "Vous êtes déjà membre de ce groupe.")
        return redirect('cotisationtontine:group_detail', group.id)

    # Ajouter l'utilisateur au groupe
    GroupMember.objects.create(group=group, user=request.user)
    messages.success(request, f"Vous avez rejoint le groupe {group.nom}.")
    return redirect('cotisationtontine:group_detail', group.id)

# views.py
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import CustomUser
from .models import Group, GroupMember
import random
import string

def rejoindre_groupe(request, uuid_code):
    group = get_object_or_404(Group, code_invitation=uuid_code)
    message = None

    if request.method == 'POST':
        nom = request.POST.get('nom')
        phone = request.POST.get('phone')

        if Member.objects.filter(group=group, phone=phone).exists():
            message = "Vous êtes déjà membre de ce groupe."
        else:
            # Crée un compte utilisateur automatiquement
            if not CustomUser.objects.filter(phone=phone).exists():
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                CustomUser.objects.create_user(phone=phone, nom=nom, password=password)

            user = CustomUser.objects.get(phone=phone)
            Member.objects.create(nom=nom, phone=phone, user=user, group=group)

            message = f"Bienvenue {nom}, vous avez été ajouté au groupe {group.nom} avec succès !"

    return render(request, 'rejoindre_groupe.html', {'group': group, 'message': message})


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

    # Montant de base × membres éligibles
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
                return redirect(data.get("response_text"))  # Redirection vers la page paiement PayDunya
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
