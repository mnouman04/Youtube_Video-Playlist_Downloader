import streamlit as st
import yt_dlp
import os
import re
from itertools import islice
import pandas as pd
import time

st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        text-align: center;
    }
    .download-progress {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #ff4b4b, #ff9d4b, #ffdb4b) !important;
    }
    .small-text {
        font-size: 0.8rem;
        color: #888888;
    }
    .result-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success {
        background-color: rgba(0, 200, 0, 0.1);
        border-left: 5px solid rgba(0, 200, 0, 0.5);
    }
    .error {
        background-color: rgba(255, 0, 0, 0.1);
        border-left: 5px solid rgba(255, 0, 0, 0.5);
    }
</style>
""", unsafe_allow_html=True)

def sanitize_filename(title):
    """Sanitize filename the way yt-dlp does it"""
    title = re.sub(r'[\\/*?"<>|]', '', title)
    title = title.replace(':', ' -').replace('/', '_')
    title = title.strip('. ')
    return title

def ensure_directories_exist(content_title=None):
    """Create necessary directories if they don't exist"""
    base_dir = st.session_state.get("download_path", "C:/YoutubeScraped")


    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        st.info(f"Created base directory: {base_dir}")

    if content_title:

        safe_title = sanitize_filename(content_title)
        content_dir = os.path.join(base_dir, safe_title)


        if not os.path.exists(content_dir):
            os.makedirs(content_dir)


        subdirs = ['videos', 'thumbnails', 'metadata', 'subtitles']
        for subdir in subdirs:
            full_path = os.path.join(content_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

        return content_dir

    return base_dir

def get_content_info(url):
    """Get information about the YouTube content (video or playlist)"""
    with st.spinner("Fetching content information..."):
        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(url, download=False)
                if 'entries' in result:  
                    playlist_info = {'type': 'playlist', 'entries': result['entries'], 'title': result.get('title', 'Unknown Playlist')}
                    

                    return playlist_info
                else:  
                    return {'type': 'video', 'entries': [result], 'title': result.get('title', 'Unknown Video')}
        except Exception as e:
            st.error(f"Error fetching content: {str(e)}")
            return {'type': 'error', 'entries': [], 'title': 'Error'}
        
        
def download_videos(entries, start, end, options, content_dir, playlist_title=None):
    """Download selected videos with specified options"""
    selected = list(islice(entries, start, end))
    success_count = 0
    failed_count = 0
    failed_videos = []
    total = len(selected)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    download_status = st.empty()
    

    if options['video_quality'] == 'best':
        format_str = 'bestvideo+bestaudio/best'
    elif options['video_quality'] == 'medium':
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    elif options['video_quality'] == 'worst':
        format_str = 'worstvideo+worstaudio/worst'
    else: 
        format_str = 'bestaudio/best'


    video_dir = os.path.join(content_dir, 'videos')
    thumbnail_dir = os.path.join(content_dir, 'thumbnails')
    metadata_dir = os.path.join(content_dir, 'metadata')
    subtitles_dir = os.path.join(content_dir, 'subtitles')


    filename_template = '%(playlist_index)s. %(title)s' if playlist_title and len(selected) > 1 else '%(title)s'

    def progress_hook(d):
        if d['status'] == 'downloading':
            download_status.markdown(f"Downloading: **{os.path.basename(d['filename'])}** - {d.get('_percent_str', '0%')}")
        elif d['status'] == 'finished':
            download_status.markdown(f"✅ Completed: **{os.path.basename(d['filename'])}**")

    ydl_opts = {
        'format': format_str,
        'progress_hooks': [progress_hook],
        'noplaylist': True,  
        'restrictfilenames': True,
        'windowsfilenames': True,
        'outtmpl': {
            'default': os.path.join(video_dir, filename_template + '.%(ext)s'),
            'thumbnail': os.path.join(thumbnail_dir, filename_template + '.%(ext)s'),
            'infojson': os.path.join(metadata_dir, filename_template + '.info.json'),
            'subtitle': os.path.join(subtitles_dir, filename_template + '.%(ext)s'),
        }
    }

    # Set options based on user selections
    if not options['video']:
        ydl_opts['skip_download'] = True

    if options['thumbnail']:
        ydl_opts['writethumbnail'] = True

    if options['metadata']:
        ydl_opts['writeinfojson'] = True

    if options['subtitles']:
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True
        ydl_opts['subtitleslangs'] = ['en']  # Default to English

    for index, entry in enumerate(selected):
        try:
            status_text.markdown(f"Processing {index+1} of {total}: **{entry['title']}**")
            progress_bar.progress((index) / total)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([entry['url'] if 'url' in entry else entry['webpage_url']])
                
            success_count += 1
        except Exception as e:
            st.error(f"Error downloading: {entry['title']}")
            st.error(f"Reason: {str(e)}")
            failed_count += 1
            failed_videos.append(entry['title'])
            time.sleep(1)  
            continue
            
    progress_bar.progress(1.0)
    status_text.markdown("✅ **Download complete!**")
    download_status.empty()

    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'failed_videos': failed_videos
    }


