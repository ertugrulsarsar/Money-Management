from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLite veritabanı dosya yolu
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'finance.db')

# Klasör yoksa oluştur
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite bağlantısı
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine oluştur
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session fabrikası oluştur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Temel sınıf
Base = declarative_base()

def get_db():
    """Veritabanı oturumu oluşturur ve işlem sonunda kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 