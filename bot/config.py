"""環境變數集中管理"""

import os

# LINE
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_BOT_ID = os.environ.get("LINE_BOT_ID", "")

# Travelpayouts
TRAVELPAYOUTS_TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN", "")
TP_MARKER = os.environ.get("TP_MARKER", "abroaduturn")

# Supabase（可選）
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Upstash Redis
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL", "")
UPSTASH_REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_TOKEN", "")
