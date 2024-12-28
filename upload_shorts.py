import os
import json
import dropbox
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import googleapiclient.http

# Get the YouTube credentials JSON from environment variables
YOUTUBE_CREDENTIALS_JSON = os.environ.get('YOUTUBE_CREDENTIALS_JSON')

# Ensure the environment variable is loaded
if not YOUTUBE_CREDENTIALS_JSON:
    raise ValueError("Missing YouTube credentials! Make sure the secret is correctly set.")

# Parse the credentials JSON
credentials_dict = json.loads(YOUTUBE_CREDENTIALS_JSON)

# Setup Dropbox client
DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
if not DROPBOX_ACCESS_TOKEN:
    raise ValueError("Missing Dropbox access token!")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Setup YouTube API client using Service Account
def get_youtube_service():
    credentials = None
    # Use service account credentials
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict, 
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    youtube = build('youtube', 'v3', credentials=credentials)
    return youtube

# Example function to upload a video to YouTube
def upload_video_to_youtube(video_file_path, title, description):
    youtube = get_youtube_service()
    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=title,
                    description=description
                ),
                status=dict(
                    privacyStatus="public"
                )
            ),
            media_body=googleapiclient.http.MediaFileUpload(video_file_path)
        )
        request.execute()
    except HttpError as e:
        print(f"An error occurred: {e}")

# Fetch the next video from Dropbox
def fetch_next_video_from_dropbox():
    result = dbx.files_list_folder('/Riddles Shorts').entries
    video_file = result[0]  # assuming you want to upload the first video
    video_path = '/path/to/video/file'  # Example: Download the video or use its path
    # Download the video if needed (you can customize this part as needed)
    with open(video_path, "wb") as f:
        metadata, res = dbx.files_download(path=video_file.path_lower)
        f.write(res.content)
    return video_path

# Main execution to upload videos
def main():
    video_file_path = fetch_next_video_from_dropbox()
    upload_video_to_youtube(video_file_path, "Riddle Short", "Description of the riddle short.")

if __name__ == '__main__':
    main()
