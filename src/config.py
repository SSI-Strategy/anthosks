"""Application configuration management."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from typing import Optional


class Config(BaseSettings):
    """Application configuration from environment variables."""

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = Field(
        ...,
        description="Azure OpenAI endpoint URL"
    )
    AZURE_OPENAI_DEPLOYMENT: str = Field(
        default="gpt-5-chat-deployment",
        description="Deployment name"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-08-01-preview",
        description="API version"
    )
    AZURE_OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="API key (optional, falls back to Azure CLI auth)"
    )

    # Local Storage
    INPUT_PATH: Path = Field(default=Path("./data/input"))
    OUTPUT_PATH: Path = Field(default=Path("./data/output"))
    DATABASE_PATH: Path = Field(default=Path("./data/reports.db"))
    CACHE_PATH: Optional[Path] = Field(default=Path("./data/cache"))

    # Database Connection (PostgreSQL - takes precedence over DATABASE_PATH if set)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection string (postgresql://user:password@host:port/database)"
    )

    # Application Settings
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_CACHE: bool = Field(default=True)
    MAX_RETRIES: int = Field(default=3)
    TIMEOUT_SECONDS: int = Field(default=120)

    # Extraction Parameters
    LLM_TEMPERATURE: float = Field(default=0.0, ge=0.0, le=2.0)
    LLM_MAX_TOKENS: int = Field(default=16000)  # Increased for full report extraction
    CONFIDENCE_THRESHOLD: float = Field(default=0.7, ge=0.0, le=1.0)

    # Analytics Parameters
    ANALYTICS_QUERY_LIMIT: int = Field(default=10000, description="Maximum number of reports to query for analytics")

    # Azure AD / EntraID Authentication
    AZURE_AD_ENABLED: bool = Field(default=True, description="Enable Azure AD authentication")
    AZURE_AD_TENANT_ID: Optional[str] = Field(default=None, description="Azure AD Tenant ID")
    AZURE_AD_CLIENT_ID: Optional[str] = Field(default=None, description="Azure AD Application (Client) ID for API")
    AZURE_AD_AUDIENCE: Optional[str] = Field(default=None, description="Expected audience in JWT tokens (api://<client-id>)")
    AZURE_AD_ALLOWED_GROUPS: Optional[str] = Field(
        default=None,
        description="Comma-separated list of Azure AD group object IDs for authorization"
    )

    # CORS Configuration
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @field_validator('INPUT_PATH', 'OUTPUT_PATH', 'DATABASE_PATH', 'CACHE_PATH')
    @classmethod
    def ensure_path_exists(cls, v: Optional[Path]) -> Optional[Path]:
        """Create directories if they don't exist."""
        if v:
            v = Path(v)
            v.parent.mkdir(parents=True, exist_ok=True)
            if not v.suffix:  # It's a directory
                v.mkdir(parents=True, exist_ok=True)
        return v


# Global config instance
config = Config()
