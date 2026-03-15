import os
import logging
import traceback

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .video_agent import VideoLaunchAgent
from .models import GeneratedVideo


logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def create_video(request):
    """
    Génère une vidéo marketing.
    L'utilisateur peut fournir un script ou laisser l'IA le générer.
    """

    if request.method == "POST":

        topic = request.POST.get("topic", "").strip()
        script = request.POST.get("script", "").strip()

        # Validation
        if not topic:
            messages.error(request, "Veuillez saisir un sujet pour la vidéo.")
            return redirect("create_video")

        try:

            logger.info(f"Génération vidéo demandée pour : {topic}")

            agent = VideoLaunchAgent()

            # Génération du script si non fourni
            if not script:
                logger.info("Aucun script fourni, génération automatique...")
                script = agent.generate_script(topic)

            # Génération de la voix
            logger.info("Génération de la voix...")
            voice_path = agent.generate_voice(script)

            # Génération de la vidéo
            logger.info("Génération de la vidéo...")
            video_path = agent.generate_video(voice_path)

            # Convertir chemin absolu -> chemin relatif pour FileField
            relative_video_path = os.path.relpath(video_path, settings.MEDIA_ROOT)

            # Sauvegarde en base
            video = GeneratedVideo.objects.create(
                title=topic,
                script=script,
                video_file=relative_video_path
            )

            logger.info(f"Vidéo générée avec succès : {relative_video_path}")

            messages.success(request, "🎬 Vidéo générée avec succès.")

            return render(
                request,
                "video_ai/result.html",
                {"video": video}
            )

        except Exception as e:

            logger.error("Erreur lors de la génération vidéo")
            logger.error(traceback.format_exc())

            messages.error(
                request,
                "Une erreur est survenue lors de la génération de la vidéo."
            )

            return redirect("create_video")

    return render(request, "video_ai/create_video.html")
