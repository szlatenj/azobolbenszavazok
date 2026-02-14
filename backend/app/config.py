from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:changeme@192.168.1.159:5432/voting_guide"
    allowed_origins: list[str] = ["https://azobolbenszavazok.us", "http://localhost:8080"]
    signup_rate_limit: str = "5/hour"
    contact_rate_limit: str = "3/hour"
    helprequest_rate_limit: str = "5/hour"
    carpool_rate_limit: str = "5/hour"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
