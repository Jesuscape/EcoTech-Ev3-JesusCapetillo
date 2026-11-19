import os
from pathlib import Path
from dotenv import load_dotenv

# Carga variables de entorno desde el archivo .env si existe
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Centraliza rutas y configuraciones seguras desde variables de entorno."""

    DATA_DIR = BASE_DIR / "data"
    USERS_FILE = DATA_DIR / "users.json"
    WEATHER_HISTORY_FILE = DATA_DIR / "clima_historial.json"
    PAYMENTS_HISTORY_FILE = DATA_DIR / "pagos_historial.json"

    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    CURRENCY_API_URL = "https://open.er-api.com/v6/latest"

    # Claves opcionales leídas de forma segura (nunca hardcodeadas)
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
    CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY", "").strip()

    @classmethod
    def get_timeout(cls) -> int:
        try:
            timeout = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
            return timeout if 1 <= timeout <= 30 else 10
        except ValueError:
            return 10

    @classmethod
    def get_max_login_attempts(cls) -> int:
        try:
            attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
            return attempts if 1 <= attempts <= 5 else 3
        except ValueError:
            return 3
