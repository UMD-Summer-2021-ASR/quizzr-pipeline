from typing import Dict, List
import io
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload


class Drive:
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """

    service = None

    def __init__(self) -> None:

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("secrets/token.json"):
            creds = Credentials.from_authorized_user_file("secrets/token.json")
        # If there are no (valid) credentials available, raise an error
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise FileNotFoundError

        self.service = build("drive", "v3", credentials=creds)

    def download_batch(self, files: List[Dict[str, str]], audio_dir: str):
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir, exist_ok=True)
        for file in files:
            file_id = file["_id"]
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print("Download %d%%." % int(status.progress() * 100))
            with open(os.path.join(audio_dir, "{}.wav".format(file_id)), "wb") as f:
                f.write(fh.getbuffer())

