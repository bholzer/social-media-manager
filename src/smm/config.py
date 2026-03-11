from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://smm:smm@localhost:5434/smm"
    test_database_url: str = "postgresql+asyncpg://smm:smm@localhost:5433/smm_test"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    base_url: str = "http://localhost:8000"

    # Facebook OAuth
    facebook_app_id: str = ""
    facebook_app_secret: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
