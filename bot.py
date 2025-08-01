#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import asyncio
import logging
from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import Database
from music_player import MusicPlayer
from utils import get_file_from_youtube, format_duration
import time
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramMusicBot:
    def __init__(self):
        self.app = Client(
            "music_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        self.assistant = Client(
            "assistant",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=Config.SESSION_STRING
        ) if Config.SESSION_STRING else None
        
        self.db = Database()
        self.music_player = MusicPlayer()
        self.start_time = time.time()
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register all command handlers"""
        
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            await self.handle_start(message)
        
        @self.app.on_message(filters.command("help"))
        async def help_command(client, message: Message):
            await self.handle_help(message)
        
        @self.app.on_message(filters.command("song"))
        async def song_command(client, message: Message):
            await self.handle_song_download(message)
        
        @self.app.on_message(filters.command(["play", "p"]))
        async def play_command(client, message: Message):
            await self.handle_play(message)
        
        @self.app.on_message(filters.command(["vplay", "vp"]))
        async def vplay_command(client, message: Message):
            await self.handle_vplay(message)
        
        @self.app.on_message(filters.command(["playforce", "pf"]))
        async def playforce_command(client, message: Message):
            await self.handle_playforce(message)
        
        @self.app.on_message(filters.command(["vplayforce", "vpf"]))
        async def vplayforce_command(client, message: Message):
            await self.handle_vplayforce(message)
        
        @self.app.on_message(filters.command("stop"))
        async def stop_command(client, message: Message):
            await self.handle_stop(message)
        
        @self.app.on_message(filters.command(["queue", "q"]))
        async def queue_command(client, message: Message):
            await self.handle_queue(message)
        
        @self.app.on_message(filters.command("shuffle"))
        async def shuffle_command(client, message: Message):
            await self.handle_shuffle(message)
        
        @self.app.on_message(filters.command(["speed", "playback"]))
        async def speed_command(client, message: Message):
            await self.handle_speed(message)
        
        @self.app.on_message(filters.command(["cspeed", "cplayback"]))
        async def cspeed_command(client, message: Message):
            await self.handle_cspeed(message)
        
        @self.app.on_message(filters.command("seek"))
        async def seek_command(client, message: Message):
            await self.handle_seek(message)
        
        @self.app.on_message(filters.command("seekback"))
        async def seekback_command(client, message: Message):
            await self.handle_seekback(message)
        
        @self.app.on_message(filters.command("loop"))
        async def loop_command(client, message: Message):
            await self.handle_loop(message)
        
        @self.app.on_message(filters.command(["cplay", "cp"]))
        async def cplay_command(client, message: Message):
            await self.handle_cplay(message)
        
        @self.app.on_message(filters.command(["cvplay", "cvp"]))
        async def cvplay_command(client, message: Message):
            await self.handle_cvplay(message)
        
        @self.app.on_message(filters.command(["cplayforce", "cpf"]))
        async def cplayforce_command(client, message: Message):
            await self.handle_cplayforce(message)
        
        @self.app.on_message(filters.command(["cvplayforce", "cvpf"]))
        async def cvplayforce_command(client, message: Message):
            await self.handle_cvplayforce(message)
        
        @self.app.on_message(filters.command("channelplay"))
        async def channelplay_command(client, message: Message):
            await self.handle_channelplay(message)
        
        # Admin commands
        @self.app.on_message(filters.command("auth") & filters.user(Config.SUDO_USERS))
        async def auth_command(client, message: Message):
            await self.handle_auth(message)
        
        @self.app.on_message(filters.command("unauth") & filters.user(Config.SUDO_USERS))
        async def unauth_command(client, message: Message):
            await self.handle_unauth(message)
        
        @self.app.on_message(filters.command("authusers") & filters.user(Config.SUDO_USERS))
        async def authusers_command(client, message: Message):
            await self.handle_authusers(message)
        
        # Sudo commands
        @self.app.on_message(filters.command("ping") & filters.user(Config.SUDO_USERS))
        async def ping_command(client, message: Message):
            await self.handle_ping(message)
        
        @self.app.on_message(filters.command("stats") & filters.user(Config.SUDO_USERS))
        async def stats_command(client, message: Message):
            await self.handle_stats(message)
        
        @self.app.on_message(filters.command("blacklistchat") & filters.user(Config.SUDO_USERS))
        async def blacklistchat_command(client, message: Message):
            await self.handle_blacklistchat(message)
        
        @self.app.on_message(filters.command("whitelistchat") & filters.user(Config.SUDO_USERS))
        async def whitelistchat_command(client, message: Message):
            await self.handle_whitelistchat(message)
        
        @self.app.on_message(filters.command("blacklistedchats") & filters.user(Config.SUDO_USERS))
        async def blacklistedchats_command(client, message: Message):
            await self.handle_blacklistedchats(message)
        
        @self.app.on_message(filters.command("block") & filters.user(Config.SUDO_USERS))
        async def block_command(client, message: Message):
            await self.handle_block(message)
        
        @self.app.on_message(filters.command("unblock") & filters.user(Config.SUDO_USERS))
        async def unblock_command(client, message: Message):
            await self.handle_unblock(message)
        
        @self.app.on_message(filters.command("blockedusers") & filters.user(Config.SUDO_USERS))
        async def blockedusers_command(client, message: Message):
            await self.handle_blockedusers(message)
        
        @self.app.on_message(filters.command("gban") & filters.user(Config.SUDO_USERS))
        async def gban_command(client, message: Message):
            await self.handle_gban(message)
        
        @self.app.on_message(filters.command("ungban") & filters.user(Config.SUDO_USERS))
        async def ungban_command(client, message: Message):
            await self.handle_ungban(message)
        
        @self.app.on_message(filters.command("gbannedusers") & filters.user(Config.SUDO_USERS))
        async def gbannedusers_command(client, message: Message):
            await self.handle_gbannedusers(message)
        
        @self.app.on_message(filters.command("logs") & filters.user(Config.SUDO_USERS))
        async def logs_command(client, message: Message):
            await self.handle_logs(message)
        
        @self.app.on_message(filters.command("logger") & filters.user(Config.SUDO_USERS))
        async def logger_command(client, message: Message):
            await self.handle_logger(message)
        
        @self.app.on_message(filters.command("maintenance") & filters.user(Config.SUDO_USERS))
        async def maintenance_command(client, message: Message):
            await self.handle_maintenance(message)
        
        @self.app.on_message(filters.command("broadcast") & filters.user(Config.SUDO_USERS))
        async def broadcast_command(client, message: Message):
            await self.handle_broadcast(message)
    
    async def handle_start(self, message: Message):
        """Handle /start command"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is gbanned
        if await self.db.is_gbanned(user_id):
            return
        
        # Check if chat is blacklisted
        if await self.db.is_chat_blacklisted(chat_id):
            return
        
        # Add user to database
        await self.db.add_user(user_id, message.from_user.first_name)
        await self.db.add_chat(chat_id, message.chat.title or "Private")
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Commands", callback_data="commands"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            ],
            [
                InlineKeyboardButton("👮‍♂️ Admin", callback_data="admin"),
                InlineKeyboardButton("🎵 Music", callback_data="music")
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ]
        ])
        
        photo_url = "https://telegra.ph/file/a5b3c3544fdc81e48e226.jpg"  # Add your bot's photo URL
        
        welcome_text = f"""
🎵 **Welcome to Music Bot!** 🎵

Hello {message.from_user.first_name}! I'm your personal music assistant.

✨ **Features:**
• Play music in voice calls
• Download songs from YouTube
• Queue management
• Speed control
• Channel streaming
• And much more!

🚀 **Quick Start:**
Use /play [song name] to start playing music!

Click the buttons below to explore all commands.
        """
        
        try:
            await message.reply_photo(
                photo=photo_url,
                caption=welcome_text,
                reply_markup=keyboard
            )
        except:
            await message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def handle_help(self, message: Message):
        """Handle /help command"""
        help_text = """
🎵 **Music Bot Commands** 🎵

**🎧 Music Commands:**
• `/play` or `/p` [song] - Play music
• `/vplay` or `/vp` [song] - Play with video
• `/song` [song] - Download MP3/MP4
• `/queue` or `/q` - Show queue
• `/shuffle` - Shuffle queue
• `/stop` - Stop playback
• `/loop` [1-10] - Set loop count

**⚡ Force Commands:**
• `/playforce` - Force play (clear queue)
• `/vplayforce` - Force video play

**🎛️ Control Commands:**
• `/speed` [0.5-2.0] - Adjust speed
• `/seek` [duration] - Seek to position
• `/seekback` [duration] - Seek backward

**📺 Channel Commands:**
• `/cplay` - Channel audio play
• `/cvplay` - Channel video play
• `/channelplay` - Connect channel

**👑 Admin Commands (Authorized users only):**
• `/auth` [user] - Authorize user
• `/unauth` [user] - Remove authorization

**🔧 Sudo Commands (Owner only):**
• `/ping` - Check bot latency
• `/stats` - Bot statistics
• `/gban` [user] - Global ban
• `/broadcast` - Send broadcast

Use buttons below for detailed command categories!
        """
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Music", callback_data="music_help"),
                InlineKeyboardButton("👑 Admin", callback_data="admin_help")
            ],
            [
                InlineKeyboardButton("🔧 Sudo", callback_data="sudo_help"),
                InlineKeyboardButton("📺 Channel", callback_data="channel_help")
            ],
            [InlineKeyboardButton("🏠 Back to Start", callback_data="start")]
        ])
        
        await message.reply_text(help_text, reply_markup=keyboard)
    
    async def handle_song_download(self, message: Message):
        """Handle /song command for downloading"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a song name!\n\nExample: `/song Never Gonna Give You Up`")
            return
        
        query = " ".join(message.command[1:])
        processing_msg = await message.reply_text("🔄 Searching and downloading...")
        
        try:
            # Download audio and video
            audio_file, video_file, title, duration = await get_file_from_youtube(query)
            
            if not audio_file:
                await processing_msg.edit_text("❌ Song not found!")
                return
            
            # Send audio file
            await message.reply_audio(
                audio=audio_file,
                title=title,
                duration=duration,
                caption=f"🎵 **{title}**\n⏱️ Duration: {format_duration(duration)}"
            )
            
            # Send video file if available
            if video_file:
                await message.reply_video(
                    video=video_file,
                    caption=f"🎬 **{title}**\n⏱️ Duration: {format_duration(duration)}"
                )
            
            await processing_msg.delete()
            
            # Clean up files
            if os.path.exists(audio_file):
                os.remove(audio_file)
            if video_file and os.path.exists(video_file):
                os.remove(video_file)
                
        except Exception as e:
            logger.error(f"Error in song download: {e}")
            await processing_msg.edit_text("❌ An error occurred while downloading the song!")
    
    async def handle_play(self, message: Message):
        """Handle /play command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a song name!\n\nExample: `/play Never Gonna Give You Up`")
            return
        
        query = " ".join(message.command[1:])
        chat_id = message.chat.id
        
        # Check if user can use the bot
        if not await self.can_use_bot(message):
            return
        
        processing_msg = await message.reply_text("🔄 Adding to queue...")
        
        try:
            result = await self.music_player.add_to_queue(chat_id, query, message.from_user)
            if result:
                await processing_msg.edit_text(f"✅ Added to queue: **{result['title']}**")
                await self.music_player.play_next(chat_id, self.assistant or self.app)
            else:
                await processing_msg.edit_text("❌ Song not found!")
        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await processing_msg.edit_text("❌ An error occurred!")
    
    async def handle_vplay(self, message: Message):
        """Handle /vplay command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a song name!\n\nExample: `/vplay Never Gonna Give You Up`")
            return
        
        query = " ".join(message.command[1:])
        chat_id = message.chat.id
        
        if not await self.can_use_bot(message):
            return
        
        processing_msg = await message.reply_text("🔄 Adding video to queue...")
        
        try:
            result = await self.music_player.add_to_queue(chat_id, query, message.from_user, video=True)
            if result:
                await processing_msg.edit_text(f"✅ Added video to queue: **{result['title']}**")
                await self.music_player.play_next(chat_id, self.assistant or self.app)
            else:
                await processing_msg.edit_text("❌ Video not found!")
        except Exception as e:
            logger.error(f"Error in vplay command: {e}")
            await processing_msg.edit_text("❌ An error occurred!")
    
    async def handle_playforce(self, message: Message):
        """Handle /playforce command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a song name!")
            return
        
        query = " ".join(message.command[1:])
        chat_id = message.chat.id
        
        if not await self.can_use_bot(message):
            return
        
        # Clear queue and add song
        await self.music_player.clear_queue(chat_id)
        await self.handle_play(message)
    
    async def handle_vplayforce(self, message: Message):
        """Handle /vplayforce command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide a song name!")
            return
        
        query = " ".join(message.command[1:])
        chat_id = message.chat.id
        
        if not await self.can_use_bot(message):
            return
        
        # Clear queue and add video
        await self.music_player.clear_queue(chat_id)
        await self.handle_vplay(message)
    
    async def handle_stop(self, message: Message):
        """Handle /stop command"""
        chat_id = message.chat.id
        
        if not await self.can_use_bot(message):
            return
        
        await self.music_player.stop(chat_id, self.assistant or self.app)
        await message.reply_text("⏹️ Stopped playback and cleared queue!")
    
    async def handle_queue(self, message: Message):
        """Handle /queue command"""
        chat_id = message.chat.id
        queue = await self.music_player.get_queue(chat_id)
        
        if not queue:
            await message.reply_text("📭 Queue is empty!")
            return
        
        queue_text = "🎵 **Current Queue:**\n\n"
        for i, track in enumerate(queue[:10], 1):
            queue_text += f"{i}. **{track['title']}**\n"
            queue_text += f"   👤 Requested by: {track['requester']['first_name']}\n\n"
        
        if len(queue) > 10:
            queue_text += f"... and {len(queue) - 10} more tracks"
        
        await message.reply_text(queue_text)
    
    async def handle_shuffle(self, message: Message):
        """Handle /shuffle command"""
        chat_id = message.chat.id
        
        if not await self.can_use_bot(message):
            return
        
        shuffled = await self.music_player.shuffle_queue(chat_id)
        if shuffled:
            await message.reply_text("🔀 Queue shuffled!")
        else:
            await message.reply_text("❌ Queue is empty!")
    
    async def handle_speed(self, message: Message):
        """Handle /speed command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide speed value (0.5-2.0)!\n\nExample: `/speed 1.5`")
            return
        
        try:
            speed = float(message.command[1])
            if speed < 0.5 or speed > 2.0:
                await message.reply_text("❌ Speed must be between 0.5 and 2.0!")
                return
            
            chat_id = message.chat.id
            success = await self.music_player.set_speed(chat_id, speed)
            
            if success:
                await message.reply_text(f"⚡ Speed set to {speed}x")
            else:
                await message.reply_text("❌ No active playback!")
                
        except ValueError:
            await message.reply_text("❌ Invalid speed value!")
    
    async def handle_cspeed(self, message: Message):
        """Handle /cspeed command for channel"""
        # Similar to handle_speed but for channel playback
        await self.handle_speed(message)  # For now, same implementation
    
    async def handle_seek(self, message: Message):
        """Handle /seek command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide seek duration!\n\nExample: `/seek 30` (seeks to 30 seconds)")
            return
        
        try:
            seek_time = int(message.command[1])
            chat_id = message.chat.id
            success = await self.music_player.seek(chat_id, seek_time)
            
            if success:
                await message.reply_text(f"⏩ Seeked to {format_duration(seek_time)}")
            else:
                await message.reply_text("❌ No active playback!")
                
        except ValueError:
            await message.reply_text("❌ Invalid seek time!")
    
    async def handle_seekback(self, message: Message):
        """Handle /seekback command"""
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide seekback duration!\n\nExample: `/seekback 10`")
            return
        
        try:
            seekback_time = int(message.command[1])
            chat_id = message.chat.id
            success = await self.music_player.seekback(chat_id, seekback_time)
            
            if success:
                await message.reply_text(f"⏪ Seeked back {seekback_time} seconds")
            else:
                await message.reply_text("❌ No active playback!")
                
        except ValueError:
            await message.reply_text("❌ Invalid seekback time!")
    
    async def handle_loop(self, message: Message):
        """Handle /loop command"""
        chat_id = message.chat.id
        
        if len(message.command) == 1:
            # Toggle loop
            current_loop = await self.music_player.get_loop_status(chat_id)
            new_status = not current_loop
            await self.music_player.set_loop(chat_id, new_status)
            status_text = "enabled" if new_status else "disabled"
            await message.reply_text(f"🔂 Loop {status_text}!")
        else:
            try:
                loop_count = int(message.command[1])
                if loop_count < 1 or loop_count > 10:
                    await message.reply_text("❌ Loop count must be between 1 and 10!")
                    return
                
                # Only sudoers can set specific loop counts
                if message.from_user.id not in Config.SUDO_USERS:
                    await message.reply_text("❌ Only bot owners can set specific loop counts!")
                    return
                
                await self.music_player.set_loop_count(chat_id, loop_count)
                await message.reply_text(f"🔂 Loop set to {loop_count} times!")
                
            except ValueError:
                await message.reply_text("❌ Invalid loop count!")
    
    async def handle_cplay(self, message: Message):
        """Handle /cplay command"""
        # Channel play implementation
        await message.reply_text("📺 Channel play feature coming soon!")
    
    async def handle_cvplay(self, message: Message):
        """Handle /cvplay command"""
        # Channel video play implementation
        await message.reply_text("📺 Channel video play feature coming soon!")
    
    async def handle_cplayforce(self, message: Message):
        """Handle /cplayforce command"""
        await message.reply_text("📺 Channel play force feature coming soon!")
    
    async def handle_cvplayforce(self, message: Message):
        """Handle /cvplayforce command"""
        await message.reply_text("📺 Channel video play force feature coming soon!")
    
    async def handle_channelplay(self, message: Message):
        """Handle /channelplay command"""
        await message.reply_text("📺 Channel connection feature coming soon!")
    
    # Admin Commands
    async def handle_auth(self, message: Message):
        """Handle /auth command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        chat_id = message.chat.id
        await self.db.add_auth_user(chat_id, user_id)
        await message.reply_text(f"✅ {username} has been authorized in this chat!")
    
    async def handle_unauth(self, message: Message):
        """Handle /unauth command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        chat_id = message.chat.id
        await self.db.remove_auth_user(chat_id, user_id)
        await message.reply_text(f"❌ {username} has been unauthorized in this chat!")
    
    async def handle_authusers(self, message: Message):
        """Handle /authusers command"""
        chat_id = message.chat.id
        auth_users = await self.db.get_auth_users(chat_id)
        
        if not auth_users:
            await message.reply_text("📭 No authorized users in this chat!")
            return
        
        text = "👮‍♂️ **Authorized Users:**\n\n"
        for user_id in auth_users:
            try:
                user = await self.app.get_users(user_id)
                text += f"• {user.first_name} (@{user.username or 'No username'})\n"
            except:
                text += f"• User ID: {user_id}\n"
        
        await message.reply_text(text)
    
    # Sudo Commands
    async def handle_ping(self, message: Message):
        """Handle /ping command"""
        start_time = time.time()
        ping_msg = await message.reply_text("🏓 Pinging...")
        end_time = time.time()
        
        ping_time = round((end_time - start_time) * 1000, 2)
        uptime = time.time() - self.start_time
        uptime_str = format_duration(int(uptime))
        
        await ping_msg.edit_text(
            f"🏓 **Pong!**\n\n"
            f"📡 **Latency:** {ping_time}ms\n"
            f"⏰ **Uptime:** {uptime_str}"
        )
    
    async def handle_stats(self, message: Message):
        """Handle /stats command"""
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get bot stats
        total_users = await self.db.get_total_users()
        total_chats = await self.db.get_total_chats()
        uptime = time.time() - self.start_time
        uptime_str = format_duration(int(uptime))
        
        stats_text = f"""
