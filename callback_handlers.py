#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

class CallbackHandlers:
    """Handle inline keyboard callbacks"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.register_callbacks()
    
    def register_callbacks(self):
        """Register all callback handlers"""
        
        @self.bot.app.on_callback_query()
        async def handle_callback(client, callback_query: CallbackQuery):
            """Main callback handler"""
            try:
                data = callback_query.data
                user_id = callback_query.from_user.id
                
                # Check if user is gbanned
                if await self.bot.db.is_gbanned(user_id):
                    await callback_query.answer("❌ You are banned from using this bot!", show_alert=True)
                    return
                
                # Handle different callback types
                if data == "commands":
                    await self.show_commands_menu(callback_query)
                elif data == "help":
                    await self.show_help_menu(callback_query)
                elif data == "admin":
                    await self.show_admin_menu(callback_query)
                elif data == "music":
                    await self.show_music_menu(callback_query)
                elif data == "broadcast":
                    await self.show_broadcast_menu(callback_query)
                elif data == "settings":
                    await self.show_settings_menu(callback_query)
                elif data == "music_help":
                    await self.show_music_help(callback_query)
                elif data == "admin_help":
                    await self.show_admin_help(callback_query)
                elif data == "sudo_help":
                    await self.show_sudo_help(callback_query)
                elif data == "channel_help":
                    await self.show_channel_help(callback_query)
                elif data == "start":
                    await self.show_start_menu(callback_query)
                elif data.startswith("queue_"):
                    await self.handle_queue_action(callback_query, data)
                elif data.startswith("player_"):
                    await self.handle_player_action(callback_query, data)
                else:
                    await callback_query.answer("❓ Unknown command!", show_alert=True)
                    
            except Exception as e:
                logger.error(f"Callback error: {e}")
                await callback_query.answer("❌ An error occurred!", show_alert=True)
    
    async def show_commands_menu(self, callback_query: CallbackQuery):
        """Show commands menu"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Music", callback_data="music_help"),
                InlineKeyboardButton("👑 Admin", callback_data="admin_help")
            ],
            [
                InlineKeyboardButton("🔧 Sudo", callback_data="sudo_help"),
                InlineKeyboardButton("📺 Channel", callback_data="channel_help")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="start")]
        ])
        
        text = """
📋 **Command Categories**

Choose a category to see available commands:

🎵 **Music** - Playback and queue commands
👑 **Admin** - Chat administration commands  
🔧 **Sudo** - Owner-only commands
📺 **Channel** - Channel streaming commands
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_help_menu(self, callback_query: CallbackQuery):
        """Show help menu"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📚 User Guide", url="https://github.com/anshuplugs11/telegram-music-bot/wiki"),
                InlineKeyboardButton("🐛 Report Bug", url="https://github.com/anshuplugs11/telegram-music-bot/issues")
            ],
            [
                InlineKeyboardButton("💬 Support Chat", url="https://t.me/your_support_chat"),
                InlineKeyboardButton("📢 Updates", url="https://t.me/your_updates_channel")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="start")]
        ])
        
        text = """
❓ **Need Help?**

**📚 User Guide**
Complete documentation and tutorials

**🐛 Report Issues**
Found a bug? Let us know!

**💬 Get Support**
Join our support chat for help

**📢 Stay Updated**
Follow our channel for updates

**🎥 Video Tutorials**
Coming soon on YouTube!
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_admin_menu(self, callback_query: CallbackQuery):
        """Show admin menu"""
        user_id = callback_query.from_user.id
        
        # Check if user is sudo or admin
        is_sudo = user_id in self.bot.config.SUDO_USERS
        
        keyboard = []
        
        if is_sudo:
            keyboard.extend([
                [
                    InlineKeyboardButton("👥 Manage Users", callback_data="manage_users"),
                    InlineKeyboardButton("💬 Manage Chats", callback_data="manage_chats")
                ],
                [
                    InlineKeyboardButton("📊 Statistics", callback_data="view_stats"),
                    InlineKeyboardButton("🔧 Maintenance", callback_data="maintenance_mode")
                ],
                [
                    InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_help"),
                    InlineKeyboardButton("📋 Logs", callback_data="view_logs")
                ]
            ])
        
        keyboard.append([InlineKeyboardButton("🏠 Back", callback_data="start")])
        
        text = "👑 **Admin Panel**\n\n"
        
        if is_sudo:
            text += """
**Available Admin Functions:**

