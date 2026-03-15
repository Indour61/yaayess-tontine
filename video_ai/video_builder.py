from moviepy.editor import *

def generate_video(audio_file, subtitles):

    background = VideoFileClip("assets/background.mp4")

    audio = AudioFileClip(audio_file)

    text = TextClip(
        subtitles,
        fontsize=60,
        color="white",
        method="caption",
        size=(720, None)
    )

    text = text.set_position("center").set_duration(audio.duration)

    video = CompositeVideoClip([background, text])

    video = video.set_audio(audio)

    output = "generated_video.mp4"

    video.write_videofile(
        output,
        fps=30,
        codec="libx264"
    )

    return output