from django.shortcuts import render
from .video_agent import VideoLaunchAgent
from .models import GeneratedVideo


def create_video(request):

    if request.method == "POST":

        topic = request.POST.get("topic")

        agent = VideoLaunchAgent()

        script = agent.generate_script(topic)

        voice = agent.generate_voice(script)

        video_path = agent.generate_video(voice)

        video = GeneratedVideo.objects.create(
            title=topic,
            script=script,
            video_file=video_path
        )

        return render(request, "video_ai/result.html", {"video": video})

    return render(request, "video_ai/create_video.html")