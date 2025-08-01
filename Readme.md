# 🤖 Telegram Music Bot

A powerful, feature-rich Telegram bot for playing music in voice calls, queue management, speed control, and multi-platform support.

---

## ✨ Features

### 🎧 Music Features
- **Play Music**: Stream songs from YouTube directly in Telegram voice chats.
- **Video Support**: Play videos (with audio) in voice chats.
- **Queue Management**: Add, remove, shuffle, and manage your song queue.
- **Speed Control**: Adjust playback speed (0.5x–2.0x).
- **Loop Tracks**: Loop songs with custom repeat counts.
- **Seek Controls**: Seek forward/backward in tracks.
- **Volume Control**: Set playback volume.
- **Download**: Download MP3/MP4 files from YouTube.

### 👑 Admin Features
- **User Authorization**: Authorize users per chat.
- **Global Bans**: Ban users across all chats.
- **Chat Management**: Blacklist/whitelist chats.
- **Broadcast**: Send messages to all users/chats.
- **Maintenance Mode**: Restrict bot usage to sudo users.

### 📊 Monitoring
- **Web Dashboard**: Real-time status monitoring.
- **System Stats**: CPU, memory, disk usage.
- **Bot Statistics**: Users, chats, active calls.
- **Health Checks**: Automated endpoints for uptime.
- **Logging**: Activity logs.

### 🔧 Technical Features
- **Multi-Platform**: Deploy on Heroku, Render, Railway, VPS.
- **Database**: SQLite (async).
- **Keep Alive**: Automatic uptime monitoring.
- **Rate Limiting**: Prevent spam/abuse.
- **Error Handling**: Robust recovery.
- **Assistant Support**: (Optional) Userbot for performance.

---

## 🚀 Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

---

## 🛠️ Manual Installation

### Prerequisites
- Python 3.8+
- FFmpeg
- Git

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/telegram-music-bot.git
cd telegram-music-bot

# Run install script (Linux/macOS)
chmod +x install.sh
./install.sh
```

Manual setup (Windows/alternative):
```bash
python -m venv venv
# Activate venv
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

Configure environment:
```bash
cp .env.example .env
# Edit .env with your data
```

Run the bot:
```bash
python run.py
```

---

## ⚙️ Configuration

### Required Environment Variables

| Variable         | Description                   | Example                   |
|------------------|------------------------------|---------------------------|
| `BOT_TOKEN`      | Bot token from @BotFather     | `1234567890:ABCdef...`    |
| `API_ID`         | API ID from my.telegram.org   | `12345`                   |
| `API_HASH`       | API Hash from my.telegram.org | `abcdef123456...`         |
| `SUDO_USERS`     | Owner user IDs, comma-separated | `123456789,987654321`   |

### Optional

| Variable              | Description               | Default                     |
|-----------------------|--------------------------|-----------------------------|
| `SESSION_STRING`      | Pyrogram assistant string| None                        |
| `DATABASE_URL`        | Database URL             | `sqlite:///music_bot.db`    |
| `SPOTIFY_CLIENT_ID`   | Spotify API client ID    | None                        |
| `SPOTIFY_CLIENT_SECRET` | Spotify client secret  | None                        |
| `PORT`                | Web server port          | `8000`                      |

---

## 📱 Bot Commands

### 🎵 Music
- `/play <song>` — Play music
- `/vplay <song>` — Play video+audio
- `/song <song>` — Download MP3/MP4
- `/queue` — Show queue
- `/shuffle` — Shuffle queue
- `/stop` — Stop playback
- `/loop [count]` — Loop track(s)

### ⚡ Control
- `/speed <0.5-2.0>` — Playback speed
- `/seek <seconds>` — Seek forward
- `/seekback <seconds>` — Seek backward
- `/volume <0-200>` — Set volume

### 👑 Admin
- `/auth <user>` — Authorize user
- `/unauth <user>` — Remove authorization
- `/authusers` — List authorized users

### 🔧 Sudo
- `/ping` — Bot status
- `/stats` — Bot statistics
- `/gban <user>` — Global ban
- `/broadcast <msg>` — Broadcast
- `/maintenance` — Toggle maintenance mode

---

## 🌐 Web Dashboard

Access at your deployment URL:

- Status: `/`
- Health: `/health`
- Metrics: `/metrics`
- Logs: `/logs`

---

## 🔧 Advanced Configuration

### Assistant Account

Generate session string:
```python
from pyrogram import Client

api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"

with Client("assistant", api_id, api_hash) as app:
    print(app.export_session_string())
```
Add the string to `SESSION_STRING` in `.env`.

### Database

- **SQLite** (default): `sqlite:///music_bot.db`
- **PostgreSQL**: `postgresql://user:pass@host:port/db`
- **MySQL**: `mysql://user:pass@host:port/db`

### Spotify

1. Create app at [Spotify Developer Dashboard](https://developer.spotify.com/)
2. Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`

---

## 🐳 Docker Deployment

Build and run:
```bash
docker build -t telegram-music-bot .
docker run -d \
  --name music-bot \
  --env-file .env \
  -p 8000:8000 \
  telegram-music-bot
```

With Docker Compose:
```bash
docker-compose up -d
```

---

## 📊 Monitoring

### Endpoints
- `GET /health` — JSON health
- `GET /ping` — Ping response
- `GET /metrics` — Prometheus metrics

### Log Levels
- INFO — General info
- WARNING — Issues
- ERROR — Exceptions
- DEBUG — Debug details

---

## 🤝 Contributing

1. Fork the repo
2. Create branch (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- [Pyrogram](https://github.com/pyrogram/pyrogram)
- [PyTgCalls](https://github.com/pytgcalls/pytgcalls)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

---

## 🐛 Troubleshooting

### Common Issues

**Bot not responding**
- Check bot token
- Verify API credentials
- Check network

**Voice calls not working**
- Ensure FFmpeg is installed
- Check voice chat permissions
- Verify assistant setup

**Deployment issues**
- Check environment variables
- Python version (3.8+)
- Check build logs

### Get Help

- 📖 Read docs
- 🐛 Check issues
- 💬 Create new issue
- 📧 Contact maintainers

---

## 📈 Roadmap

- [ ] Spotify direct streaming
- [ ] Playlist import/export
- [ ] Audio effects
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Voice commands
- [ ] AI music recommendations