👥 **User Management**
• Global ban/unban users
• Block/unblock users
• View user statistics

💬 **Chat Management**  
• Blacklist/whitelist chats
• View chat statistics
• Manage authorized users

📊 **Statistics**
• Bot usage statistics
• System resource monitoring
• Activity logs

🔧 **Maintenance**
• Enable/disable maintenance mode
• View system logs
• Bot configuration
            """
        else:
            text += "❌ You don't have admin permissions!"
        
        await callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
    
    async def show_music_menu(self, callback_query: CallbackQuery):
        """Show music control menu"""
        chat_id = callback_query.message.chat.id
        
        # Get current playing track
        current_track = await self.bot.music_player.get_current_track(chat_id)
        queue = await self.bot.music_player.get_queue(chat_id)
        
        keyboard = [
            [
                InlineKeyboardButton("⏸️ Pause", callback_data="player_pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="player_resume"),
                InlineKeyboardButton("⏹️ Stop", callback_data="player_stop")
            ],
            [
                InlineKeyboardButton("⏭️ Skip", callback_data="player_skip"),
                InlineKeyboardButton("🔀 Shuffle", callback_data="queue_shuffle"),
                InlineKeyboardButton("🔂 Loop", callback_data="player_loop")
            ],
            [
                InlineKeyboardButton("📋 Queue", callback_data="queue_show"),
                InlineKeyboardButton("🎚️ Volume", callback_data="player_volume"),
                InlineKeyboardButton("⚡ Speed", callback_data="player_speed")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="start")]
        ]
        
        text = "🎵 **Music Player Control**\n\n"
        
        if current_track:
            text += f"**🎧 Now Playing:**\n"
            text += f"📀 {current_track['title']}\n"
            text += f"👤 Requested by: {current_track['requester']['first_name']}\n\n"
        else:
            text += "**⏸️ Nothing is playing**\n\n"
        
        if queue:
            text += f"**📋 Queue:** {len(queue)} track(s)\n"
            text += f"**⏱️ Total Duration:** {sum(track.get('duration', 0) for track in queue) // 60}m\n\n"
        
        text += "**🎛️ Available Controls:**\n"
        text += "• Play/Pause/Stop playback\n"
        text += "• Skip tracks and shuffle queue\n"
        text += "• Adjust volume and speed\n"
        text += "• Manage queue and loop settings"
        
        await callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
    
    async def show_music_help(self, callback_query: CallbackQuery):
        """Show music commands help"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="commands")]
        ])
        
        text = """
🎵 **Music Commands**

**🎧 Basic Playback:**
• `/play <song>` - Play audio in voice chat
• `/vplay <song>` - Play video in voice chat
• `/stop` - Stop playback and leave voice chat
• `/pause` - Pause current track
• `/resume` - Resume playback

**📥 Downloads:**
• `/song <song>` - Download MP3 and MP4 files

**📋 Queue Management:**
• `/queue` - Show current queue
• `/shuffle` - Shuffle the queue
• `/clear` - Clear the queue
• `/skip` - Skip current track

**🎛️ Controls:**
• `/speed <0.5-2.0>` - Adjust playback speed
• `/volume <0-200>` - Set playback volume
• `/seek <seconds>` - Seek to position
• `/seekback <seconds>` - Seek backward

**🔂 Loop Controls:**
• `/loop` - Toggle loop on/off
• `/loop <count>` - Set loop count (sudo only)

**⚡ Force Commands:**
• `/playforce <song>` - Force play (clear queue)
• `/vplayforce <song>` - Force video play
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_admin_help(self, callback_query: CallbackQuery):
        """Show admin commands help"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="commands")]
        ])
        
        text = """
👑 **Admin Commands**

**👥 User Authorization:**
• `/auth <user>` - Authorize user in chat
• `/unauth <user>` - Remove user authorization
• `/authusers` - List authorized users

**🛡️ Moderation:**
• `/block <user>` - Block user from bot
• `/unblock <user>` - Unblock user
• `/blockedusers` - List blocked users

**💬 Chat Management:**
• `/blacklistchat` - Blacklist current chat
• `/whitelistchat` - Whitelist current chat
• `/blacklistedchats` - List blacklisted chats

**🌍 Global Controls (Sudo Only):**
• `/gban <user>` - Global ban user
• `/ungban <user>` - Remove global ban
• `/gbannedusers` - List globally banned users

**📢 Broadcasting:**
• `/broadcast <message>` - Send to all chats
• `/broadcast -user <message>` - Send to all users
• `/broadcast -pin <message>` - Pin message
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_sudo_help(self, callback_query: CallbackQuery):
        """Show sudo commands help"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="commands")]
        ])
        
        user_id = callback_query.from_user.id
        if user_id not in self.bot.config.SUDO_USERS:
            text = "❌ **Access Denied**\n\nSudo commands are only available to bot owners."
        else:
            text = """
🔧 **Sudo Commands**

**📊 Monitoring:**
• `/ping` - Check bot latency and uptime
• `/stats` - Detailed bot statistics
• `/logs` - Get bot log files

**🔧 System Management:**
• `/maintenance enable/disable` - Maintenance mode
• `/logger enable/disable` - Toggle logging
• `/restart` - Restart the bot

**👥 Global User Management:**
• `/gban <user>` - Globally ban user
• `/ungban <user>` - Remove global ban
• `/gbannedusers` - List all gbanned users

**💬 Chat Management:**
• `/blacklistchat <id>` - Blacklist chat
• `/whitelistchat <id>` - Whitelist chat
• `/leave <id>` - Leave chat

**📢 Broadcasting:**
• `/broadcast [options] <message>` - Mass broadcast
• Options: `-pin`, `-user`, `-assistant`, `-nobot`

**🎵 Advanced Music:**
• `/loop <count>` - Set specific loop count
• `/forceplay` - Override all restrictions
            """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_channel_help(self, callback_query: CallbackQuery):
        """Show channel commands help"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back", callback_data="commands")]
        ])
        
        text = """
