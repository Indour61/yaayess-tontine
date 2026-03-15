from django.db import models


class GeneratedVideo(models.Model):

    LANGUAGE_CHOICES = [
        ("fr", "Français"),
        ("wo", "Wolof"),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la vidéo"
    )

    script = models.TextField(
        verbose_name="Script de la vidéo"
    )

    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="fr",
        verbose_name="Langue"
    )

    video_file = models.FileField(
        upload_to="videos/",
        max_length=500,   # évite les erreurs de chemin trop long
        verbose_name="Fichier vidéo"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )

    tiktok_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Lien TikTok"
    )

    facebook_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Lien Facebook"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Vidéo générée"
        verbose_name_plural = "Vidéos générées"

    def __str__(self):
        return f"{self.title} ({self.language})"
