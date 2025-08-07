from django import forms
from .models import Group, GroupMember, Versement
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

# ✅ Formulaire de création de groupe
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['nom', 'montant_base']  # Ajout du champ montant_base
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du groupe'
            }),
            'montant_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Montant de base (ex: 5000)'
            }),
        }
        labels = {
            'nom': 'Nom du groupe',
            'montant_base': 'Montant de base du groupe (FCFA)',
        }

# ✅ Formulaire d’ajout de membre
class GroupMemberForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].label_from_instance = lambda obj: f"{obj.nom} ({obj.phone})"

    class Meta:
        model = GroupMember
        fields = ['user']


# ✅ Formulaire de versement

# cotisationtontine/forms.py

from django import forms
from .models import Versement

class VersementForm(forms.ModelForm):
    class Meta:
        model = Versement
        fields = ['member', 'montant', 'methode']  # ❌ 'statut' supprimé
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'methode': forms.Select(attrs={'class': 'form-select'}),  # ✅ on garde ce champ
        }

    def __init__(self, *args, **kwargs):
        super(VersementForm, self).__init__(*args, **kwargs)
        self.fields['methode'].choices = [
            ('paydunya', 'PayDunya'),
            ('caisse', 'Caisse (sans frais)'),
        ]

# ✅ Formulaire d’inscription utilisateur
class RegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['nom', 'phone', 'password1', 'password2']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom complet'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre numéro de téléphone'
            }),
        }
