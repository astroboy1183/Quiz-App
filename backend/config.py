from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://quizmind:quizmind@localhost:5432/quizmind"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    llm_model: str = "gpt-4o"

    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    app_env: str = "development"
    backend_port: int = 8000
    frontend_port: int = 8501


settings = Settings()