📺 **Channel Commands**

**🎵 Channel Streaming:**
• `/cplay <song>` - Play audio in connected channel
• `/cvplay <song>` - Play video in connected channel
• `/cstop` - Stop channel playback

**⚡ Channel Force Commands:**
• `/cplayforce <song>` - Force play in channel
• `/cvplayforce <song>` - Force video play in channel

**🔗 Channel Connection:**
• `/channelplay` - Connect channel to group
• `/channelplay <channel_id>` - Connect specific channel

**🎛️ Channel Controls:**
• `/cspeed <0.5-2.0>` - Channel playback speed
• `/cvolume <0-200>` - Channel volume
• `/cloop` - Channel loop toggle

**📋 Channel Queue:**
• `/cqueue` - Show channel queue
• `/cshuffle` - Shuffle channel queue
• `/cskip` - Skip channel track

**ℹ️ Notes:**
• Bot must be admin in the channel
• Channel must have an active voice chat
• Group and channel must be linked
• Some commands require special permissions
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_start_menu(self, callback_query: CallbackQuery):
        """Show start menu"""
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
        
        user_name = callback_query.from_user.first_name
        
        text = f"""
🎵 **Welcome Back, {user_name}!** 🎵

Your personal music assistant is ready to serve.

✨ **Quick Actions:**
• 📋 View all available commands
• 🎵 Control music playback
• 👮‍♂️ Access admin functions
• ⚙️ Manage bot settings

🚀 **Quick Start:**
Use /play [song name] to start playing music!

Click the buttons below to explore all features.
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def handle_queue_action(self, callback_query: CallbackQuery, data: str):
        """Handle queue-related actions"""
        chat_id = callback_query.message.chat.id
        action = data.split("_")[1]
        
        if action == "show":
            queue = await self.bot.music_player.get_queue(chat_id)
            
            if not queue:
                await callback_query.answer("📭 Queue is empty!", show_alert=True)
                return
            
            text = "📋 **Current Queue:**\n\n"
            for i, track in enumerate(queue[:10], 1):
                text += f"{i}. **{track['title'][:30]}{'...' if len(track['title']) > 30 else ''}**\n"
                text += f"   👤 {track['requester']['first_name']}\n\n"
            
            if len(queue) > 10:
                text += f"... and {len(queue) - 10} more tracks"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔀 Shuffle", callback_data="queue_shuffle"),
                    InlineKeyboardButton("🗑️ Clear", callback_data="queue_clear")
                ],
                [InlineKeyboardButton("🏠 Back", callback_data="music")]
            ])
            
            await callback_query.edit_message_text(text, reply_markup=keyboard)
            
        elif action == "shuffle":
            shuffled = await self.bot.music_player.shuffle_queue(chat_id)
            if shuffled:
                await callback_query.answer("🔀 Queue shuffled!", show_alert=True)
            else:
                await callback_query.answer("❌ Queue is empty!", show_alert=True)
                
        elif action == "clear":
            await self.bot.music_player.clear_queue(chat_id)
            await callback_query.answer("🗑️ Queue cleared!", show_alert=True)
        
        await callback_query.answer()
    
    async def handle_player_action(self, callback_query: CallbackQuery, data: str):
        """Handle player control actions"""
        chat_id = callback_query.message.chat.id
        action = data.split("_")[1]
        
        if action == "pause":
            success = await self.bot.music_player.pause(chat_id)
            if success:
                await callback_query.answer("⏸️ Playback paused!")
            else:
                await callback_query.answer("❌ Nothing is playing!", show_alert=True)
                
        elif action == "resume":
            success = await self.bot.music_player.resume(chat_id)
            if success:
                await callback_query.answer("▶️ Playback resumed!")
            else:
                await callback_query.answer("❌ Nothing is paused!", show_alert=True)
                
        elif action == "stop":
            await self.bot.music_player.stop(chat_id, self.bot.assistant or self.bot.app)
            await callback_query.answer("⏹️ Playback stopped!")
            
        elif action == "skip":
            await self.bot.music_player.skip_track(chat_id, self.bot.assistant or self.bot.app)
            await callback_query.answer("⏭️ Track skipped!")
            
        elif action == "loop":
            current_loop = await self.bot.music_player.get_loop_status(chat_id)
            new_status = not current_loop
            await self.bot.music_player.set_loop(chat_id, new_status)
            status_text = "enabled" if new_status else "disabled"
            await callback_query.answer(f"🔂 Loop {status_text}!")
            
        elif action == "volume":
            await self.show_volume_controls(callback_query)
            return
            
        elif action == "speed":
            await self.show_speed_controls(callback_query)
            return
        
        await callback_query.answer()
    
    async def show_volume_controls(self, callback_query: CallbackQuery):
        """Show volume control interface"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔇 0%", callback_data="vol_0"),
                InlineKeyboardButton("🔈 25%", callback_data="vol_25"),
                InlineKeyboardButton("🔉 50%", callback_data="vol_50")
            ],
            [
                InlineKeyboardButton("🔊 75%", callback_data="vol_75"),
                InlineKeyboardButton("📢 100%", callback_data="vol_100"),
                InlineKeyboardButton("📯 150%", callback_data="vol_150")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="music")]
        ])
        
        text = """
🎚️ **Volume Control**

Select a volume level:

🔇 **0%** - Mute
🔈 **25%** - Low  
🔉 **50%** - Medium
🔊 **75%** - High
📢 **100%** - Maximum (Default)
📯 **150%** - Boosted

**Current Volume:** Loading...
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_speed_controls(self, callback_query: CallbackQuery):
        """Show speed control interface"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🐌 0.5x", callback_data="speed_0.5"),
                InlineKeyboardButton("🚶 0.75x", callback_data="speed_0.75"),
                InlineKeyboardButton("🏃 1.0x", callback_data="speed_1.0")
            ],
            [
                InlineKeyboardButton("🏃‍♂️ 1.25x", callback_data="speed_1.25"),
                InlineKeyboardButton("🚀 1.5x", callback_data="speed_1.5"),
                InlineKeyboardButton("⚡ 2.0x", callback_data="speed_2.0")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="music")]
        ])
        
        text = """
⚡ **Speed Control**

Select a playback speed:

🐌 **0.5x** - Half speed
🚶 **0.75x** - Slow
🏃 **1.0x** - Normal (Default)
🏃‍♂️ **1.25x** - Slightly fast
🚀 **1.5x** - Fast  
⚡ **2.0x** - Very fast

**Current Speed:** Loading...
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_broadcast_menu(self, callback_query: CallbackQuery):
        """Show broadcast menu"""
        user_id = callback_query.from_user.id
        
        if user_id not in self.bot.config.SUDO_USERS:
            await callback_query.answer("❌ Only bot owners can access broadcast!", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👥 All Users", callback_data="broadcast_users"),
                InlineKeyboardButton("💬 All Chats", callback_data="broadcast_chats")
            ],
            [
                InlineKeyboardButton("📌 Pinned Broadcast", callback_data="broadcast_pin"),
                InlineKeyboardButton("📢 Loud Broadcast", callback_data="broadcast_loud")
            ],
            [
                InlineKeyboardButton("📊 Broadcast Stats", callback_data="broadcast_stats"),
                InlineKeyboardButton("📝 Broadcast Help", callback_data="broadcast_help")
            ],
            [InlineKeyboardButton("🏠 Back", callback_data="start")]
        ])
        
        # Get statistics
        total_users = await self.bot.db.get_total_users()
        total_chats = await self.bot.db.get_total_chats()
        
        text = f"""
