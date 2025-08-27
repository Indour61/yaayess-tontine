from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

# ----------------------------------------------------
# Choix d'inscription
# ----------------------------------------------------
OPTION_CHOICES = (
    ('1', 'Cotisation & Tontine'),
    ('2', 'Epargne & Crédit'),
)

# ----------------------------------------------------
# Formulaire d'inscription pour un utilisateur normal
# ----------------------------------------------------
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    option = forms.ChoiceField(
        choices=OPTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Option d'inscription"
    )

    class Meta:
        model = CustomUser
        fields = ('phone', 'nom', 'option')  # ajout du champ option

    def clean_password2(self):
        pw1 = self.cleaned_data.get('password1')
        pw2 = self.cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.option = self.cleaned_data['option']  # sauvegarde de l'option
        if commit:
            user.save()
        return user

# ----------------------------------------------------
# Formulaire de connexion
# ----------------------------------------------------
class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulaire d'authentification personnalisé avec choix de l'option.
    """
    username = forms.CharField(
        label=_("Nom d'utilisateur ou téléphone"),
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Votre nom complet ou téléphone',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Votre mot de passe',
            'class': 'form-control'
        }),
        strip=False
    )
    option = forms.ChoiceField(
        choices=OPTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Option"
    )

    error_messages = {
        'invalid_login': _(
            "Veuillez saisir un nom et un mot de passe valides. "
            "Notez que les deux champs peuvent être sensibles à la casse."
        ),
        'inactive': _("Ce compte est inactif."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(request, *args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        option = self.cleaned_data.get('option')

        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
            # Vérifie que l'option correspond
            if option and str(self.user_cache.option) != option:
                raise forms.ValidationError(
                    f"Cet utilisateur n'est pas inscrit pour l'option sélectionnée.",
                    code='invalid_option'
                )
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user(self):
        return self.user_cache

# ----------------------------------------------------
# Formulaires pour l'administration Django
# ----------------------------------------------------
class CustomUserCreationFormAdmin(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmez le mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('phone', 'nom')

    def clean_password2(self):
        pw1 = self.cleaned_data.get('password1')
        pw2 = self.cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return pw2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CustomUserChangeFormAdmin(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label="Mot de passe",
        help_text="Vous pouvez changer le mot de passe avec <a href=\"../password/\">ce formulaire</a>."
    )

    class Meta:
        model = CustomUser
        fields = ('phone', 'nom', 'password', 'is_active', 'is_staff', 'is_super_admin')

    def clean_password(self):
        return self.initial["password"]

# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser

class InscriptionParInvitationForm(UserCreationForm):
    nom = forms.CharField(max_length=150, required=True, label="Nom complet")
    telephone = forms.CharField(max_length=20, required=True, label="Téléphone")

    class Meta:
        model = CustomUser
        fields = ("nom", "telephone", "password1", "password2")