if 'download_path' not in st.session_state:
    st.session_state.download_path = "C:/YoutubeScraped"
if 'video_data' not in st.session_state:
    st.session_state.video_data = None
if 'content_info' not in st.session_state:
    st.session_state.content_info = None
if 'download_results' not in st.session_state:
    st.session_state.download_results = None
if 'selected_videos' not in st.session_state:
    st.session_state.selected_videos = []

with st.sidebar:
    st.image("https://img.icons8.com/color/96/youtube-play.png", width=80)
    st.title("Settings")
    
    st.session_state.download_path = st.text_input("Download Path", value=st.session_state.download_path)
    
    st.subheader("Download Options")
    video_option = st.checkbox("Download Videos", value=True)
    
    video_quality = "best"
    if video_option:
        video_quality = st.radio(
            "Video Quality",
            ["best", "medium", "worst"],
            horizontal=True
        )
    
    thumbnail_option = st.checkbox("Download Thumbnails", value=True)
    metadata_option = st.checkbox("Download Metadata", value=True)
    subtitles_option = st.checkbox("Download Subtitles", value=True)
    
    st.divider()
    
    st.markdown("<p class='small-text'>YouTube Downloader v1.0</p>", unsafe_allow_html=True)

st.markdown("<h1 class='main-title'>🎬 YouTube Downloader</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 URL Input", "🎞️ Select Videos", "📥 Download"])

# Tab 1: Video Selection and Content Fetching
with tab1:
    st.write("Enter a YouTube video or playlist URL to begin.")
    url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        fetch_button = st.button("Fetch Content", type="primary", use_container_width=True)
    
    with col2:
        pass
    
    if fetch_button and url:
        content_info = get_content_info(url)
        st.session_state.content_info = content_info
        
        if content_info['type'] == 'error':
            st.error("Failed to fetch content. Please check the URL and try again.")
        
        elif not content_info['entries']:
            st.warning("No content found at the provided URL.")
        
        else:
            st.session_state.video_data = []
            for idx, entry in enumerate(content_info['entries']):
                if content_info['type'] == 'playlist':
                    duration = entry.get('duration_string', '')
                    if not duration:
                        if isinstance(entry.get('duration'), (int, float)):
                            minutes, seconds = divmod(entry['duration'], 60)
                            hours, minutes = divmod(minutes, 60)
                            if hours > 0:
                                duration = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
                            else:
                                duration = f"{int(minutes)}:{int(seconds):02d}"
                        else:
                            duration = "Unavailable"  
                else:
                    duration = entry.get('duration_string', '')
                    if not duration and 'duration' in entry:
                        minutes, seconds = divmod(entry['duration'], 60)
                        hours, minutes = divmod(minutes, 60)
                        if hours > 0:
                            duration = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
                        else:
                            duration = f"{int(minutes)}:{int(seconds):02d}"
                    elif not duration:
                        duration = "Unknown"
                        
                st.session_state.video_data.append({
                    'index': idx + 1,
                    'title': entry['title'],
                    'duration': duration,
                    'id': entry.get('id', ''),
                    'selected': True  
                })

            st.session_state.selected_videos = [i for i in range(len(content_info['entries']))]
            
            st.success(f"Found content: {content_info['title']}")
            if content_info['type'] == 'playlist':
                st.info(f"This is a playlist with {len(content_info['entries'])} videos.")
            else:
                st.info("This is a single video.")
                
            st.markdown("👉 **Go to the 'Select Videos' tab to continue.**")

