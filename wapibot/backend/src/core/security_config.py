"""Security configuration with environment-aware behavior.

Auto-hardens security settings in production environment.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class SecuritySettings(BaseSettings):
    """Security configuration with environment-aware auto-hardening."""

    # Environment
    environment: str = "development"
    debug: bool = True

    # JWT Authentication
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    # API Keys (encrypted in .env.txt)
    api_key_admin: str = ""
    api_key_brain: str = ""

    # Rate Limiting (requests per second)
    rate_limit_enabled: bool = False
    rate_limit_chat: int = 5
    rate_limit_admin: int = 2
    rate_limit_brain: int = 3
    rate_limit_qr: int = 8

    # Encryption
    field_encryption_key: str = ""
    secrets_encrypted: bool = False
    master_key_path: str = "./master.key"
    request_encryption_enabled: bool = False

    @field_validator('debug', mode='before')
    @classmethod
    def auto_disable_debug_in_prod(cls, v, info) -> bool:
        """Auto-disable debug in production."""
        if info.data.get('environment') == 'production':
            return False
        return v

    @field_validator('rate_limit_enabled', mode='before')
    @classmethod
    def auto_enable_rate_limit_in_prod(cls, v, info) -> bool:
        """Auto-enable rate limiting in production."""
        if info.data.get('environment') == 'production':
            return True
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    model_config = SettingsConfigDict(
        env_file=".env.txt",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env.txt
    )


# Global security settings instance
security_settings = SecuritySettings()
