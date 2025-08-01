#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Music Bot - Main Entry Point
Author: Your Name
Version: 2.0.0
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

# Import bot modules
from bot import TelegramMusicBot
from config import Config
from database import init_database
from keep_alive import start_keep_alive, uptime_monitor
from utils import periodic_cleanup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        logger.info("🔧 Validating configuration...")
        Config.validate_config()
        
        # Initialize database
        logger.info("🗄️ Initializing database...")
        await init_database()
        
        # Create bot instance
        logger.info("🤖 Creating bot instance...")
        bot = TelegramMusicBot()
        
        # Start keep alive server
        logger.info("🌐 Starting keep alive server...")
        start_keep_alive(bot, bot.db)
        
        # Start background tasks
        logger.info("🔄 Starting background tasks...")
        cleanup_task = asyncio.create_task(periodic_cleanup())
        monitor_task = asyncio.create_task(uptime_monitor())
        
        # Start the bot
        logger.info("🚀 Starting Telegram Music Bot...")
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        try:
            cleanup_task.cancel()
            monitor_task.cancel()
        except:
            pass

def run_bot():
    """Run the bot with proper event loop handling"""
    try:
        # Set up event loop policy for Windows
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run the bot
        asyncio.run(main())
        
    except Exception as e:
        logger.error(f"Failed to run bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("""
    
🎵 ═══════════════════════════════════════════════════════ 🎵
   ████████╗███████╗██╗     ███████╗ ██████╗ ██████╗  █████╗ ███╗   ███╗
   ╚══██╔══╝██╔════╝██║     ██╔════╝██╔════╝ ██╔══██╗██╔══██╗████╗ ████║  
      ██║   █████╗  ██║     █████╗  ██║  ███╗██████╔╝███████║██╔████╔██║
      ██║   ██╔══╝  ██║     ██╔══╝  ██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║
      ██║   ███████╗███████╗███████╗╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║
      ╚═╝   ╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝
                                                                           
                        🎵 MUSIC BOT v2.0.0 🎵
    
🎵 ═══════════════════════════════════════════════════════ 🎵

    """)
    
    # Show configuration info
    print("📋 Configuration:")
    print(f"   • Bot Token: {'✅ Set' if Config.BOT_TOKEN and Config.BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else '❌ Not Set'}")
    print(f"   • API ID: {'✅ Set' if Config.API_ID != 0 else '❌ Not Set'}")
    print(f"   • API Hash: {'✅ Set' if Config.API_HASH != 'YOUR_API_HASH' else '❌ Not Set'}")
    print(f"   • Sudo Users: {len(Config.SUDO_USERS)} user(s)")
    print(f"   • Assistant: {'✅ Enabled' if Config.SESSION_STRING else '❌ Disabled'}")
    print(f"   • Database: {Config.DATABASE_URL}")
    print()
    
    # Start the bot
    run_bot()
