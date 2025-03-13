import streamlit as st
import yt_dlp
import os
import time
from itertools import islice
import json

# Configure the page settings
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme configuration
def set_theme():
    # Set theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'

    # Apply theme CSS
    theme_css = f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            background-color: {st.session_state.background_color};
            color: {st.session_state.text_color};
        }}
        
        .stButton>button {{
            background-color: {st.session_state.primary_color};
            color: {st.session_state.button_text_color};
            border: 1px solid {st.session_state.border_color};
        }}
        
        .stTextInput>div>div>input {{
            background-color: {st.session_state.secondary_background};
            color: {st.session_state.text_color};
            border: 1px solid {st.session_state.border_color};
        }}
        
        .stTable {{
            background-color: {st.session_state.secondary_background};
            color: {st.session_state.text_color};
        }}
        
        .stProgress>div>div>div {{
            background-color: {st.session_state.primary_color};
        }}
        
        .sidebar .sidebar-content {{
            background-color: {st.session_state.secondary_background};
        }}
        
        [data-testid="stHeader"] {{
            background-color: {st.session_state.secondary_background};
        }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

# Initialize theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

# Set color variables based on theme
def set_theme_colors():
    if st.session_state.theme == 'dark':
        st.session_state.background_color = "#1a1a1a"
        st.session_state.text_color = "#ffffff"
        st.session_state.primary_color = "#4a4a4a"
        st.session_state.secondary_background = "#2d2d2d"
        st.session_state.button_text_color = "#ffffff"
        st.session_state.border_color = "#595959"
    else:
        st.session_state.background_color = "#ffffff"
        st.session_state.text_color = "#ff5733"
        st.session_state.primary_color = "#f0f2f6"
        st.session_state.secondary_background = "#f8f9fa"
        st.session_state.button_text_color = "#000000"
        st.session_state.border_color = "#ced4da"

# Toggle theme function
def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
    set_theme_colors()
    set_theme()

# Initial theme setup
set_theme_colors()
set_theme()

# Initialize session state variables
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(message):
    """Add log message to the session state"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {message}")
    
def display_logs():
    """Display all logs in the UI"""
    log_container = st.container()
    with log_container:
        for log in st.session_state.logs:
            st.text(log)

def get_video_info(url):
    """Get info for either a single video or a playlist"""
    add_log(f"Fetching information for: {url}")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist or a single video
            if 'entries' in info:
                add_log(f"Found playlist: {info.get('title', 'Untitled Playlist')}")
                add_log(f"Total videos in playlist: {len(info['entries'])}")
                return {'type': 'playlist', 'info': info}
            else:
                add_log(f"Found single video: {info.get('title', 'Untitled Video')}")
                return {'type': 'video', 'info': info}
        except Exception as e:
            add_log(f"Error: {str(e)}")
            return {'type': 'error', 'error': str(e)}

def download_single_video(video_info, include_thumbnail, include_metadata, include_subtitles):
    """Download a single video"""
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'writethumbnail': include_thumbnail,
        'writeinfojson': include_metadata,
        'writesubtitles': include_subtitles,
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%', '')
            try:
                progress_bar.progress(float(p) / 100)
                status_text.text(f"Downloading: {d.get('_percent_str', '0%')} complete")
            except:
                pass
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)
            status_text.text(f"Download complete! Processing file...")
            add_log(f"Finished downloading: {d.get('filename', 'file')}")
    
    ydl_opts['progress_hooks'] = [progress_hook]
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            add_log(f"Starting download of: {video_info.get('title', 'Unknown video')}")
            ydl.download([video_info['webpage_url']])
            add_log("Download completed successfully")
            return True
        except Exception as e:
            add_log(f"Error during download: {str(e)}")
            return False

def download_playlist(playlist_info, start_idx, end_idx, include_thumbnail, include_metadata, include_subtitles):
    """Download videos from a playlist"""
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    entries = playlist_info['entries']
    selected_entries = list(islice(entries, start_idx-1, end_idx))
    total_videos = len(selected_entries)
    
    success_count = 0
    failed_count = 0
    failed_videos = []
    
    overall_progress = st.progress(0)
    video_progress = st.progress(0)
    overall_status = st.empty()
    video_status = st.empty()
    
    for idx, entry in enumerate(selected_entries):
        overall_progress.progress(idx / total_videos)
        overall_status.text(f"Overall Progress: {idx}/{total_videos} videos")
        
        video_title = entry.get('title', f"Video {idx+1}")
        add_log(f"Processing video {idx+1}/{total_videos}: {video_title}")
        
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'downloads/{idx+1}. %(title)s.%(ext)s',
            'writethumbnail': include_thumbnail,
            'writeinfojson': include_metadata,
            'writesubtitles': include_subtitles,
        }
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%', '')
                try:
                    video_progress.progress(float(p) / 100)
                    video_status.text(f"Video {idx+1}: {p}% complete")
                except:
                    pass
            elif d['status'] == 'finished':
                video_progress.progress(1.0)
                video_status.text(f"Video {idx+1}: Download complete!")
        
        ydl_opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([entry['url']])
                success_count += 1
                add_log(f"Successfully downloaded: {video_title}")
            except Exception as e:
                failed_count += 1
                failed_videos.append(video_title)
                add_log(f"Failed to download {video_title}: {str(e)}")
        
        # Reset video progress for next video
        video_progress.progress(0)
    
    # Final update for overall progress
    overall_progress.progress(1.0)
    overall_status.text(f"Download Complete: {success_count} succeeded, {failed_count} failed")
    
    # Report summary
    add_log(f"Download Summary: {success_count} succeeded, {failed_count} failed")
    
    if failed_videos:
        add_log("The following videos could not be downloaded:")
        for i, video in enumerate(failed_videos, 1):
            add_log(f"{i}. {video}")
    
    return success_count, failed_count, failed_videos

# UI Layout
st.sidebar.title('Settings')
st.sidebar.button('Toggle Theme 🌓', on_click=toggle_theme)

# Main content
st.title('YouTube Video Downloader')
st.write('Download videos or playlists from YouTube')

# URL input
url = st.text_input('Enter YouTube URL (video or playlist):', placeholder='https://www.youtube.com/watch?v=...')

# Download options
st.subheader('Download Options')
col1, col2, col3 = st.columns(3)
include_thumbnail = col1.checkbox('Download thumbnail', value=True)
include_metadata = col2.checkbox('Include metadata', value=True)
include_subtitles = col3.checkbox('Download subtitles', value=True)

# Fetch info button
if st.button('Fetch Info'):
    if url:
        with st.spinner('Fetching video information...'):
            result = get_video_info(url)
            st.session_state.url_result = result
    else:
        st.error('Please enter a valid URL')

# Display results and download options
if 'url_result' in st.session_state:
    result = st.session_state.url_result
    
    if result['type'] == 'error':
        st.error(f"Error: {result['error']}")
    
    elif result['type'] == 'video':
        st.subheader('Video Information')
        video_info = result['info']
        
        # Display video details
        st.write(f"*Title:* {video_info.get('title', 'Unknown')}")
        st.write(f"*Duration:* {video_info.get('duration_string', 'Unknown')}")
        st.write(f"*Channel:* {video_info.get('uploader', 'Unknown')}")
        
        if st.button('Download Video'):
            with st.spinner('Downloading video...'):
                success = download_single_video(
                    video_info, 
                    include_thumbnail, 
                    include_metadata, 
                    include_subtitles
                )
                if success:
                    st.success('Video downloaded successfully!')
                else:
                    st.error('Failed to download video.')
    
    elif result['type'] == 'playlist':
        st.subheader('Playlist Information')
        playlist_info = result['info']
        entries = playlist_info.get('entries', [])
        
        # Display playlist details
        st.write(f"*Playlist Title:* {playlist_info.get('title', 'Unknown')}")
        st.write(f"*Total Videos:* {len(entries)}")
        
        # Create a table to display videos
        st.subheader('Videos in Playlist')
        
        # Display videos in a data table
        video_data = []
        for i, entry in enumerate(entries, 1):
            video_data.append({
                "No.": i,
                "Title": entry.get('title', f'Video {i}'),
                "Duration": entry.get('duration_string', 'Unknown')
            })
        
        st.table(video_data)
        
        # Video range selection
        col1, col2 = st.columns(2)
        start_idx = col1.number_input('Start from video #', min_value=1, max_value=len(entries), value=1)
        end_idx = col2.number_input('End at video #', min_value=start_idx, max_value=len(entries), value=min(5, len(entries)))
        
        if st.button('Download Selected Videos'):
            with st.spinner(f'Downloading videos {start_idx} to {end_idx}...'):
                success_count, failed_count, failed_videos = download_playlist(
                    playlist_info, 
                    start_idx, 
                    end_idx, 
                    include_thumbnail, 
                    include_metadata, 
                    include_subtitles
                )
            
                if failed_count == 0:
                    st.success(f'All {success_count} videos downloaded successfully!')
                else:
                    st.warning(f'{success_count} videos downloaded successfully. {failed_count} videos failed.')

# Display logs section
st.subheader('Logs')
logs_placeholder = st.empty()

# Display logs inside a container with scrolling
with logs_placeholder.container():
    display_logs()