from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = "VietSpot API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database (Supabase PostgreSQL) - optional nếu chỉ dùng Supabase client
    DATABASE_URL: Optional[str] = None
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET: str = "images"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    # API
    API_V1_PREFIX: str = "/api"
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate database URL format."""
        if v is None:
            return v
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'"
            )
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
