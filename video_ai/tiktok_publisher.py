import requests

def publish_to_tiktok(video_path, caption):

    url = "https://open.tiktokapis.com/v2/post/publish/"

    files = {
        "video": open(video_path, "rb")
    }

    data = {
        "caption": caption
    }

    headers = {
        "Authorization": "Bearer TIKTOK_TOKEN"
    }

    response = requests.post(url, headers=headers, files=files, data=data)

    return response.json()
