#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiosqlite

logger = logging.getLogger(__name__)

class Database:
    """Database manager for the music bot"""
    
    def __init__(self, db_path: str = "music_bot.db"):
        self.db_path = db_path
        self.lock = asyncio.Lock()
    
    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    is_gbanned BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Chats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id INTEGER PRIMARY KEY,
                    chat_title TEXT,
                    chat_type TEXT,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_blacklisted BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Auth users table (authorized users per chat)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    auth_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, user_id)
                )
            """)
            
            # Queue table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    title TEXT,
                    url TEXT,
                    duration INTEGER,
                    requester_id INTEGER,
                    requester_name TEXT,
                    file_path TEXT,
                    is_video BOOLEAN DEFAULT FALSE,
                    position INTEGER,
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bot settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    chat_id INTEGER PRIMARY KEY,
                    volume INTEGER DEFAULT 100,
                    loop_enabled BOOLEAN DEFAULT FALSE,
                    loop_count INTEGER DEFAULT 1,
                    auto_leave BOOLEAN DEFAULT TRUE,
                    connected_channel INTEGER,
                    settings_json TEXT
                )
            """)
            
            # Activity logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    command TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT
                )
            """)
            
            # Stats table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    date DATE PRIMARY KEY,
                    total_users INTEGER DEFAULT 0,
                    total_chats INTEGER DEFAULT 0,
                    total_commands INTEGER DEFAULT 0,
                    total_songs_played INTEGER DEFAULT 0
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    # User management
    async def add_user(self, user_id: int, first_name: str, username: str = None):
        """Add or update user in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO users (user_id, first_name, username)
                VALUES (?, ?, ?)
            """, (user_id, first_name, username))
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_total_users(self) -> int:
        """Get total user count"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
            return result[0]
    
    async def get_all_users(self) -> List[int]:
        """Get all user IDs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM users")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Chat management
    async def add_chat(self, chat_id: int, chat_title: str, chat_type: str = "group"):
        """Add or update chat in database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO chats (chat_id, chat_title, chat_type)
                VALUES (?, ?, ?)
            """, (chat_id, chat_title, chat_type))
            await db.commit()
    
    async def get_total_chats(self) -> int:
        """Get total chat count"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM chats")
            result = await cursor.fetchone()
            return result[0]
    
    async def get_all_chats(self) -> List[int]:
        """Get all chat IDs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT chat_id FROM chats")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Blacklist/Whitelist management
    async def blacklist_chat(self, chat_id: int):
        """Blacklist a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE chats SET is_blacklisted = TRUE WHERE chat_id = ?
            """, (chat_id,))
            await db.commit()
    
    async def whitelist_chat(self, chat_id: int):
        """Whitelist a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE chats SET is_blacklisted = FALSE WHERE chat_id = ?
            """, (chat_id,))
            await db.commit()
    
    async def is_chat_blacklisted(self, chat_id: int) -> bool:
        """Check if chat is blacklisted"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT is_blacklisted FROM chats WHERE chat_id = ?
            """, (chat_id,))
            result = await cursor.fetchone()
            return bool(result[0]) if result else False
    
    async def get_blacklisted_chats(self) -> List[int]:
        """Get all blacklisted chat IDs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT chat_id FROM chats WHERE is_blacklisted = TRUE
            """)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Block/Unblock users
    async def block_user(self, user_id: int):
        """Block a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET is_blocked = TRUE WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    async def unblock_user(self, user_id: int):
        """Unblock a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET is_blocked = FALSE WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    async def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT is_blocked FROM users WHERE user_id = ?
            """, (user_id,))
            result = await cursor.fetchone()
            return bool(result[0]) if result else False
    
    async def get_blocked_users(self) -> List[int]:
        """Get all blocked user IDs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id FROM users WHERE is_blocked = TRUE
            """)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Global ban management
    async def gban_user(self, user_id: int):
        """Globally ban a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET is_gbanned = TRUE WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    async def ungban_user(self, user_id: int):
        """Remove global ban from user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET is_gbanned = FALSE WHERE user_id = ?
            """, (user_id,))
            await db.commit()
    
    async def is_gbanned(self, user_id: int) -> bool:
        """Check if user is globally banned"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT is_gbanned FROM users WHERE user_id = ?
            """, (user_id,))
            result = await cursor.fetchone()
            return bool(result[0]) if result else False
    
    async def get_gbanned_users(self) -> List[int]:
        """Get all globally banned user IDs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id FROM users WHERE is_gbanned = TRUE
            """)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Auth users management
    async def add_auth_user(self, chat_id: int, user_id: int):
        """Add authorized user for a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO auth_users (chat_id, user_id)
                VALUES (?, ?)
            """, (chat_id, user_id))
            await db.commit()
    
    async def remove_auth_user(self, chat_id: int, user_id: int):
        """Remove authorized user from a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM auth_users WHERE chat_id = ? AND user_id = ?
            """, (chat_id, user_id))
            await db.commit()
    
    async def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        """Check if user is authorized in chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 1 FROM auth_users WHERE chat_id = ? AND user_id = ?
            """, (chat_id, user_id))
            result = await cursor.fetchone()
            return bool(result)
    
    async def get_auth_users(self, chat_id: int) -> List[int]:
        """Get all authorized users for a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT user_id FROM auth_users WHERE chat_id = ?
            """, (chat_id,))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    # Queue management
    async def add_to_queue(self, chat_id: int, track_data: Dict[str, Any]):
        """Add track to queue"""
        async with aiosqlite.connect(self.db_path) as db:
            # Get next position
            cursor = await db.execute("""
                SELECT COALESCE(MAX(position), 0) + 1 FROM queue WHERE chat_id = ?
            """, (chat_id,))
            position = (await cursor.fetchone())[0]
            
            await db.execute("""
                INSERT INTO queue (
                    chat_id, title, url, duration, requester_id, 
                    requester_name, file_path, is_video, position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chat_id, track_data['title'], track_data['url'],
                track_data['duration'], track_data['requester_id'],
                track_data['requester_name'], track_data.get('file_path'),
                track_data.get('is_video', False), position
            ))
            await db.commit()
            return position
    
    async def get_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        """Get queue for a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM queue WHERE chat_id = ? ORDER BY position
            """, (chat_id,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def remove_from_queue(self, chat_id: int, position: int = None):
        """Remove track from queue"""
        async with aiosqlite.connect(self.db_path) as db:
            if position is None:
                # Remove first track
                await db.execute("""
                    DELETE FROM queue WHERE chat_id = ? AND position = (
                        SELECT MIN(position) FROM queue WHERE chat_id = ?
                    )
                """, (chat_id, chat_id))
            else:
                await db.execute("""
                    DELETE FROM queue WHERE chat_id = ? AND position = ?
                """, (chat_id, position))
            await db.commit()
    
    async def clear_queue(self, chat_id: int):
        """Clear entire queue for a chat"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queue WHERE chat_id = ?", (chat_id,))
            await db.commit()
    
    async def shuffle_queue(self, chat_id: int):
        """Shuffle queue for a chat"""
        import random
        async with aiosqlite.connect(self.db_path) as db:
            # Get all tracks except the first one (currently playing)
            cursor = await db.execute("""
                SELECT id FROM queue WHERE chat_id = ? AND position > (
                    SELECT MIN(position) FROM queue WHERE chat_id = ?
                ) ORDER BY position
            """, (chat_id, chat_id))
            track_ids = [row[0] for row in await cursor.fetchall()]
            
            if len(track_ids) < 2:
                return False
            
            # Shuffle the IDs
            random.shuffle(track_ids)
            
            # Update positions
            for i, track_id in enumerate(track_ids, 2):  # Start from position 2
                await db.execute("""
                    UPDATE queue SET position = ? WHERE id = ?
                """, (i, track_id))
            
            await db.commit()
            return True
    
    # Bot settings management
    async def get_chat_settings(self, chat_id: int) -> Dict[str, Any]:
        """Get chat settings"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM bot_settings WHERE chat_id = ?
            """, (chat_id,))
            row = await cursor.fetchone()
            
            if row:
                settings = dict(row)
                if settings.get('settings_json'):
                    try:
                        extra_settings = json.loads(settings['settings_json'])
                        settings.update(extra_settings)
                    except json.JSONDecodeError:
                        pass
                return settings
            else:
                # Return default settings
                return {
                    'chat_id': chat_id,
                    'volume': 100,
                    'loop_enabled': False,
                    'loop_count': 1,
                    'auto_leave': True,
                    'connected_channel': None
                }
    
    async def update_chat_settings(self, chat_id: int, settings: Dict[str, Any]):
        """Update chat settings"""
        async with aiosqlite.connect(self.db_path) as db:
            # Separate standard fields from extra settings
            standard_fields = {
                'volume', 'loop_enabled', 'loop_count', 
                'auto_leave', 'connected_channel'
            }
            
            standard_settings = {k: v for k, v in settings.items() if k in standard_fields}
            extra_settings = {k: v for k, v in settings.items() if k not in standard_fields}
            
            # Build update query for standard fields
            if standard_settings:
                fields = ', '.join(f"{k} = ?" for k in standard_settings.keys())
                values = list(standard_settings.values()) + [chat_id]
                
                await db.execute(f"""
                    INSERT OR REPLACE INTO bot_settings (chat_id, {', '.join(standard_settings.keys())})
                    VALUES (?, {', '.join('?' * len(standard_settings))})
                """, [chat_id] + list(standard_settings.values()))
            
            # Update extra settings as JSON
            if extra_settings:
                await db.execute("""
                    UPDATE bot_settings SET settings_json = ? WHERE chat_id = ?
                """, (json.dumps(extra_settings), chat_id))
            
            await db.commit()
    
    # Activity logging
    async def log_activity(self, user_id: int, chat_id: int, command: str, 
                          success: bool = True, error_message: str = None):
        """Log user activity"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO activity_logs (user_id, chat_id, command, success, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, chat_id, command, success, error_message))
            await db.commit()
    
    async def get_activity_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent activity logs"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM activity_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Statistics
    async def update_daily_stats(self):
        """Update daily statistics"""
        today = datetime.now().date()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Get current counts
            users_count = await self.get_total_users()
            chats_count = await self.get_total_chats()
            
            # Get today's command count
            cursor = await db.execute("""
                SELECT COUNT(*) FROM activity_logs 
                WHERE DATE(timestamp) = ? AND success = TRUE
            """, (today,))
            commands_count = (await cursor.fetchone())[0]
            
            # Update or insert today's stats
            await db.execute("""
                INSERT OR REPLACE INTO stats (date, total_users, total_chats, total_commands)
                VALUES (?, ?, ?, ?)
            """, (today, users_count, chats_count, commands_count))
            
            await db.commit()
    
    async def get_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get statistics for the last N days"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM stats 
                ORDER BY date DESC 
                LIMIT ?
            """, (days,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # Cleanup methods
    async def cleanup_old_logs(self, days: int = 30):
        """Clean up old activity logs"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM activity_logs 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            await db.commit()
    
    async def cleanup_empty_queues(self):
        """Clean up empty queue entries"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM queue 
                WHERE added_date < datetime('now', '-1 day')
            """)
            await db.commit()
    
    async def vacuum_database(self):
        """Optimize database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("VACUUM")
            await db.commit()
    
    async def backup_database(self, backup_path: str):
        """Create database backup"""
        import shutil
        async with self.lock:
            shutil.copy2(self.db_path, backup_path)
    
    async def close(self):
        """Close database connections"""
        # Perform final cleanup
        await self.cleanup_old_logs()
        await self.cleanup_empty_queues()
        logger.info("Database connections closed")

# Initialize database instance
db = Database()

async def init_database():
    """Initialize the database"""
    await db.init_db()

if __name__ == "__main__":
    # Test database operations
    async def test_db():
        await init_database()
        await db.add_user(12345, "Test User", "testuser")
        user = await db.get_user(12345)
        print(f"Added user: {user}")
        
        await db.add_chat(-100123456789, "Test Group", "supergroup")
        total_chats = await db.get_total_chats()
        print(f"Total chats: {total_chats}")
    
    asyncio.run(test_db())
