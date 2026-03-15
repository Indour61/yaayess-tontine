import requests

def generate_voice(text, language="fr"):

    if language == "wo":
        voice = "af_sarah"
    else:
        voice = "alloy"

    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": "Bearer YOUR_KEY"
        },
        json={
            "model": "gpt-4o-mini-tts",
            "voice": voice,
            "input": text
        }
    )

    with open("voice.mp3", "wb") as f:
        f.write(response.content)

    return "voice.mp3"