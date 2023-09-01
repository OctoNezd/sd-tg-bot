import os
import json
from dotenv import load_dotenv as _load_dotenv

_load_dotenv()

TG_BOT_API_TOKEN = os.environ["TG_BOT_API_TOKEN"]
SD_WEBUI_URL = os.environ["SD_WEBUI_URL"]
CHAT_WHITELIST = os.environ.get("CHAT_WHITELIST", None)
RANDOM_PROMPT_PERCENTAGE = int(os.environ.get("RANDOM_PROMPT_PERCENTAGE", 5))
GENERATION_CONFIG = json.loads(os.environ.get("GENERATION_CONFIG", "{}"))
