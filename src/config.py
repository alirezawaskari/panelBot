import os
from dotenv import load_dotenv

# Load environment variables from env.txt
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Log and report channels
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
REPORT_CHANNEL_ID = int(os.getenv("REPORT_CHANNEL_ID"))

# Super admin ID
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID"))

# Database URL
DATABASE_URL = "sqlite:///database/bot.db"
