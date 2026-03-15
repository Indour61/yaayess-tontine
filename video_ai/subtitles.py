import whisper

model = whisper.load_model("base")

def generate_subtitles(audio_path):

    result = model.transcribe(audio_path)

    return result["text"]
