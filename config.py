import os
from typing import Dict, Any

# Temel konfigürasyon ayarları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Klasörleri oluştur
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Database ayarları
DB_PATH = os.path.join(DATA_DIR, "finance.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SMTP Ayarları
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
EMAIL_SENDER = SMTP_USERNAME

# Uygulama ayarları
APP_NAME = "Kişisel Finans"
APP_VERSION = "1.0.0"
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

# Varsayılan dil
DEFAULT_LANGUAGE = "tr"

# Para birimleri
CURRENCIES = ["TRY", "USD", "EUR", "GBP"]

# Tarih formatları
DATE_FORMATS = ["DD.MM.YYYY", "YYYY-MM-DD", "MM/DD/YYYY"]

# Tema seçenekleri
THEMES = ["light", "dark", "system"]

# Tüm ayarları içeren sözlük
settings: Dict[str, Any] = {
    "app_name": APP_NAME,
    "app_version": APP_VERSION,
    "debug": DEBUG,
    "base_dir": BASE_DIR,
    "data_dir": DATA_DIR,
    "log_dir": LOG_DIR,
    "db_path": DB_PATH,
    "database_url": DATABASE_URL,
    "smtp": {
        "server": SMTP_SERVER,
        "port": SMTP_PORT,
        "username": SMTP_USERNAME,
        "password": SMTP_PASSWORD,
        "email_sender": EMAIL_SENDER,
    },
    "languages": {
        "default": DEFAULT_LANGUAGE,
        "available": ["tr", "en"]
    },
    "currencies": CURRENCIES,
    "date_formats": DATE_FORMATS,
    "themes": THEMES
} 