📊 **Bot Statistics**

**🤖 Bot Stats:**
• Users: {total_users}
• Chats: {total_chats}
• Uptime: {uptime_str}

**💻 System Stats:**
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used//1024//1024} MB / {memory.total//1024//1024} MB)
• Disk: {disk.percent}% ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)
        """
        
        await message.reply_text(stats_text)
    
    async def handle_blacklistchat(self, message: Message):
        """Handle /blacklistchat command"""
        if len(message.command) < 2:
            chat_id = message.chat.id
        else:
            try:
                chat_id = int(message.command[1])
            except ValueError:
                await message.reply_text("❌ Invalid chat ID!")
                return
        
        await self.db.blacklist_chat(chat_id)
        await message.reply_text(f"🚫 Chat {chat_id} has been blacklisted!")
    
    async def handle_whitelistchat(self, message: Message):
        """Handle /whitelistchat command"""
        if len(message.command) < 2:
            chat_id = message.chat.id
        else:
            try:
                chat_id = int(message.command[1])
            except ValueError:
                await message.reply_text("❌ Invalid chat ID!")
                return
        
        await self.db.whitelist_chat(chat_id)
        await message.reply_text(f"✅ Chat {chat_id} has been whitelisted!")
    
    async def handle_blacklistedchats(self, message: Message):
        """Handle /blacklistedchats command"""
        blacklisted = await self.db.get_blacklisted_chats()
        
        if not blacklisted:
            await message.reply_text("📭 No blacklisted chats!")
            return
        
        text = "🚫 **Blacklisted Chats:**\n\n"
        for chat_id in blacklisted[:20]:  # Show only first 20
            try:
                chat = await self.app.get_chat(chat_id)
                text += f"• {chat.title} ({chat_id})\n"
            except:
                text += f"• Chat ID: {chat_id}\n"
        
        if len(blacklisted) > 20:
            text += f"\n... and {len(blacklisted) - 20} more chats"
        
        await message.reply_text(text)
    
    async def handle_block(self, message: Message):
        """Handle /block command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        await self.db.block_user(user_id)
        await message.reply_text(f"🚫 {username} has been blocked!")
    
    async def handle_unblock(self, message: Message):
        """Handle /unblock command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        await self.db.unblock_user(user_id)
        await message.reply_text(f"✅ {username} has been unblocked!")
    
    async def handle_blockedusers(self, message: Message):
        """Handle /blockedusers command"""
        blocked = await self.db.get_blocked_users()
        
        if not blocked:
            await message.reply_text("📭 No blocked users!")
            return
        
        text = "🚫 **Blocked Users:**\n\n"
        for user_id in blocked[:20]:  # Show only first 20
            try:
                user = await self.app.get_users(user_id)
                text += f"• {user.first_name} (@{user.username or 'No username'})\n"
            except:
                text += f"• User ID: {user_id}\n"
        
        if len(blocked) > 20:
            text += f"\n... and {len(blocked) - 20} more users"
        
        await message.reply_text(text)
    
    async def handle_gban(self, message: Message):
        """Handle /gban command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        # Don't allow gbanning sudo users
        if user_id in Config.SUDO_USERS:
            await message.reply_text("❌ Cannot gban a sudo user!")
            return
        
        await self.db.gban_user(user_id)
        await message.reply_text(f"🌍🚫 {username} has been globally banned!")
        
        # Optionally kick from all served chats
        chats = await self.db.get_all_chats()
        kicked_count = 0
        for chat_id in chats:
            try:
                await self.app.ban_chat_member(chat_id, user_id)
                kicked_count += 1
            except:
                pass
        
        if kicked_count > 0:
            await message.reply_text(f"👢 Kicked from {kicked_count} chats!")
    
    async def handle_ungban(self, message: Message):
        """Handle /ungban command"""
        if len(message.command) < 2 and not message.reply_to_message:
            await message.reply_text("❌ Please provide username/user_id or reply to a user!")
            return
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            username = message.reply_to_message.from_user.first_name
        else:
            try:
                user_input = message.command[1]
                if user_input.startswith("@"):
                    user_input = user_input[1:]
                
                if user_input.isdigit():
                    user_id = int(user_input)
                    user = await self.app.get_users(user_id)
                    username = user.first_name
                else:
                    user = await self.app.get_users(user_input)
                    user_id = user.id
                    username = user.first_name
            except:
                await message.reply_text("❌ User not found!")
                return
        
        await self.db.ungban_user(user_id)
        await message.reply_text(f"✅ {username} has been ungbanned!")
    
    async def handle_gbannedusers(self, message: Message):
        """Handle /gbannedusers command"""
        gbanned = await self.db.get_gbanned_users()
        
        if not gbanned:
            await message.reply_text("📭 No globally banned users!")
            return
        
        text = "🌍🚫 **Globally Banned Users:**\n\n"
        for user_id in gbanned[:20]:  # Show only first 20
            try:
                user = await self.app.get_users(user_id)
                text += f"• {user.first_name} (@{user.username or 'No username'})\n"
            except:
                text += f"• User ID: {user_id}\n"
        
        if len(gbanned) > 20:
            text += f"\n... and {len(gbanned) - 20} more users"
        
        await message.reply_text(text)
    
    async def handle_logs(self, message: Message):
        """Handle /logs command"""
        try:
            if os.path.exists("bot.log"):
                await message.reply_document("bot.log", caption="📋 Bot Logs")
            else:
                await message.reply_text("❌ No log file found!")
        except Exception as e:
            await message.reply_text(f"❌ Error sending logs: {str(e)}")
    
    async def handle_logger(self, message: Message):
        """Handle /logger command"""
        if len(message.command) < 2:
            status = "enabled" if Config.LOGGING_ENABLED else "disabled"
            await message.reply_text(f"📋 Logging is currently **{status}**\n\nUse `/logger enable` or `/logger disable`")
            return
        
        action = message.command[1].lower()
        if action == "enable":
            Config.LOGGING_ENABLED = True
            await message.reply_text("✅ Logging enabled!")
        elif action == "disable":
            Config.LOGGING_ENABLED = False
            await message.reply_text("❌ Logging disabled!")
        else:
            await message.reply_text("❌ Use `/logger enable` or `/logger disable`")
    
    async def handle_maintenance(self, message: Message):
        """Handle /maintenance command"""
        if len(message.command) < 2:
            status = "enabled" if Config.MAINTENANCE_MODE else "disabled"
            await message.reply_text(f"🔧 Maintenance mode is currently **{status}**\n\nUse `/maintenance enable` or `/maintenance disable`")
            return
        
        action = message.command[1].lower()
        if action == "enable":
            Config.MAINTENANCE_MODE = True
            await message.reply_text("🔧 Maintenance mode enabled! Bot will only respond to sudo users.")
        elif action == "disable":
            Config.MAINTENANCE_MODE = False
            await message.reply_text("✅ Maintenance mode disabled! Bot is now public.")
        else:
            await message.reply_text("❌ Use `/maintenance enable` or `/maintenance disable`")
    
    async def handle_broadcast(self, message: Message):
        """Handle /broadcast command"""
        if len(message.command) < 2:
            await message.reply_text(
                "❌ Please provide broadcast message!\n\n"
                "**Usage:** `/broadcast [options] <message>`\n\n"
                "**Options:**\n"
                "• `-pin` - Pin message in chats\n"
                "• `-pinloud` - Pin with notification\n"
                "• `-user` - Broadcast to users only\n"
                "• `-assistant` - Send from assistant account\n"
                "• `-nobot` - Don't send from bot\n\n"
                "**Example:** `/broadcast -pin -user Hello everyone!`"
            )
            return
        
        # Parse options and message
        args = message.command[1:]
        options = []
        message_parts = []
        
        for arg in args:
            if arg.startswith('-'):
                options.append(arg)
            else:
                message_parts.append(arg)
        
        if not message_parts:
            await message.reply_text("❌ No message provided!")
            return
        
        broadcast_text = " ".join(message_parts)
        
        # Get broadcast targets
        if "-user" in options:
            targets = await self.db.get_all_users()
            target_type = "users"
        else:
            targets = await self.db.get_all_chats()
            target_type = "chats"
        
        if not targets:
            await message.reply_text(f"❌ No {target_type} found!")
            return
        
        # Start broadcasting
        progress_msg = await message.reply_text(f"📢 Broadcasting to {len(targets)} {target_type}...")
        
        sent_count = 0
        failed_count = 0
        
        for target_id in targets:
            try:
                # Choose which client to use
                client = self.app
                if "-assistant" in options and self.assistant:
                    client = self.assistant
                elif "-nobot" in options:
                    continue
                
                # Send message
                sent_msg = await client.send_message(target_id, broadcast_text)
                
                # Pin if requested
                if "-pin" in options:
                    await sent_msg.pin(disable_notification="-pinloud" not in options)
                elif "-pinloud" in options:
                    await sent_msg.pin(disable_notification=False)
                
                sent_count += 1
                
                # Update progress every 50 messages
                if sent_count % 50 == 0:
                    await progress_msg.edit_text(
                        f"📢 Broadcasting...\n✅ Sent: {sent_count}\n❌ Failed: {failed_count}"
                    )
                
                # Small delay to avoid flooding
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Broadcast error for {target_id}: {e}")
        
        # Final report
        await progress_msg.edit_text(
            f"📢 **Broadcast Complete!**\n\n"
            f"✅ **Sent:** {sent_count}\n"
            f"❌ **Failed:** {failed_count}\n"
            f"📊 **Total:** {len(targets)}"
        )
    
    async def can_use_bot(self, message: Message) -> bool:
        """Check if user can use the bot"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check maintenance mode
        if Config.MAINTENANCE_MODE and user_id not in Config.SUDO_USERS:
            await message.reply_text("🔧 Bot is under maintenance! Please try again later.")
            return False
        
        # Check if user is gbanned
        if await self.db.is_gbanned(user_id):
            return False
        
        # Check if user is blocked
        if await self.db.is_user_blocked(user_id):
            return False
        
        # Check if chat is blacklisted
        if await self.db.is_chat_blacklisted(chat_id):
            return False
        
        # Check if user is authorized (for groups)
        if message.chat.type in ["group", "supergroup"]:
            if user_id not in Config.SUDO_USERS:
                if not await self.db.is_auth_user(chat_id, user_id):
                    # Check if user is admin
                    try:
                        member = await self.app.get_chat_member(chat_id, user_id)
                        if member.status not in ["creator", "administrator"]:
                            await message.reply_text("❌ You need to be authorized to use music commands in this group!")
                            return False
                    except:
                        await message.reply_text("❌ You need to be authorized to use music commands in this group!")
                        return False
        
        return True
    
    async def run(self):
        """Start the bot"""
        logger.info("Starting Music Bot...")
        
        # Start assistant if available
        if self.assistant:
            await self.assistant.start()
            logger.info("Assistant started")
        
        # Start main bot
        await self.app.start()
        logger.info("Bot started successfully!")
        
        # Keep the bot running
        await idle()
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping bot...")
        
        if self.assistant:
            await self.assistant.stop()
        
        await self.app.stop()
        logger.info("Bot stopped")

if __name__ == "__main__":
    bot = TelegramMusicBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        asyncio.run(bot.stop())
