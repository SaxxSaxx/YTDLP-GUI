# 🎥 YouTube Downloader GUI (yt-dlp)

A powerful and modern YouTube Downloader with GUI built using Python and `yt-dlp`.

## 🚀 Features

- Paste YouTube URL(s) and fetch video info
- Download video/audio in multiple formats
- Show video thumbnail, title, duration, uploader, views
- Supports subtitles, playlists, and audio-only mode
- Drag-and-drop folder selection
- Dark mode and light mode toggle
- Maintains download history
- Uses `yt-dlp` under the hood

## 🛠 Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Install `yt-dlp` separately (globally or locally):

```bash
pip install yt-dlp
# or
brew install yt-dlp  # macOS
sudo apt install yt-dlp  # Linux
```

## 🧪 Running the App

```bash
python youtube_downloader_gui.py
```

## 📁 Project Structure

```
.
├── youtube_downloader_gui.py
├── README.md
├── requirements.txt
└── [downloads go to selected directory]
```

## 🧠 Notes

- All downloads are handled using `yt-dlp` subprocess
- Video info is extracted using `--dump-json`
- History is stored in memory (not persisted yet)

## 🙌 Credits

Built with ❤️ by [@saxx](https://github.com/saxxsaxx)
