from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth import authenticate
from .models import CustomUser

# ----------------------------------------------------
# Formulaire d'inscription pour un utilisateur normal
# ----------------------------------------------------
class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('phone', 'nom')  # ✅ pas de choix_inscription ici

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


# ----------------------------------------------------
# Formulaire de connexion
# ----------------------------------------------------
from django import forms
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulaire d'authentification personnalisé utilisant le nom comme identifiant.
    """
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'Votre nom',
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

    error_messages = {
        'invalid_login': _(
            "Veuillez saisir un nom et un mot de passe valides. "
            "Notez que les deux champs peuvent être sensibles à la casse."
        ),
        'inactive': _("Ce compte est inactif."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        Initialise le formulaire avec la requête optionnelle.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """
        Valide les données du formulaire et authentifie l'utilisateur.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

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
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Vérifie si l'utilisateur est autorisé à se connecter.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user(self):
        """
        Retourne l'utilisateur authentifié.
        """
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
        # Retourne la valeur initiale du mot de passe
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
