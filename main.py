import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import dropbox
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# YouTube API Scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# File paths from environment variables
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER = "/Riddles Shorts"
LOCAL_FOLDER = "./downloads"

def authenticate_youtube():
    """
    Authenticate with YouTube using OAuth2.
    """
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube

def fetch_and_upload_files(dropbox_folder, local_folder, youtube):
    """
    Fetch files from Dropbox in ascending order and upload them to YouTube.
    """
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    entries = dbx.files_list_folder(dropbox_folder).entries

    # Sort files by name in ascending order
    entries.sort(key=lambda x: x.name)

    for file in entries:
        local_path = os.path.join(local_folder, file.name)

        # Download the file to local folder
        with open(local_path, "wb") as f:
            metadata, res = dbx.files_download(path=file.path_lower)
            f.write(res.content)

        # Upload the video to YouTube
        title = os.path.splitext(os.path.basename(file.name))[0]  # Use file name as title
        upload_video(youtube, local_path, title)

        # After uploading, remove the file from local folder to save space
        os.remove(local_path)

def upload_video(youtube, file_path, title, description="Auto-uploaded from Dropbox", category="22", privacy_status="private"):
    """
    Upload a video to YouTube.
    """
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category,
            },
            "status": {
                "privacyStatus": privacy_status,
            },
        },
        media_body=file_path,
    )

    response = request.execute()
    print(f"Uploaded: {title}, Video ID: {response['id']}")

def main():
    """
    Main function to fetch and upload files to YouTube in the desired order.
    """
    os.makedirs(LOCAL_FOLDER, exist_ok=True)

    youtube = authenticate_youtube()

    # Fetch and upload files from Dropbox in ascending order by name
    fetch_and_upload_files(DROPBOX_FOLDER, LOCAL_FOLDER, youtube)

if __name__ == "__main__":
    main()
