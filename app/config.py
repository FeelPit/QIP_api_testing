import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - Heroku автоматически предоставляет DATABASE_URL
    database_url: str = "sqlite:///./quantum_insight.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Telegram
    telegram_bot_token: str = ""
    
    # App Settings
    debug: bool = False  # False для продакшена
    allowed_hosts: str = "localhost,127.0.0.1"
    cors_origins: str = "http://localhost:3000,https://web.telegram.org"
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 