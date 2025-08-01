#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import logging
from typing import Dict, List, Optional, Any
from pyrogram import Client
from pyrogram.types import User
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import AudioPiped, VideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, HighQualityVideo
from pytgcalls.exceptions import NoActiveGroupCall, NotInGroupCallError
import yt_dlp
import json
import random
from config import Config
from database import Database

logger = logging.getLogger(__name__)

class MusicPlayer:
    """Music player manager for voice calls"""
    
    def __init__(self):
        self.db = Database()
        self.active_calls: Dict[int, PyTgCalls] = {}
        self.queues: Dict[int, List[Dict[str, Any]]] = {}
        self.current_tracks: Dict[int, Dict[str, Any]] = {}
        self.loop_status: Dict[int, bool] = {}
        self.loop_counts: Dict[int, int] = {}
        self.speeds: Dict[int, float] = {}
        self.volumes: Dict[int, int] = {}
        
        # YouTube-DL options
        self.ytdl_opts = Config.YTDL_OPTS.copy()
        self.ytdl_video_opts = Config.YTDL_VIDEO_OPTS.copy()
    
    async def init_pytgcalls(self, client: Client) -> PyTgCalls:
        """Initialize PyTgCalls for a client"""
        pytgcalls = PyTgCalls(client)
        
        @pytgcalls.on_stream_end()
        async def on_stream_end(client, update):
            chat_id = update.chat_id
            await self.on_track_end(chat_id, client)
        
        @pytgcalls.on_closed_voice_chat()
        async def on_closed_vc(client, update):
            chat_id = update.chat_id
            await self.cleanup_chat(chat_id)
        
        await pytgcalls.start()
        return pytgcalls
    
    async def get_pytgcalls(self, chat_id: int, client: Client) -> PyTgCalls:
        """Get or create PyTgCalls instance for chat"""
        if chat_id not in self.active_calls:
            self.active_calls[chat_id] = await self.init_pytgcalls(client)
        return self.active_calls[chat_id]
    
    async def search_youtube(self, query: str, video: bool = False) -> Optional[Dict[str, Any]]:
        """Search YouTube for a track"""
        try:
            opts = self.ytdl_video_opts if video else self.ytdl_opts
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Search for the video
                search_results = ydl.extract_info(
                    f"ytsearch:{query}",
                    download=False
                )
                
                if not search_results or not search_results.get('entries'):
                    return None
                
                # Get the first result
                video_info = search_results['entries'][0]
                
                # Get direct URL
                if 'formats' in video_info:
                    if video:
                        # For video, get best video format
                        format_selector = ydl.build_format_selector('best[height<=720][ext=mp4]/best[ext=mp4]/best')
                        formats = format_selector({'formats': video_info['formats']})
                        if formats:
                            video_info['url'] = formats[0]['url']
                    else:
                        # For audio, get best audio format
                        format_selector = ydl.build_format_selector('bestaudio[ext=m4a]/bestaudio/best')
                        formats = format_selector({'formats': video_info['formats']})
                        if formats:
                            video_info['url'] = formats[0]['url']
                
                return {
                    'title': video_info.get('title', 'Unknown'),
                    'url': video_info.get('url'),
                    'webpage_url': video_info.get('webpage_url'),
                    'duration': video_info.get('duration', 0),
                    'thumbnail': video_info.get('thumbnail'),
                    'uploader': video_info.get('uploader', 'Unknown'),
                    'view_count': video_info.get('view_count', 0),
                    'is_video': video
                }
                
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return None
    
    async def download_track(self, track_info: Dict[str, Any]) -> Optional[str]:
        """Download track for local playback"""
        try:
            output_path = os.path.join(Config.DOWNLOADS_PATH, f"{track_info['title'][:50]}")
            
            opts = self.ytdl_video_opts.copy() if track_info.get('is_video') else self.ytdl_opts.copy()
            opts['outtmpl'] = f"{output_path}.%(ext)s"
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([track_info['webpage_url']])
            
            # Find the downloaded file
            for ext in ['.mp3', '.mp4', '.webm', '.m4a']:
                file_path = f"{output_path}{ext}"
                if os.path.exists(file_path):
                    return file_path
            
            return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def add_to_queue(self, chat_id: int, query: str, requester: User, video: bool = False) -> Optional[Dict[str, Any]]:
        """Add track to queue"""
        try:
            # Search for track
            track_info = await self.search_youtube(query, video)
            if not track_info:
                return None
            
            # Prepare track data
            track_data = {
                'title': track_info['title'],
                'url': track_info['url'],
                'webpage_url': track_info['webpage_url'],
                'duration': track_info['duration'],
                'thumbnail': track_info.get('thumbnail'),
                'uploader': track_info.get('uploader'),
                'requester': {
                    'id': requester.id,
                    'first_name': requester.first_name,
                    'username': requester.username
                },
                'is_video': video
            }
            
            # Add to database queue
            await self.db.add_to_queue(chat_id, {
                'title': track_data['title'],
                'url': track_data['url'],
                'duration': track_data['duration'],
                'requester_id': requester.id,
                'requester_name': requester.first_name,
                'is_video': video
            })
            
            # Add to memory queue
            if chat_id not in self.queues:
                self.queues[chat_id] = []
            
            self.queues[chat_id].append(track_data)
            
            return track_data
            
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            return None
    
    async def get_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        """Get current queue"""
        return self.queues.get(chat_id, [])
    
    async def clear_queue(self, chat_id: int):
        """Clear queue"""
        self.queues[chat_id] = []
        await self.db.clear_queue(chat_id)
    
    async def shuffle_queue(self, chat_id: int) -> bool:
        """Shuffle queue"""
        if chat_id not in self.queues or len(self.queues[chat_id]) <= 1:
            return False
        
        # Keep first track (currently playing) and shuffle the rest
        if len(self.queues[chat_id]) > 1:
            tracks_to_shuffle = self.queues[chat_id][1:]
            random.shuffle(tracks_to_shuffle)
            self.queues[chat_id] = [self.queues[chat_id][0]] + tracks_to_shuffle
        
        # Update database
        await self.db.shuffle_queue(chat_id)
        return True
    
    async def play_next(self, chat_id: int, client: Client):
        """Play next track in queue"""
        try:
            if chat_id not in self.queues or not self.queues[chat_id]:
                return
            
            pytgcalls = await self.get_pytgcalls(chat_id, client)
            track = self.queues[chat_id][0]
            self.current_tracks[chat_id] = track
            
            # Prepare stream
            if track.get('is_video'):
                stream = VideoPiped(
                    track['url'],
                    HighQualityVideo(),
                    HighQualityAudio()
                )
            else:
                stream = AudioPiped(
                    track['url'],
                    HighQualityAudio()
                )
            
            # Join voice chat and play
            try:
                await pytgcalls.join_group_call(
                    chat_id,
                    stream,
                    stream_type=StreamType().video_audio if track.get('is_video') else StreamType().audio
                )
            except NoActiveGroupCall:
                # No active voice chat
                logger.warning(f"No active voice chat in {chat_id}")
                return
            except Exception as e:
                logger.error(f"Error joining voice chat: {e}")
                return
            
            logger.info(f"Playing: {track['title']} in {chat_id}")
            
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            await self.skip_track(chat_id, client)
    
    async def skip_track(self, chat_id: int, client: Client):
        """Skip current track"""
        try:
            if chat_id in self.queues and self.queues[chat_id]:
                # Remove current track
                self.queues[chat_id].pop(0)
                await self.db.remove_from_queue(chat_id)
            
            # Play next track
            await self.play_next(chat_id, client)
            
        except Exception as e:
            logger.error(f"Error skipping track: {e}")
    
    async def stop(self, chat_id: int, client: Client):
        """Stop playback and clear queue"""
        try:
            if chat_id in self.active_calls:
                pytgcalls = self.active_calls[chat_id]
                await pytgcalls.leave_group_call(chat_id)
            
            await self.cleanup_chat(chat_id)
            
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    async def pause(self, chat_id: int) -> bool:
        """Pause playback"""
        try:
            if chat_id in self.active_calls:
                pytgcalls = self.active_calls[chat_id]
                await pytgcalls.pause_stream(chat_id)
                return True
        except Exception as e:
            logger.error(f"Error pausing: {e}")
        return False
    
    async def resume(self, chat_id: int) -> bool:
        """Resume playback"""
        try:
            if chat_id in self.active_calls:
                pytgcalls = self.active_calls[chat_id]
                await pytgcalls.resume_stream(chat_id)
                return True
        except Exception as e:
            logger.error(f"Error resuming: {e}")
        return False
    
    async def set_volume(self, chat_id: int, volume: int) -> bool:
        """Set playback volume"""
        try:
            if chat_id in self.active_calls and 0 <= volume <= 200:
                pytgcalls = self.active_calls[chat_id]
                await pytgcalls.change_volume_call(chat_id, volume)
                self.volumes[chat_id] = volume
                
                # Update in database
                settings = await self.db.get_chat_settings(chat_id)
                settings['volume'] = volume
                await self.db.update_chat_settings(chat_id, settings)
                
                return True
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
        return False
    
    async def set_speed(self, chat_id: int, speed: float) -> bool:
        """Set playback speed"""
        try:
            if 0.5 <= speed <= 2.0:
                self.speeds[chat_id] = speed
                # Note: PyTgCalls doesn't directly support speed change
                # This would require restarting the stream with speed parameter
                return True
        except Exception as e:
            logger.error(f"Error setting speed: {e}")
        return False
    
    async def seek(self, chat_id: int, position: int) -> bool:
        """Seek to position in current track"""
        try:
            if chat_id in self.active_calls:
                # Note: PyTgCalls doesn't directly support seeking
                # This would require restarting the stream from the position
                logger.warning("Seek functionality not fully implemented")
                return True
        except Exception as e:
            logger.error(f"Error seeking: {e}")
        return False
    
    async def seekback(self, chat_id: int, seconds: int) -> bool:
        """Seek backward in current track"""
        try:
            # This would calculate current position and seek back
            logger.warning("Seekback functionality not fully implemented")
            return True
        except Exception as e:
            logger.error(f"Error seeking back: {e}")
        return False
    
    async def set_loop(self, chat_id: int, enabled: bool):
        """Enable/disable loop for current track"""
        self.loop_status[chat_id] = enabled
        
        # Update in database
        settings = await self.db.get_chat_settings(chat_id)
        settings['loop_enabled'] = enabled
        await self.db.update_chat_settings(chat_id, settings)
    
    async def set_loop_count(self, chat_id: int, count: int):
        """Set loop count"""
        self.loop_counts[chat_id] = count
        
        # Update in database
        settings = await self.db.get_chat_settings(chat_id)
        settings['loop_count'] = count
        await self.db.update_chat_settings(chat_id, settings)
    
    async def get_loop_status(self, chat_id: int) -> bool:
        """Get loop status"""
        return self.loop_status.get(chat_id, False)
    
    async def on_track_end(self, chat_id: int, client: Client):
        """Handle when a track ends"""
        try:
            current_track = self.current_tracks.get(chat_id)
            if not current_track:
                return
            
            # Check if loop is enabled
            if self.loop_status.get(chat_id, False):
                loop_count = self.loop_counts.get(chat_id, 1)
                if loop_count > 1:
                    # Decrease loop count and replay
                    self.loop_counts[chat_id] = loop_count - 1
                    await self.play_next(chat_id, client)
                    return
                elif loop_count == -1:  # Infinite loop
                    await self.play_next(chat_id, client)
                    return
            
            # Remove current track and play next
            if chat_id in self.queues and self.queues[chat_id]:
                self.queues[chat_id].pop(0)
                await self.db.remove_from_queue(chat_id)
            
            # Play next track
            await self.play_next(chat_id, client)
            
        except Exception as e:
            logger.error(f"Error handling track end: {e}")
    
    async def get_current_track(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get currently playing track"""
        return self.current_tracks.get(chat_id)
    
    async def is_playing(self, chat_id: int) -> bool:
        """Check if music is playing in chat"""
        return chat_id in self.active_calls and chat_id in self.current_tracks
    
    async def cleanup_chat(self, chat_id: int):
        """Cleanup chat data"""
        self.queues.pop(chat_id, None)
        self.current_tracks.pop(chat_id, None)
        self.loop_status.pop(chat_id, None)
        self.loop_counts.pop(chat_id, None)
        self.speeds.pop(chat_id, None)
        self.volumes.pop(chat_id, None)
        self.active_calls.pop(chat_id, None)
        
        # Clear database queue
        await self.db.clear_queue(chat_id)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get player statistics"""
        return {
            'active_calls': len(self.active_calls),
            'total_queues': len(self.queues),
            'total_tracks_queued': sum(len(queue) for queue in self.queues.values()),
            'currently_playing': len(self.current_tracks)
        }
    
    async def export_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        """Export queue to JSON format"""
        queue = self.queues.get(chat_id, [])
        return [{
            'title': track['title'],
            'url': track.get('webpage_url', ''),
            'duration': track['duration'],
            'requester': track['requester']['first_name'],
            'is_video': track.get('is_video', False)
        } for track in queue]
    
    async def import_queue(self, chat_id: int, queue_data: List[Dict[str, Any]], requester: User):
        """Import queue from JSON format"""
        try:
            for track_data in queue_data:
                await self.add_to_queue(
                    chat_id,
                    track_data.get('title', ''),
                    requester,
                    video=track_data.get('is_video', False)
                )
            return True
        except Exception as e:
            logger.error(f"Error importing queue: {e}")
            return False
