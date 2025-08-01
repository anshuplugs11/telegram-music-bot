#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import List

class Config:
    """Bot configuration class"""
    
    # Bot Token from @BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    # Telegram API credentials from https://my.telegram.org
    API_ID = int(os.getenv("API_ID", "YOUR_API_ID"))
    API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")
    
    # Assistant account session string (optional)
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    
    # Owner/Sudo users (comma separated user IDs)
    SUDO_USERS_STR = os.getenv("SUDO_USERS", "YOUR_USER_ID")
    SUDO_USERS: List[int] = [int(x.strip()) for x in SUDO_USERS_STR.split(",") if x.strip().isdigit()]
    
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///music_bot.db")
    
    # YouTube DL configuration
    YTDL_OPTS = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }
    
    YTDL_VIDEO_OPTS = {
        'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }
    
    # Bot settings
    MAINTENANCE_MODE = False
    LOGGING_ENABLED = True
    MAX_QUEUE_SIZE = 100
    DEFAULT_VOLUME = 100
    AUTO_LEAVE_TIME = 600  # 10 minutes
    
    # File paths
    DOWNLOADS_PATH = "downloads"
    LOGS_PATH = "logs"
    
    # Spotify configuration (optional)
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    # Other streaming services (optional)
    SOUNDCLOUD_CLIENT_ID = os.getenv("SOUNDCLOUD_CLIENT_ID", "")
    
    # Performance settings
    MAX_CONCURRENT_DOWNLOADS = 3
    DOWNLOAD_TIMEOUT = 300  # 5 minutes
    
    # Security settings
    ALLOWED_EXTENSIONS = ['.mp3', '.mp4', '.wav', '.flac', '.ogg']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Rate limiting
    USER_RATE_LIMIT = 10  # commands per minute
    CHAT_RATE_LIMIT = 20  # commands per minute
    
    # Heroku/Render specific
    PORT = int(os.getenv("PORT", 8000))
    
    @classmethod
    def validate_config(cls):
        """Validate configuration"""
        required_vars = [
            ("BOT_TOKEN", cls.BOT_TOKEN),
            ("API_ID", cls.API_ID),
            ("API_HASH", cls.API_HASH),
        ]
        
        missing = []
        for var_name, var_value in required_vars:
            if not var_value or str(var_value) in ["YOUR_BOT_TOKEN_HERE", "YOUR_API_ID", "YOUR_API_HASH", "0"]:
                missing.append(var_name)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        if not cls.SUDO_USERS:
            raise ValueError("At least one SUDO_USER must be configured")
        
        # Create necessary directories
        os.makedirs(cls.DOWNLOADS_PATH, exist_ok=True)
        os.makedirs(cls.LOGS_PATH, exist_ok=True)
        
        print("✅ Configuration validated successfully!")
    
    @classmethod
    def get_env_template(cls):
        """Get environment template for deployment"""
        return """
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token_from_botfather
API_ID=your_api_id_from_my_telegram_org
API_HASH=your_api_hash_from_my_telegram_org

# Owner Configuration (Your Telegram User ID)
SUDO_USERS=your_user_id

# Assistant Account (Optional - for better performance)
SESSION_STRING=your_pyrogram_session_string

# Database Configuration
DATABASE_URL=sqlite:///music_bot.db

# Optional: Spotify Integration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Optional: SoundCloud Integration
SOUNDCLOUD_CLIENT_ID=your_soundcloud_client_id

# Deployment
PORT=8000
        """

# Validate configuration on import
if __name__ == "__main__":
    try:
        Config.validate_config()
        print("Configuration is valid!")
        print("\nEnvironment template:")
        print(Config.get_env_template())
    except Exception as e:
        print(f"Configuration error: {e}")
