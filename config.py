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

# Wake word
WAKE_WORD = "土豆"

# NetEase API
NETEASE_API_BASE = "http://127.0.0.1:3000"

# Volume (0.0 ~ 1.0)
VOLUME = 1.0

# Recording params
RECORD_SECONDS = 2.0
WAKE_RECORD_SECONDS = 1.5
COMMAND_TIMEOUT = 4

# VAD
VAD_THRESHOLD = 2500
MIC_GAIN = 3000
