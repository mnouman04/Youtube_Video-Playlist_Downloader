# 🎬 YouTube Video & Playlist Downloader

A powerful and user-friendly YouTube downloader with a sleek Streamlit interface.

![GitHub](https://img.shields.io/github/license/mnouman04/Youtube_Video-Playlist_Downloader)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## 🔍 About

Tired of complicated YouTube downloaders filled with ads? This open-source YouTube Video & Playlist Downloader provides a clean, intuitive interface to download videos or entire playlists with customizable options - all powered by Streamlit and yt-dlp.

## ✨ Features

- **Flexible Downloads** - Download single videos or complete playlists
- **Selective Playlist Downloads** - Choose which videos to download from a playlist
- **Quality Options** - Select your preferred video quality (best, medium, worst)
- **Additional Content** - Option to download thumbnails, metadata, and subtitles
- **Custom Location** - Specify where your downloads are saved
- **Progress Tracking** - Real-time download progress indicators
- **Clean Interface** - Intuitive Streamlit UI for easy navigation

## 🔧 Requirements

- Python 3.13 or higher
- Streamlit
- yt-dlp
- pandas
- Poetry (recommended for dependency management)

## 📥 Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone https://github.com/mnouman04/Youtube_Video-Playlist_Downloader.git
cd Youtube_Video-Playlist_Downloader

# Install dependencies using Poetry
poetry install

# Run the application
poetry run streamlit run main.py
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/mnouman04/Youtube_Video-Playlist_Downloader.git
cd Youtube_Video-Playlist_Downloader

# Create and activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run main.py
```

## 🚀 Usage

1. Start the application using the instructions above
2. Access the interface at http://localhost:8501 in your web browser
3. Enter a YouTube video URL or playlist URL
4. Configure your download preferences:
   - Video quality
   - Download location
   - Additional content options
5. Click "Download" and wait for the process to complete

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

Made by [mnouman04](https://github.com/mnouman04) and [gellahi](https://github.com/gellahi)