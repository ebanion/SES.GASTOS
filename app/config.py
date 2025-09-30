import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SES_BASE_URL = os.getenv("SES_BASE_URL", "").rstrip("/")
    IDEMPOTENCY_HEADER = os.getenv("EVENT_IDEMPOTENCY_HEADER", "X-Idempotency-Key")
    ADMIN_KEY = os.getenv("ADMIN_KEY", "")
    TZ = os.getenv("TZ", "Europe/Madrid")

settings = Settings()
