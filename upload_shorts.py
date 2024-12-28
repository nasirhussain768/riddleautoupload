import os
import json
import dropbox
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

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

# Setup YouTube API client
def get_youtube_service():
    credentials = None
    # You can use the pickle method to cache credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                credentials_dict, ['https://www.googleapis.com/auth/youtube.upload']
            )
            credentials = flow.run_local_server(port=0)
        # Save credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
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
    video_path = '/tmp/video.mp4'  # Use a valid path like /tmp/video.mp4 for temporary storage

    # Download the video
    with open(video_path, "wb") as f:
        metadata, res = dbx.files_download(path=video_file.path_lower)
        f.write(res.content)
        
    return video_path

# Main execution to upload videos
def main():
    video_file_path = fetch_next_video_from_dropbox()  # Fetch the next video
    upload_video_to_youtube(video_file_path, "Riddle Short", "Description of the riddle short.")

if __name__ == '__main__':
    main()
