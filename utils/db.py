from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from models.base import Base

# Veritabanı dosya yolu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "finance.db")

# Klasör yoksa oluştur
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLite bağlantısı
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Engine oluştur
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session fabrikası oluştur
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Tüm tabloları oluşturur."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Tüm tabloları siler."""
    Base.metadata.drop_all(bind=engine)

def init_db():
    """Veritabanını başlatır ve tabloları oluşturur."""
    create_tables()
    print("Veritabanı tabloları oluşturuldu.")
    return True

@contextmanager
def db_session():
    """Veritabanı oturumu context manager'ı."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db():
    """Veritabanı oturumu oluşturur ve işlem sonunda kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 