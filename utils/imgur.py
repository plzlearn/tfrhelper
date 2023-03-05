import requests
from requests.structures import CaseInsensitiveDict
import os
from dotenv import load_dotenv
load_dotenv()
import json

CLIENT_ID = os.getenv('IMGUR_API_ID')

def upload_image_to_imgur(image_bytes):
    url = "https://api.imgur.com/3/image"

    headers = CaseInsensitiveDict()
    headers["Authorization"] = f"Client-ID {CLIENT_ID}"
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    data = {
        "image": image_bytes
    }

    resp = requests.post(url, headers=headers, data=data)

    if resp.status_code != 200:
        raise Exception(f"Error uploading image to Imgur: {resp.text}")

    response_data = json.loads(resp.text)['data']
    return response_data['link']