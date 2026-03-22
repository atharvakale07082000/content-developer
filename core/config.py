from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017" # default
    database_name: str = "content_strategy"
    gemini_api_key: str = ""
    environment: str = "development"
    poll_interval_seconds: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