# Tab 2: Select Videos
with tab2:
    if st.session_state.video_data:
        st.write("Select the videos you want to download:")
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("Select All", use_container_width=True):
                for video in st.session_state.video_data:
                    video['selected'] = True
                st.session_state.selected_videos = list(range(len(st.session_state.video_data)))
                st.rerun()
        
        with col2:
            if st.button("Deselect All", use_container_width=True):
                for video in st.session_state.video_data:
                    video['selected'] = False
                st.session_state.selected_videos = []
                st.rerun()
        
        df = pd.DataFrame(st.session_state.video_data)
        
        edited_df = st.data_editor(
            df,
            column_config={
                "index": st.column_config.NumberColumn("No.", help="Video number"),
                "title": st.column_config.TextColumn("Title", help="Video title"),
                "duration": st.column_config.TextColumn("Duration", help="Video duration"),
                "id": st.column_config.TextColumn("ID", help="Video ID"),
                "selected": st.column_config.CheckboxColumn("Download", help="Select to download")
            },
            disabled=["index", "title", "duration", "id"],
            hide_index=True,
            use_container_width=True
        )
        
        st.session_state.selected_videos = edited_df[edited_df['selected']].index.tolist()
        
        st.markdown(f"**{len(st.session_state.selected_videos)} videos selected for download**")
        
        if st.session_state.selected_videos:
            st.markdown("👉 **Go to the 'Download' tab to start the download.**")
    else:
        st.info("Enter a URL in the URL Input tab first.")

# Tab 3: Download
with tab3:
    if st.session_state.content_info and st.session_state.selected_videos:
        st.write("Start downloading the selected videos:")
        
        download_options = {
            'video': video_option,
            'video_quality': video_quality,
            'thumbnail': thumbnail_option,
            'metadata': metadata_option,
            'subtitles': subtitles_option
        }
        
        st.write("Download Options:")
        
        cols = st.columns([1, 1, 1, 1])
        with cols[0]:
            st.write(f"📹 Videos: {'✅' if download_options['video'] else '❌'}")
        with cols[1]:
            st.write(f"🖼️ Thumbnails: {'✅' if download_options['thumbnail'] else '❌'}")
        with cols[2]:
            st.write(f"📄 Metadata: {'✅' if download_options['metadata'] else '❌'}")
        with cols[3]:
            st.write(f"💬 Subtitles: {'✅' if download_options['subtitles'] else '❌'}")
        
        if download_options['video']:
            st.write(f"🎥 Quality: **{download_options['video_quality'].upper()}**")
        
        st.write(f"🗂️ Download Path: **{st.session_state.download_path}**")
        
        download_button = st.button("Start Download", type="primary", use_container_width=True)
        
        if download_button:
            content_info = st.session_state.content_info
            content_type = content_info['type']
            entries = content_info['entries']
            title = content_info['title']
            
            selected_entries = [entries[i] for i in st.session_state.selected_videos]
            
            content_dir = ensure_directories_exist(title)
            
            with st.expander("Download Details", expanded=True):
                st.write(f"Content type: **{content_type.capitalize()}**")
                st.write(f"Title: **{title}**")
                st.write(f"Selected videos: **{len(selected_entries)}**")
                st.write(f"Download directory: **{content_dir}**")
                
                download_results = download_videos(
                    selected_entries, 
                    0, 
                    len(selected_entries), 
                    download_options, 
                    content_dir,
                    playlist_title=title if content_type == 'playlist' else None
                )
                
                st.session_state.download_results = download_results
                
                st.subheader("Download Summary")
                st.markdown(f"✅ Successfully downloaded: **{download_results['success_count']}** videos")
                st.markdown(f"❌ Failed to download: **{download_results['failed_count']}** videos")
                
                if download_results['failed_videos']:
                    with st.expander("Failed Videos"):
                        for i, video in enumerate(download_results['failed_videos'], 1):
                            st.write(f"{i}. {video}")
                
                st.success(f"Download completed! Files saved to: **{content_dir}**")
                
                if st.button("📂 Open Download Directory", use_container_width=True):
                    os.startfile(content_dir)
    else:
        if not st.session_state.content_info:
            st.info("Enter a URL in the URL Input tab first.")
        elif not st.session_state.selected_videos:
            st.warning("No videos selected. Please select videos in the 'Select Videos' tab.")

# footer
st.divider()
st.markdown(
    """
    <div style="text-align: center">
        <p class="small-text">Built by Nouman & Gohar | using Streamlit and yt-dlp</p>
    </div>
    """, 
    unsafe_allow_html=True
)