import dropbox
import os
from datetime import datetime

# Dropbox API setup (Make sure you have a valid Dropbox token in your GitHub secrets)
def fetch_latest_file(dropbox_folder, local_folder):
    # Dropbox access token (from GitHub Secrets)
    access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
    dbx = dropbox.Dropbox(access_token)

    # List files in the Dropbox folder
    entries = dbx.files_list_folder(dropbox_folder).entries
    if not entries:
        return None

    # Get the most recently added file (can be modified to get other files based on your needs)
    latest_file = max(entries, key=lambda x: x.client_modified if hasattr(x, 'client_modified') else datetime.min)
    video_filename = latest_file.name  # Filename to be used as title
    local_video_path = os.path.join(local_folder, video_filename)

    # Download the file to the local folder
    with open(local_video_path, "wb") as f:
        metadata, res = dbx.files_download(path=latest_file.path_lower)
        f.write(res.content)

    return local_video_path, video_filename
