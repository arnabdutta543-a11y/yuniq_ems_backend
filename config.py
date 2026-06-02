import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App General Settings
    APP_NAME: str = "YuniQ Employee Portal API"
    DEBUG: bool = True
    
    # Supabase Settings
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY", "")
    
    # Redis Cloud Settings
    REDIS_HOST: Optional[str] = os.getenv("REDIS_HOST", "")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", "")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "")
    
    # SerpAPI Settings
    SERPAPI_KEY: Optional[str] = os.getenv("SERPAPI_KEY", "")
    
    # Email SMTP Settings (Gmail)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", "")
    
    # Mock Mode configuration (force or fallback)
    FORCE_MOCK: bool = os.getenv("FORCE_MOCK", "true").lower() == "true"
    
    @property
    def is_mock_mode(self) -> bool:
        if self.FORCE_MOCK:
            return True
        # If any essential credential is empty, run in mock mode
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            return True
        return False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
