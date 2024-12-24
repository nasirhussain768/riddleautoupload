// This script automates the upload of YouTube Shorts from a Dropbox folder using GitHub Actions.
// Prerequisites:
// 1. Set up API access for YouTube and Dropbox.
// 2. Store API keys and tokens in GitHub Secrets.

const { google } = require('googleapis');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Dropbox API configuration
const DROPBOX_TOKEN = process.env.DROPBOX_TOKEN;
const DROPBOX_FOLDER = '/Riddles Shorts';
const LOCAL_FOLDER = 'downloads';

// YouTube API configuration
const YOUTUBE_CLIENT_ID = process.env.YOUTUBE_CLIENT_ID;
const YOUTUBE_CLIENT_SECRET = process.env.YOUTUBE_CLIENT_SECRET;
const YOUTUBE_REFRESH_TOKEN = process.env.YOUTUBE_REFRESH_TOKEN;

// Initialize YouTube API client
const oauth2Client = new google.auth.OAuth2(
  YOUTUBE_CLIENT_ID,
  YOUTUBE_CLIENT_SECRET,
  'https://developers.google.com/oauthplayground'
);
oauth2Client.setCredentials({ refresh_token: YOUTUBE_REFRESH_TOKEN });
const youtube = google.youtube({ version: 'v3', auth: oauth2Client });

async function downloadFile(filePath, destination) {
  const url = `https://content.dropboxapi.com/2/files/download`;
  const headers = {
    'Authorization': `Bearer ${DROPBOX_TOKEN}`,
    'Dropbox-API-Arg': JSON.stringify({ path: filePath }),
  };

  const response = await axios.post(url, null, { headers, responseType: 'stream' });
  const writer = fs.createWriteStream(destination);

  return new Promise((resolve, reject) => {
    response.data.pipe(writer);
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
}

async function getDropboxFiles() {
  const url = 'https://api.dropboxapi.com/2/files/list_folder';
  const headers = {
    'Authorization': `Bearer ${DROPBOX_TOKEN}`,
    'Content-Type': 'application/json',
  };

  const data = { path: DROPBOX_FOLDER };
  const response = await axios.post(url, data, { headers });
  return response.data.entries;
}

async function uploadToYouTube(filePath, title, description) {
  const fileSize = fs.statSync(filePath).size;
  const fileStream = fs.createReadStream(filePath);

  const res = await youtube.videos.insert({
    part: 'snippet,status',
    requestBody: {
      snippet: {
        title,
        description,
        tags: ['shorts'],
        categoryId: '22', // Category for People & Blogs
      },
      status: {
        privacyStatus: 'public',
      },
    },
    media: {
      body: fileStream,
    },
  }, {
    onUploadProgress: (evt) => {
      const progress = (evt.bytesRead / fileSize) * 100;
      console.log(`Upload progress: ${Math.round(progress)}%`);
    },
  });

  console.log('Video uploaded:', res.data);
}

(async function main() {
  try {
    const files = await getDropboxFiles();
    if (!files.length) {
      console.log('No files found in Dropbox folder.');
      return;
    }

    const file = files[0];
    const localPath = path.join(LOCAL_FOLDER, file.name);

    console.log(`Downloading file: ${file.name}`);
    await downloadFile(file.path_lower, localPath);

    console.log('Uploading to YouTube...');
    const title = path.basename(file.name, path.extname(file.name));
    const description = `Automated upload from Dropbox: ${file.name}`;

    await uploadToYouTube(localPath, title, description);

    console.log('Deleting local file...');
    fs.unlinkSync(localPath);

  } catch (error) {
    console.error('Error:', error);
  }
})();
