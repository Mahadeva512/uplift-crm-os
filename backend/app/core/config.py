from dotenv import load_dotenv
load_dotenv()
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ==========================================================
    # 🔐 Security Config
    # ==========================================================
    SECRET_KEY: str = "upliftcrm_super_secret_key_2025"
    ALGORITHM: str = "HS256"

    # ==========================================================
    # 🗄️ Database Config
    # ==========================================================
    DATABASE_URL: str = (
        "postgresql+psycopg://uplift:uplift123@localhost:5432/uplift"
    )

    # ==========================================================
    # ⚙️ App Metadata
    # ==========================================================
    PROJECT_NAME: str = "Uplift CRM vPro"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API backend for Uplift CRM vPro"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