📢 **Broadcast Center**

**📊 Current Reach:**
👥 **Users:** {total_users}
💬 **Chats:** {total_chats}
📈 **Total Reach:** {total_users + total_chats}

**📤 Broadcast Options:**
• Send to all users who started the bot
• Send to all groups and channels
• Pin messages in chats
• Send with notification sound

**⚠️ Usage:**
Use `/broadcast [options] <message>` command for broadcasting.

**Example:**
`/broadcast -pin -user Hello everyone!`
        """
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    
    async def show_settings_menu(self, callback_query: CallbackQuery):
        """Show settings menu"""
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        
        # Get current settings
        settings = await self.bot.db.get_chat_settings(chat_id)
        
        keyboard = []
        
        # Music settings for groups
        if callback_query.message.chat.type in ["group", "supergroup"]:
            keyboard.extend([
                [
                    InlineKeyboardButton(
                        f"🔊 Volume: {settings.get('volume', 100)}%", 
                        callback_data="setting_volume"
                    ),
                    InlineKeyboardButton(
                        f"🔂 Loop: {'On' if settings.get('loop_enabled') else 'Off'}", 
                        callback_data="setting_loop"
                    )
                ],
                [
                    InlineKeyboardButton(
                        f"🚪 Auto Leave: {'On' if settings.get('auto_leave') else 'Off'}", 
                        callback_data="setting_autoleave"
                    ),
                    InlineKeyboardButton("📺 Channel Link", callback_data="setting_channel")
                ]
            ])
        
        # User preferences
        keyboard.extend([
            [
                InlineKeyboardButton("🌐 Language", callback_data="setting_language"),
                InlineKeyboardButton("🎨 Theme", callback_data="setting_theme")
            ],
            [
                InlineKeyboardButton("📱 Notifications", callback_data="setting_notifications"),
                InlineKeyboardButton("🔐 Privacy", callback_data="setting_privacy")
            ]
        ])
        
        # Admin settings
        if user_id in self.bot.config.SUDO_USERS:
            keyboard.append([
                InlineKeyboardButton("⚙️ Bot Settings", callback_data="setting_bot"),
                InlineKeyboardButton("🔧 Advanced", callback_data="setting_advanced")
            ])
        
        keyboard.append([InlineKeyboardButton("🏠 Back", callback_data="start")])
        
        text = f"""
