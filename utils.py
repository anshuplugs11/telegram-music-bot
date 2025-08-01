#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import asyncio
import logging
import yt_dlp
from typing import Optional, Tuple, Dict, Any
from config import Config
import time
import psutil

logger = logging.getLogger(__name__)

async def get_file_from_youtube(query: str) -> Tuple[Optional[str], Optional[str], str, int]:
    """Download audio and video from YouTube"""
    try:
        # Create downloads directory if not exists
        os.makedirs(Config.DOWNLOADS_PATH, exist_ok=True)
        
        # Search and get info
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            search_results = ydl.extract_info(
                f"ytsearch:{query}",
                download=False
            )
            
            if not search_results or not search_results.get('entries'):
                return None, None, "Not Found", 0
            
            video_info = search_results['entries'][0]
            title = sanitize_filename(video_info.get('title', 'Unknown'))
            duration = video_info.get('duration', 0)
            url = video_info.get('webpage_url')
        
        # Download audio
        audio_file = None
        try:
            audio_opts = Config.YTDL_OPTS.copy()
            audio_opts['outtmpl'] = os.path.join(Config.DOWNLOADS_PATH, f"{title}_audio.%(ext)s")
            
            with yt_dlp.YoutubeDL(audio_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded audio file
            for ext in ['.mp3', '.m4a', '.webm', '.ogg']:
                audio_path = os.path.join(Config.DOWNLOADS_PATH, f"{title}_audio{ext}")
                if os.path.exists(audio_path):
                    audio_file = audio_path
                    break
                    
        except Exception as e:
            logger.error(f"Audio download error: {e}")
        
        # Download video
        video_file = None
        try:
            video_opts = Config.YTDL_VIDEO_OPTS.copy()
            video_opts['outtmpl'] = os.path.join(Config.DOWNLOADS_PATH, f"{title}_video.%(ext)s")
            
            with yt_dlp.YoutubeDL(video_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded video file
            for ext in ['.mp4', '.webm', '.mkv']:
                video_path = os.path.join(Config.DOWNLOADS_PATH, f"{title}_video{ext}")
                if os.path.exists(video_path):
                    video_file = video_path
                    break
                    
        except Exception as e:
            logger.error(f"Video download error: {e}")
        
        return audio_file, video_file, title, duration
        
    except Exception as e:
        logger.error(f"YouTube download error: {e}")
        return None, None, "Error", 0

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'[^\w\s-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    
    # Limit length
    if len(filename) > 50:
        filename = filename[:50]
    
    return filename or "unknown"

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds == 0:
        return "Live"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

async def get_youtube_info(url: str) -> Optional[Dict[str, Any]]:
    """Get YouTube video information without downloading"""
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            return {
                'title': info.get('title'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date'),
                'description': info.get('description', '')[:200] + '...' if info.get('description') else '',
                'url': info.get('webpage_url')
            }
    except Exception as e:
        logger.error(f"Error getting YouTube info: {e}")
        return None

def is_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'https?://(?:www\.)?youtu\.be/[\w-]+',
        r'https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'https?://(?:m\.)?youtube\.com/watch\?v=[\w-]+',
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def is_spotify_url(url: str) -> bool:
    """Check if URL is a valid Spotify URL"""
    spotify_patterns = [
        r'https?://open\.spotify\.com/track/[\w]+',
        r'https?://open\.spotify\.com/album/[\w]+',
        r'https?://open\.spotify\.com/playlist/[\w]+',
        r'spotify:track:[\w]+',
        r'spotify:album:[\w]+',
        r'spotify:playlist:[\w]+'
    ]
    
    return any(re.match(pattern, url) for pattern in spotify_patterns)

async def cleanup_downloads():
    """Clean up old downloaded files"""
    try:
        downloads_path = Config.DOWNLOADS_PATH
        if not os.path.exists(downloads_path):
            return
        
        current_time = time.time()
        cleanup_count = 0
        
        for filename in os.listdir(downloads_path):
            file_path = os.path.join(downloads_path, filename)
            
            # Remove files older than 1 hour
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > 3600:  # 1 hour
                    try:
                        os.remove(file_path)
                        cleanup_count += 1
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
        
        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} old files")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_mb': memory.used // 1024 // 1024,
            'memory_total_mb': memory.total // 1024 // 1024,
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used // 1024 // 1024 // 1024,
            'disk_total_gb': disk.total // 1024 // 1024 // 1024,
            'boot_time': boot_time
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Create a progress bar string"""
    if total == 0:
        return "█" * length
    
    filled_length = int(length * current / total)
    bar = "█" * filled_length + "░" * (length - filled_length)
    percentage = round(100 * current / total, 1)
    
    return f"{bar} {percentage}%"

async def validate_audio_file(file_path: str) -> bool:
    """Validate if file is a valid audio file"""
    try:
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in Config.ALLOWED_EXTENSIONS:
            return False
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > Config.MAX_FILE_SIZE:
            return False
        
        # Additional validation can be added here
        # (e.g., using ffmpeg to check if file is actually playable)
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating audio file: {e}")
        return False

def extract_user_id(text: str) -> Optional[int]:
    """Extract user ID from text (username or ID)"""
    try:
        # Remove @ if present
        if text.startswith('@'):
            text = text[1:]
        
        # Try to convert to int (direct user ID)
        if text.isdigit():
            return int(text)
        
        # If it's a username, we can't extract ID without API call
        return None
        
    except Exception:
        return None

def parse_time_duration(duration_str: str) -> Optional[int]:
    """Parse time duration string to seconds"""
    try:
        # Support formats like: 1:30, 90, 1m30s, 1h30m, etc.
        duration_str = duration_str.lower().strip()
        
        # Simple seconds
        if duration_str.isdigit():
            return int(duration_str)
        
        # MM:SS or HH:MM:SS format
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        
        # Parse units like 1h30m20s
        total_seconds = 0
        
        # Hours
        if 'h' in duration_str:
            hours_match = re.search(r'(\d+)h', duration_str)
            if hours_match:
                total_seconds += int(hours_match.group(1)) * 3600
        
        # Minutes
        if 'm' in duration_str:
            minutes_match = re.search(r'(\d+)m', duration_str)
            if minutes_match:
                total_seconds += int(minutes_match.group(1)) * 60
        
        # Seconds
        if 's' in duration_str:
            seconds_match = re.search(r'(\d+)s', duration_str)
            if seconds_match:
                total_seconds += int(seconds_match.group(1))
        
        return total_seconds if total_seconds > 0 else None
        
    except Exception as e:
        logger.error(f"Error parsing duration: {e}")
        return None

def generate_session_string():
    """Generate Pyrogram session string instructions"""
    return """
To generate a session string for the assistant account:

1. Install pyrogram: pip install pyrogram
2. Run this code:

```python
from pyrogram import Client

api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"

with Client("assistant", api_id, api_hash) as app:
    print("Session String:")
    print(app.export_session_string())
```

3. Login with your account when prompted
4. Copy the session string and add it to your environment variables
"""

async def send_long_message(client, chat_id: int, text: str, max_length: int = 4000):
    """Send long message by splitting it into chunks"""
    try:
        if len(text) <= max_length:
            await client.send_message(chat_id, text)
            return
        
        # Split message into chunks
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk + line + '\n') > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Line itself is too long, split it
                    while len(line) > max_length:
                        chunks.append(line[:max_length])
                        line = line[max_length:]
                    current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(1)  # Small delay between messages
            await client.send_message(chat_id, chunk)
            
    except Exception as e:
        logger.error(f"Error sending long message: {e}")

class RateLimiter:
    """Simple rate limiter for commands"""
    
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make request"""
        current_time = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[user_id].append(current_time)
        return True
    
    def get_remaining_time(self, user_id: int) -> int:
        """Get remaining time until next request allowed"""
        if user_id not in self.requests or not self.requests[user_id]:
            return 0
        
        oldest_request = min(self.requests[user_id])
        return max(0, int(self.time_window - (time.time() - oldest_request)))

# Create rate limiters
user_rate_limiter = RateLimiter(Config.USER_RATE_LIMIT, 60)  # per minute
chat_rate_limiter = RateLimiter(Config.CHAT_RATE_LIMIT, 60)  # per minute

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

def create_inline_keyboard_from_dict(buttons_dict: Dict[str, str], columns: int = 2):
    """Create inline keyboard from dictionary"""
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = [InlineKeyboardButton(text, callback_data=data) 
              for text, data in buttons_dict.items()]
    
    # Arrange buttons in rows
    keyboard = []
    for i in range(0, len(buttons), columns):
        row = buttons[i:i + columns]
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

# Cleanup task
async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        try:
            await cleanup_downloads()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # Test functions
    print(format_duration(3661))  # Should print 01:01:01
    print(format_file_size(1536))  # Should print 1.5 KB
    print(parse_time_duration("1h30m15s"))  # Should print 5415
    print(create_progress_bar(7, 10))  # Should print progress bar
