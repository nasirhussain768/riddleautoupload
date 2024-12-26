import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

# Scopes for the YouTube API
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Path to your credentials.json file
CLIENT_SECRETS_FILE = "credentials.json"

# Authenticate and build the YouTube service
def authenticate_youtube():
    # Check if the token file exists to skip the authentication step
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    else:
        # If no token exists, run the authentication flow
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # Build the YouTube API client
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
    return youtube

# Function to upload a video
def upload_video(file_path, title, description, category="22", privacy="private"):
    youtube = authenticate_youtube()

    # Call the API to upload the video
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "categoryId": category,
            },
            "status": {
                "privacyStatus": privacy,  # can be 'private', 'public', or 'unlisted'
            },
        },
        media_body=file_path,
    )

    # Execute the upload
    response = request.execute()
    print(f"Video uploaded: {response['id']}")

if __name__ == "__main__":
    # Example upload (you can pass in file paths dynamically)
    upload_video("path_to_your_video.mp4", "Test Video", "This is a test video description")
