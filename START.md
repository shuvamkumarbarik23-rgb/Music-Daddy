# Quick start

1. Install Python 3.11 and FFmpeg.
2. Install packages: `pip install -r requirements.txt`
3. Set the environment variables listed in `.env.example`.
4. Run: `python main.py`
5. Start a voice chat in a Telegram group and send `/radio`.
6. Send `/stopradio` to stop.

For Render, deploy as a **Background Worker**, not a web service. Add secrets in Render Environment settings; do not commit them.
