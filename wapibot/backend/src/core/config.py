"""Application configuration with Pydantic Settings.

Supports Ollama, OpenRouter, and OpenAI providers.
Switch provider by changing PRIMARY_LLM_PROVIDER in .env.txt
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Literal

# Find .env.txt at project root (wapibot/)
# Path: backend/src/core/config.py -> ../../.. = backend -> ../.. = wapibot
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env.txt"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),  # Absolute path to project root .env.txt
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "WapiBot Backend V2"
    app_version: str = "2.0.0"
    debug: bool = True
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./conversations.db"
    checkpoint_db_path: str = "./checkpoints.db"

    # LLM Provider Selection
    primary_llm_provider: Literal["ollama", "openrouter", "openai"] = "ollama"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout: float = 30.0
    ollama_max_retries: int = 2

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_fallback_model: str = "anthropic/claude-3.5-haiku"
    openrouter_app_name: str = "WapiBot"
    openrouter_site_url: str = ""
    openrouter_timeout: float = 60.0

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout: float = 30.0

    # DSPy
    dspy_cache_dir: str = "./dspy_cache"
    dspy_max_tokens: int = 2000
    dspy_temperature: float = 0.7

    # Extraction Timeouts (seconds) - Hardware dependent, adjust for your GPU
    extraction_timeout_normal: float = 90.0      # Normal extraction (10-90s typical)
    extraction_timeout_complex: float = 180.0    # Complex modules or first load
    extraction_timeout_warmup: float = 180.0     # Warmup queries (model loading time)

    # Confidence Score Thresholds
    confidence_low: float = 0.5                  # Low confidence extraction
    confidence_medium: float = 0.7               # Medium confidence (regex fallback)
    confidence_high: float = 0.9                 # High confidence (DSPy extraction)

    # Warmup Configuration
    warmup_cooldown_seconds: int = 300           # Hot reload protection
    warmup_idle_threshold_seconds: int = 300     # Trigger warmup after idle
    warmup_idle_check_interval: int = 60         # Check idle status interval

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Feature Flags
    enable_sentiment_analysis: bool = True
    enable_intent_classification: bool = True

    # Frappe Backend Configuration
    frappe_base_url: str = "https://yawlit.duckdns.org"
    frappe_api_key: str = ""
    frappe_api_secret: str = ""

    # WAPI Configuration
    wapi_base_url: str = "https://wapi.in.net"
    wapi_vendor_uid: str = ""  # Vendor UID for WAPI API
    wapi_bearer_token: str = ""  # Bearer token for WAPI API authentication
    wapi_from_phone_number_id: str = ""  # Optional: Default phone number ID
    wapi_webhook_secret: str = ""  # HMAC secret for webhook signature validation

    @field_validator(
        'frappe_api_key',
        'frappe_api_secret',
        'wapi_webhook_secret',
        'wapi_vendor_uid',
        'wapi_bearer_token'
    )
    @classmethod
    def validate_production_secrets(cls, v: str, info) -> str:
        """Validate that required secrets are set in production."""
        # Get environment value from the values being validated
        environment = info.data.get('environment', 'development')
        field_name = info.field_name

        if environment == 'production' and not v:
            raise ValueError(
                f'{field_name} must be set in production environment. '
                f'Add {field_name.upper()} to .env.txt'
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
