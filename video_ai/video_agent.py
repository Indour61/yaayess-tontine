import os
import uuid
import logging

from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from django.conf import settings


logger = logging.getLogger(__name__)


class VideoLaunchAgent:
    """
    Agent de génération de vidéos marketing pour YaayESS.
    Pipeline :
    Script → Voix → Vidéo
    """

    # ----------------------------
    # SCRIPT
    # ----------------------------

    def generate_script(self, topic: str) -> str:
        """
        Génère un script marketing simple.
        """

        topic = topic.strip()

        script = f"""
Découvrez {topic}.

La plateforme qui digitalise les tontines africaines.

Créez votre groupe facilement.
Invitez vos membres en quelques secondes.
Payez vos cotisations rapidement et en toute sécurité.

Avec {topic}, la gestion des tontines devient simple,
moderne et accessible à tous.

Rejoignez {topic} dès aujourd'hui.
        """

        return script.strip()

    # ----------------------------
    # VOIX
    # ----------------------------

    def generate_voice(self, script: str) -> str:
        """
        Génère un fichier audio à partir du script.
        """

        try:
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            filename = f"voice_{uuid.uuid4().hex}.mp3"
            voice_path = os.path.join(settings.MEDIA_ROOT, filename)

            tts = gTTS(script, lang="fr")
            tts.save(voice_path)

            return voice_path

        except Exception as e:
            logger.error(f"Erreur génération voix : {e}")
            raise

    # ----------------------------
    # VIDEO
    # ----------------------------

    def generate_video(self, voice_path):

        from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
        import os
        import uuid
        from django.conf import settings

        videos_dir = os.path.join(settings.MEDIA_ROOT, "videos")
        os.makedirs(videos_dir, exist_ok=True)

        audio = AudioFileClip(voice_path)

        duration = audio.duration / 3

        images = [
            os.path.join(settings.BASE_DIR, "video_ai/static/images/smartphone.png"),
            os.path.join(settings.BASE_DIR, "video_ai/static/images/fintech.png"),
            os.path.join(settings.BASE_DIR, "video_ai/static/images/communaute.png"),
        ]

        clips = []

        for img in images:
            clip = (
                ImageClip(img)
                .resize((1080, 1920))  # format vertical propre
                .set_duration(duration)
            )

            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        video = video.set_audio(audio)

        filename = f"video_{uuid.uuid4().hex}.mp4"

        output = os.path.join(videos_dir, filename)

        video.write_videofile(
            output,
            fps=30,
            codec="libx264",
            audio_codec="aac"
        )

        return output



