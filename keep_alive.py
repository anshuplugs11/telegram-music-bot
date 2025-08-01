#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
from threading import Thread
from flask import Flask, jsonify, render_template_string
from config import Config
import time
import psutil
import os

logger = logging.getLogger(__name__)

# Flask app for health checks and status
app = Flask(__name__)

# HTML template for status page
STATUS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Music Bot Status</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-card h3 {
            margin: 0 0 15px 0;
            color: #fff;
            font-size: 1.2em;
        }
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .status-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }
        .status-label {
            font-weight: bold;
        }
        .status-value {
            color: #a8e6cf;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #a8e6cf, #dcedc1);
            transition: width 0.3s ease;
        }
        .online {
            color: #a8e6cf;
            font-weight: bold;
        }
        .offline {
            color: #ffaaa5;
            font-weight: bold;
        }
        .refresh-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            transition: transform 0.2s;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }
        @media (max-width: 600px) {
            .container {
                padding: 15px;
                margin: 10px;
            }
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
    <script>
        function refreshStatus() {
            location.reload();
        }
        
        // Auto refresh every 30 seconds
        setInterval(refreshStatus, 30000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Music Bot Status</h1>
            <p>Real-time monitoring dashboard</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>🤖 Bot Status</h3>
                <div class="status-item">
                    <span class="status-label">Status:</span>
                    <span class="status-value {{ 'online' if bot_online else 'offline' }}">
                        {{ 'Online' if bot_online else 'Offline' }}
                    </span>
                </div>
                <div class="status-item">
                    <span class="status-label">Uptime:</span>
                    <span class="status-value">{{ uptime }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Total Chats:</span>
                    <span class="status-value">{{ total_chats }}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>💻 System Resources</h3>
                <div class="status-item">
                    <span class="status-label">CPU Usage:</span>
                    <span class="status-value">{{ cpu_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ cpu_percent }}%"></div>
                </div>
                
                <div class="status-item">
                    <span class="status-label">Memory Usage:</span>
                    <span class="status-value">{{ memory_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ memory_percent }}%"></div>
                </div>
                
                <div class="status-item">
                    <span class="status-label">Disk Usage:</span>
                    <span class="status-value">{{ disk_percent }}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ disk_percent }}%"></div>
                </div>
            </div>
            
            <div class="status-card">
                <h3>🎵 Music Player</h3>
                <div class="status-item">
                    <span class="status-label">Active Calls:</span>
                    <span class="status-value">{{ active_calls }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Queued Tracks:</span>
                    <span class="status-value">{{ queued_tracks }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Currently Playing:</span>
                    <span class="status-value">{{ currently_playing }}</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>📊 Statistics</h3>
                <div class="status-item">
                    <span class="status-label">Version:</span>
                    <span class="status-value">v2.0.0</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Platform:</span>
                    <span class="status-value">{{ platform }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Python:</span>
                    <span class="status-value">{{ python_version }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Last Updated:</span>
                    <span class="status-value">{{ last_updated }}</span>
                </div>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshStatus()">🔄 Refresh</button>
            <button class="refresh-btn" onclick="window.open('/health', '_blank')">📈 Health Check</button>
        </div>
        
        <div class="footer">
            <p>🎵 Telegram Music Bot - Keeping your music alive 24/7</p>
            <p>Deployed on Render • Auto-refresh every 30 seconds</p>
        </div>
    </div>
</body>
</html>
"""

class KeepAlive:
    """Keep the bot alive on Render and provide status monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.bot_instance = None
        self.db_instance = None
        
    def set_bot_instance(self, bot, db):
        """Set bot and database instances for monitoring"""
        self.bot_instance = bot
        self.db_instance = db
    
    def get_uptime(self):
        """Get bot uptime in human readable format"""
        uptime_seconds = int(time.time() - self.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    
    async def get_bot_stats(self):
        """Get bot statistics"""
        try:
            if self.db_instance:
                total_users = await self.db_instance.get_total_users()
                total_chats = await self.db_instance.get_total_chats()
            else:
                total_users = 0
                total_chats = 0
            
            if self.bot_instance and hasattr(self.bot_instance, 'music_player'):
                player_stats = await self.bot_instance.music_player.get_stats()
                active_calls = player_stats.get('active_calls', 0)
                queued_tracks = player_stats.get('total_tracks_queued', 0)
                currently_playing = player_stats.get('currently_playing', 0)
            else:
                active_calls = 0
                queued_tracks = 0
                currently_playing = 0
            
            return {
                'total_users': total_users,
                'total_chats': total_chats,
                'active_calls': active_calls,
                'queued_tracks': queued_tracks,
                'currently_playing': currently_playing
            }
            
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            return {
                'total_users': 0,
                'total_chats': 0,
                'active_calls': 0,
                'queued_tracks': 0,
                'currently_playing': 0
            }
    
    def get_system_stats(self):
        """Get system statistics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': round(cpu_percent, 1),
                'memory_percent': round(memory.percent, 1),
                'disk_percent': round(disk.percent, 1),
                'memory_used_mb': memory.used // 1024 // 1024,
                'memory_total_mb': memory.total // 1024 // 1024,
                'disk_used_gb': disk.used // 1024 // 1024 // 1024,
                'disk_total_gb': disk.total // 1024 // 1024 // 1024,
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'memory_used_mb': 0,
                'memory_total_mb': 0,
                'disk_used_gb': 0,
                'disk_total_gb': 0,
            }

# Global keep alive instance
keep_alive = KeepAlive()

@app.route('/')
async def status_page():
    """Main status page"""
    try:
        import platform
        import sys
        
        bot_stats = await keep_alive.get_bot_stats()
        system_stats = keep_alive.get_system_stats()
        
        data = {
            'bot_online': True,  # If this page loads, bot is online
            'uptime': keep_alive.get_uptime(),
            'last_updated': time.strftime('%H:%M:%S'),
            'platform': platform.system(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            **bot_stats,
            **system_stats
        }
        
        return render_template_string(STATUS_TEMPLATE, **data)
        
    except Exception as e:
        logger.error(f"Error in status page: {e}")
        return render_template_string(STATUS_TEMPLATE, 
                                    bot_online=False, uptime="Error", 
                                    last_updated=time.strftime('%H:%M:%S'),
                                    **{k: 0 for k in ['total_users', 'total_chats', 'active_calls', 
                                                     'queued_tracks', 'currently_playing', 'cpu_percent',
                                                     'memory_percent', 'disk_percent']},
                                    platform="Unknown", python_version="Unknown")

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring services"""
    try:
        system_stats = keep_alive.get_system_stats()
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'uptime_seconds': int(time.time() - keep_alive.start_time),
            'uptime_human': keep_alive.get_uptime(),
            'system': system_stats,
            'checks': {
                'cpu_ok': system_stats['cpu_percent'] < 90,
                'memory_ok': system_stats['memory_percent'] < 90,
                'disk_ok': system_stats['disk_percent'] < 90,
            }
        }
        
        # Determine overall health status
        all_checks_ok = all(health_data['checks'].values())
        health_data['status'] = 'healthy' if all_checks_ok else 'degraded'
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({
        'status': 'pong',
        'timestamp': time.time(),
        'uptime': keep_alive.get_uptime()
    })

@app.route('/metrics')
def metrics():
    """Metrics endpoint in Prometheus format"""
    try:
        system_stats = keep_alive.get_system_stats()
        
        metrics_text = f"""# HELP bot_uptime_seconds Bot uptime in seconds
# TYPE bot_uptime_seconds counter
bot_uptime_seconds {int(time.time() - keep_alive.start_time)}

# HELP system_cpu_percent CPU usage percentage
# TYPE system_cpu_percent gauge
system_cpu_percent {system_stats['cpu_percent']}

# HELP system_memory_percent Memory usage percentage  
# TYPE system_memory_percent gauge
system_memory_percent {system_stats['memory_percent']}

# HELP system_disk_percent Disk usage percentage
# TYPE system_disk_percent gauge
system_disk_percent {system_stats['disk_percent']}
"""
        
        return metrics_text, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return "Error generating metrics", 500

@app.route('/logs')
def view_logs():
    """View recent logs (basic implementation)"""
    try:
        log_file = "bot.log"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Get last 100 lines
                recent_logs = ''.join(lines[-100:])
                
            return f"""
            <html>
            <head><title>Bot Logs</title></head>
            <body style="font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px;">
            <h2>Recent Bot Logs (Last 100 lines)</h2>
            <pre style="background: #000; padding: 15px; border-radius: 5px; overflow-x: auto;">
{recent_logs}
            </pre>
            <br>
            <a href="/" style="color: #00ff00;">← Back to Status</a>
            </body>
            </html>
            """
        else:
            return "<h2>No log file found</h2><a href='/'>← Back</a>"
            
    except Exception as e:
        return f"<h2>Error reading logs: {e}</h2><a href='/'>← Back</a>"

def run_flask():
    """Run Flask app in a separate thread"""
    try:
        port = int(os.environ.get('PORT', Config.PORT))
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Flask app error: {e}")

def start_keep_alive(bot_instance=None, db_instance=None):
    """Start the keep alive server"""
    if bot_instance:
        keep_alive.set_bot_instance(bot_instance, db_instance)
    
    # Start Flask in a separate thread
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()
    
    logger.info(f"Keep alive server started on port {os.environ.get('PORT', Config.PORT)}")
    return server_thread

# Uptime monitoring function
async def uptime_monitor():
    """Monitor uptime and send alerts if needed"""
    while True:
        try:
            # Check system health
            system_stats = keep_alive.get_system_stats()
            
            # Log system stats every hour
            if int(time.time()) % 3600 == 0:
                logger.info(f"System Stats - CPU: {system_stats['cpu_percent']}%, "
                          f"Memory: {system_stats['memory_percent']}%, "
                          f"Disk: {system_stats['disk_percent']}%")
            
            # Alert if resources are too high
            if system_stats['cpu_percent'] > 90:
                logger.warning(f"High CPU usage: {system_stats['cpu_percent']}%")
            
            if system_stats['memory_percent'] > 90:
                logger.warning(f"High memory usage: {system_stats['memory_percent']}%")
            
            if system_stats['disk_percent'] > 90:
                logger.warning(f"High disk usage: {system_stats['disk_percent']}%")
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Error in uptime monitor: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    # Test the keep alive server
    print("Starting keep alive server...")
    start_keep_alive()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down keep alive server...")
 Users:</span>
                    <span class="status-value">{{ total_users }}</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Total
