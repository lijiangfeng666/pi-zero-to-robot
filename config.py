""""
Configuration
Loads sensitive keys from .env file. Create .env from .env.example.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

# Baidu Speech (must set in .env)
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID", "")
BAIDU_API_KEY = os.getenv("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")

# DeepSeek AI (must set in .env)
DEEPSEEK_KEY = os.getenv("DEEPSEEK_KEY", "")

# Microphone
MIC_INDEX = -1

# Wake word (optional in .env)
WAKE_WORD = os.getenv("WAKE_WORD", "土豆")

# NetEase API
NETEASE_API_BASE = os.getenv("NETEASE_API_BASE", "http://127.0.0.1:3000")

# Volume (0.0 ~ 1.0, optional in .env)
VOLUME = float(os.getenv("VOLUME", "1.0"))

# Recording params (optional in .env)
RECORD_SECONDS = float(os.getenv("RECORD_SECONDS", "2.0"))
WAKE_RECORD_SECONDS = float(os.getenv("WAKE_RECORD_SECONDS", "1.5"))
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "4"))

# VAD (optional in .env)
VAD_THRESHOLD = int(os.getenv("VAD_THRESHOLD", "2500"))
MIC_GAIN = int(os.getenv("MIC_GAIN", "3000"))
