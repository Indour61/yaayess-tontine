import os
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from django.conf import settings


class VideoLaunchAgent:

    def generate_script(self, topic):

        script = f"""
        Découvrez {topic}.
        La plateforme qui digitalise les tontines africaines.

        Créez votre groupe.
        Ajoutez des membres.
        Payez les cotisations facilement.

        {topic} simplifie la gestion des tontines.
        """

        return script


    def generate_voice(self, script):

        voice_path = os.path.join(settings.MEDIA_ROOT, "voice.mp3")

        tts = gTTS(script, lang="fr")
        tts.save(voice_path)

        return voice_path


    def generate_video(self, voice_path):
        import os
        from django.conf import settings

        img1 = os.path.join(settings.BASE_DIR, "video_ai/static/images/smartphone.png")
        img2 = os.path.join(settings.BASE_DIR, "video_ai/static/images/fintech.png")
        img3 = os.path.join(settings.BASE_DIR, "video_ai/static/images/communaute.png")

        clip1 = ImageClip(img1).set_duration(4)
        clip2 = ImageClip(img2).set_duration(4)
        clip3 = ImageClip(img3).set_duration(4)

        video = concatenate_videoclips([clip1, clip2, clip3])

        audio = AudioFileClip(voice_path)

        video = video.set_audio(audio)

        output = os.path.join(settings.MEDIA_ROOT, "videos", "yaayess_video.mp4")

        video.write_videofile(output, fps=24)

        return output