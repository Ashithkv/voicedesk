"""
Central place for reading configuration from environment variables.

Nothing here is hardcoded — every credential comes from the environment
(populated from a .env file in local dev, or real env vars in prod).
"""
import os
from dotenv import load_dotenv

# Load variables from a .env file if one exists (local dev convenience).
load_dotenv()


class Settings:
    # VAPI.ai
    VAPI_API_KEY: str = os.getenv("VAPI_API_KEY", "")
    VAPI_ASSISTANT_ID: str = os.getenv("VAPI_ASSISTANT_ID", "")
    VAPI_WEBHOOK_SECRET: str = os.getenv("VAPI_WEBHOOK_SECRET", "")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Twilio (only needed if you want VoiceDesk to also originate/receive
    # calls directly through Twilio rather than through VAPI's own number)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./voicedesk.db")

    # App
    ENV: str = os.getenv("ENV", "development")


settings = Settings()
