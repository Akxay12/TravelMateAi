import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get absolute path of backend/.env relative to this file
config_dir = os.path.dirname(os.path.abspath(__file__))
env_file_path = os.path.normpath(os.path.join(config_dir, ".env"))

# Clear any pre-existing environment variables that could override backend/.env
if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]
if "GOOGLE_API_KEY" in os.environ:
    del os.environ["GOOGLE_API_KEY"]

# Load environment variables, ensuring they override the current process environment
load_dotenv(dotenv_path=env_file_path, override=True)


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # Database (SQLite by default)
    database_url: str = "sqlite+aiosqlite:///./travelmate.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Overpass API
    overpass_url: str = "https://overpass-api.de/api/interpreter"

    # Nominatim
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"


settings = Settings()

