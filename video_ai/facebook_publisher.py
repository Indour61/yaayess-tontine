import requests

def publish_to_facebook(video_path, caption):

    url = f"https://graph-video.facebook.com/v18.0/PAGE_ID/videos"

    files = {
        "source": open(video_path, "rb")
    }

    data = {
        "description": caption,
        "access_token": "FACEBOOK_TOKEN"
    }

    response = requests.post(url, files=files, data=data)

    return response.json()
