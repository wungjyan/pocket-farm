from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Pocket Farm API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    database_url: str
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    app_timezone: str = "Asia/Shanghai"
    test_login_enabled: bool = False
    test_login_code: str = "8888"
    # AI endpoint is optional until the AI Tab backend is implemented. Keep all
    # credentials server-side; the miniapp must never receive these values.
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    ai_request_timeout_seconds: Annotated[int, Field(ge=1, le=120)] = 30
    ai_daily_turn_limit: Annotated[int, Field(ge=1, le=1000)] = 20
    ai_max_message_chars: Annotated[int, Field(ge=1, le=10_000)] = 1000
    ai_max_history_turns: Annotated[int, Field(ge=0, le=50)] = 8
    ai_max_tool_calls_per_turn: Annotated[int, Field(ge=1, le=20)] = 6
    ai_max_output_tokens: Annotated[int, Field(ge=1, le=4096)] = 800
    ai_notice_version: str = "v1"
    ai_user_id_hash_key: SecretStr | None = None


settings = Settings()
