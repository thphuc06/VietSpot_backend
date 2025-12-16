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
    
    # Google Gemini (Legacy API Key - kept for fallback)
    GEMINI_API_KEY: Optional[str] = None
    
    # Google Cloud Credentials (JSON string for cloud deployment)
    GOOGLE_CREDENTIALS_JSON: Optional[str] = None
    
    # Vertex AI Configuration
    VERTEX_PROJECT_ID: str = "scrape-food1"
    VERTEX_LOCATION: str = "global"
    VERTEX_MODEL_ID: str = "gemini-2.0-flash-exp"
    
    # OpenWeather
    OPENWEATHER_API_KEY: Optional[str] = None
    
    # HuggingFace
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Search Configuration
    DEFAULT_NEARBY_RADIUS_KM: float = 10.0
    DEFAULT_NEARBY_RADIUS_KM_SHORT: float = 2.0
    TOP_N_SEMANTIC_RESULTS: int = 20
    TOP_K_FINAL_RESULTS: int = 10
    
    # Scoring Weights
    WEIGHT_SEMANTIC: float = 0.5
    WEIGHT_DISTANCE: float = 0.2
    WEIGHT_RATING: float = 0.2
    WEIGHT_POPULARITY: float = 0.1
    
    # Model Configuration
    EMBEDDING_MODEL: str = "dangvantuan/vietnamese-embedding"
    
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
