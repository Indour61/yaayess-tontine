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
class CustomAuthenticationForm(forms.Form):
    phone = forms.CharField(label="Numéro de téléphone")
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        phone = self.cleaned_data.get('phone')
        password = self.cleaned_data.get('password')

        if phone and password:
            self.user_cache = authenticate(self.request, phone=phone, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Numéro ou mot de passe incorrect.")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
        return self.cleaned_data

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
