from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EcoBite - Smart Meal Management"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./ecobite.db"

    class Config:
        case_sensitive = True

settings = Settings()