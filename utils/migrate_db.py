import sqlite3
import os
from sqlalchemy import create_engine, inspect
from models.database import Base, get_db, engine, Transaction, Budget, FinancialGoal
import logging

# Loglama
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_db():
    """Veritabanı şemasını günceller ve eksik sütunları ekler."""
    logger.info("Veritabanı migration işlemi başlatılıyor...")
    
    # SQLite veritabanı yolu
    db_path = os.path.join(os.getcwd(), "finance.db")
    
    if not os.path.exists(db_path):
        logger.error(f"Veritabanı dosyası bulunamadı: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Mevcut sütunları kontrol et
        cursor.execute("PRAGMA table_info(transactions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"Mevcut sütunlar: {column_names}")
        
        # 'source' sütunu eksik mi kontrol et
        if 'source' not in column_names:
            logger.info("'source' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN source TEXT")
            logger.info("'source' sütunu başarıyla eklendi.")
        
        # 'external_id' sütunu eksik mi kontrol et
        if 'external_id' not in column_names:
            logger.info("'external_id' sütunu ekleniyor...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN external_id TEXT")
            logger.info("'external_id' sütunu başarıyla eklendi.")
        
        # Değişiklikleri kaydet
        conn.commit()
        logger.info("Veritabanı migration işlemi başarıyla tamamlandı.")
        return True
    
    except Exception as e:
        logger.error(f"Migration sırasında hata oluştu: {str(e)}")
        conn.rollback()
        return False
    
    finally:
        # Bağlantıyı kapat
        cursor.close()
        conn.close()

if __name__ == "__main__":
    success = migrate_db()
    if success:
        print("Veritabanı güncelleme işlemi başarıyla tamamlandı.")
    else:
        print("Veritabanı güncelleme işlemi başarısız oldu.") 