import os
import json
import time
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import dropbox

# Load environment variables
load_dotenv()

# Load credentials from .env
youtube_credentials_json = os.getenv("YOUTUBE_CREDENTIALS_JSON")

credentials_dict = json.loads(YOUTUBE_CREDENTIALS_JSON)

dropbox_access_token = os.getenv("DROPBOX_ACCESS_TOKEN")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

if not youtube_credentials_json or not dropbox_access_token:
    raise ValueError("Missing YouTube or Dropbox credentials in .env file.")

# Parse YouTube credentials
youtube_credentials = json.loads(youtube_credentials_json)

# Set YouTube API scope
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Dropbox folder to fetch videos from
DROPBOX_FOLDER = "/Riddles Shorts"

# Local storage for tracking uploaded files
UPLOADED_TRACKER_FILE = "uploaded_files.txt"

def authenticate_youtube():
    """Authenticate with YouTube API and return a service object."""
    flow = InstalledAppFlow.from_client_config(youtube_credentials, SCOPES)
    credentials = flow.run_local_server(port=0)
    youtube = build("youtube", "v3", credentials=credentials)
    return youtube

def fetch_next_video(dbx, folder):
    """Fetch the next video file from Dropbox."""
    files = dbx.files_list_folder(folder).entries
    files = [f for f in files if isinstance(f, dropbox.files.FileMetadata)]
    files.sort(key=lambda x: x.server_modified)

    # Load uploaded tracker
    if os.path.exists(UPLOADED_TRACKER_FILE):
        with open(UPLOADED_TRACKER_FILE, "r") as f:
            uploaded_files = f.read().splitlines()
    else:
        uploaded_files = []

    for file in files:
        if file.name not in uploaded_files:
            return file

    return None

def download_video(dbx, file, local_path="temp_video.mp4"):
    """Download a video file from Dropbox."""
    with open(local_path, "wb") as f:
        metadata, res = dbx.files_download(path=file.path_lower)
        f.write(res.content)
    return local_path

def upload_to_youtube(youtube, video_path, title, description=""):
    """Upload a video to YouTube."""
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["riddles", "shorts", "fun"],
                    "categoryId": "22"  # Category for "People & Blogs"
                },
                "status": {
                    "privacyStatus": "public"
                }
            },
            media_body=video_path
        )
        response = request.execute()
        print(f"Uploaded: {title} (Video ID: {response['id']})")
    except HttpError as e:
        print(f"An error occurred: {e}")

def mark_as_uploaded(file_name):
    """Mark a file as uploaded in the tracker."""
    with open(UPLOADED_TRACKER_FILE, "a") as f:
        f.write(file_name + "\n")

def main():
    """Main function to run the workflow."""
    # Authenticate YouTube
    youtube = authenticate_youtube()

    # Connect to Dropbox
    dbx = dropbox.Dropbox(dropbox_access_token)

    # Loop to upload videos every 12 hours
    while True:
        print("Fetching next video...")
        next_video = fetch_next_video(dbx, DROPBOX_FOLDER)
        
        if not next_video:
            print("No new videos to upload.")
            break

        print(f"Downloading video: {next_video.name}")
        video_path = download_video(dbx, next_video)
        
        print(f"Uploading to YouTube: {next_video.name}")
        upload_to_youtube(youtube, video_path, title=next_video.name)

        print(f"Marking {next_video.name} as uploaded.")
        mark_as_uploaded(next_video.name)

        # Clean up local file
        os.remove(video_path)

        # Wait for 12 hours
        print("Waiting for 12 hours before the next upload...")
        time.sleep(12 * 3600)

if __name__ == "__main__":
    main()
