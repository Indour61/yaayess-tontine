from django import forms
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField,
    AuthenticationForm,
    UserCreationForm
)
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from .models import CustomUser


# ----------------------------------------------------
# Choix d'inscription
# ----------------------------------------------------

OPTION_CHOICES = (
    ("1", "Cotisation & Tontine"),
    ("2", "Épargne & Crédit"),
)


# ----------------------------------------------------
# Formulaire d'inscription utilisateur
# ----------------------------------------------------

class CustomUserCreationForm(forms.ModelForm):

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    option = forms.ChoiceField(
        label="Type de compte",
        choices=OPTION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    pays = forms.ChoiceField(
        label="Pays",
        choices=CountryField().choices,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = CustomUser
        fields = (
            "nom",
            "phone",
            "email",
            "pays",
            "ville",
            "option",
        )

        widgets = {
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "77 123 45 67"
            }),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "ville": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_password2(self):

        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                "Les mots de passe ne correspondent pas."
            )

        return password2

    def save(self, commit=True):

        user = super().save(commit=False)

        user.set_password(self.cleaned_data["password1"])
        user.option = self.cleaned_data["option"]

        if commit:
            user.save()

        return user


# ----------------------------------------------------
# Formulaire de connexion
# ----------------------------------------------------

class CustomAuthenticationForm(AuthenticationForm):

    username = forms.CharField(
        label=_("Téléphone"),
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "77 123 45 67",
            "autofocus": True
        })
    )

    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Votre mot de passe"
        }),
        strip=False
    )

    option = forms.ChoiceField(
        label="Type de compte",
        choices=OPTION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def clean(self):

        phone = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        option = self.cleaned_data.get("option")

        if phone and password:

            self.user_cache = authenticate(
                self.request,
                username=phone,
                password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError(
                    "Téléphone ou mot de passe incorrect."
                )

            if option and str(self.user_cache.option) != option:
                raise forms.ValidationError(
                    "Ce compte n'est pas inscrit pour cette option."
                )

        return self.cleaned_data

    def get_user(self):
        return getattr(self, "user_cache", None)


# ----------------------------------------------------
# Formulaire création utilisateur ADMIN
# ----------------------------------------------------

class CustomUserCreationFormAdmin(forms.ModelForm):

    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput
    )

    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput
    )

    class Meta:
        model = CustomUser
        fields = ("phone", "nom")

    def clean_password2(self):

        pw1 = self.cleaned_data.get("password1")
        pw2 = self.cleaned_data.get("password2")

        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError(
                "Les mots de passe ne correspondent pas."
            )

        return pw2

    def save(self, commit=True):

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


# ----------------------------------------------------
# Formulaire modification utilisateur ADMIN
# ----------------------------------------------------

class CustomUserChangeFormAdmin(forms.ModelForm):

    password = ReadOnlyPasswordHashField(
        label="Mot de passe",
        help_text="Utilisez le formulaire de changement de mot de passe."
    )

    class Meta:
        model = CustomUser
        fields = (
            "phone",
            "nom",
            "password",
            "is_active",
            "is_staff",
            "is_super_admin",
        )

    def clean_password(self):
        return self.initial["password"]


# ----------------------------------------------------
# Inscription par invitation
# ----------------------------------------------------

class InscriptionParInvitationForm(UserCreationForm):

    nom = forms.CharField(
        max_length=150,
        required=True,
        label="Nom complet",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    phone = forms.CharField(
        max_length=20,
        required=True,
        label="Téléphone",
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = CustomUser
        fields = (
            "nom",
            "phone",
            "password1",
            "password2",
        )