⚙️ **Settings Menu**

**🎵 Music Settings:**
• Volume: {settings.get('volume', 100)}%
• Loop: {'Enabled' if settings.get('loop_enabled') else 'Disabled'}
• Auto Leave: {'Enabled' if settings.get('auto_leave') else 'Disabled'}

**👤 User Preferences:**
• Language: English (Default)
• Theme: Default
• Notifications: Enabled

**💬 Chat Type:** {callback_query.message.chat.type.title()}
**👥 Members:** {callback_query.message.chat.members_count if hasattr(callback_query.message.chat, 'members_count') else 'Unknown'}

Customize your bot experience using the options below.
        """
        
        await callback_query.edit_message_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await callback_query.answer()
    
    # Handle volume and speed callbacks
    async def handle_volume_callback(self, callback_query: CallbackQuery, data: str):
        """Handle volume control callbacks"""
        chat_id = callback_query.message.chat.id
        volume = int(data.split("_")[1])
        
        success = await self.bot.music_player.set_volume(chat_id, volume)
        if success:
            await callback_query.answer(f"🔊 Volume set to {volume}%!")
        else:
            await callback_query.answer("❌ No active playback!", show_alert=True)
    
    async def handle_speed_callback(self, callback_query: CallbackQuery, data: str):
        """Handle speed control callbacks"""
        chat_id = callback_query.message.chat.id
        speed = float(data.split("_")[1])
        
        success = await self.bot.music_player.set_speed(chat_id, speed)
        if success:
            await callback_query.answer(f"⚡ Speed set to {speed}x!")
        else:
            await callback_query.answer("❌ No active playback!", show_alert=True)

# Additional callback handlers can be added here for specific features

def register_callback_handlers(bot_instance):
    """Register callback handlers with the bot"""
    callback_handlers = CallbackHandlers(bot_instance)
    return callback_handlers
