from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean, LargeBinary, Text, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime, date
from enum import Enum as PyEnum

# Veritabanı URL'si
DATABASE_URL = "sqlite:///./finance.db"

# Engine oluşturma
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(Date, default=datetime.now().date())
    is_active = Column(Boolean, default=True)
    
    # İlişkiler
    transactions = relationship("Transaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    goals = relationship("FinancialGoal", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")
    bank_accounts = relationship("BankAccount", back_populates="user")

class TransactionType(str, PyEnum):
    """İşlem türleri."""
    INCOME = "income"  # Gelir
    EXPENSE = "expense"  # Gider
    TRANSFER = "transfer"  # Transfer

class RecurringType(str, PyEnum):
    """Tekrarlama türleri."""
    DAILY = "daily"  # Günlük
    WEEKLY = "weekly"  # Haftalık
    MONTHLY = "monthly"  # Aylık
    YEARLY = "yearly"  # Yıllık

class Transaction(Base):
    """İşlem modeli."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # İşlem bilgileri
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    
    # Tekrarlayan işlem bilgileri
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_type = Column(Enum(RecurringType), nullable=True)
    next_date = Column(DateTime, nullable=True)
    
    # Dış entegrasyon bilgileri
    source = Column(String(50), nullable=True)  # Örn: "manual", "import", "bank_api"
    external_id = Column(String(255), nullable=True)  # Dış sistem ID'si
    
    # İlişkiler
    user = relationship("User", back_populates="transactions")
    
    def to_dict(self):
        """İşlem bilgilerini sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "type": self.type.value if isinstance(self.type, TransactionType) else self.type,
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "is_recurring": self.is_recurring,
            "recurring_type": self.recurring_type.value if isinstance(self.recurring_type, RecurringType) else self.recurring_type,
            "next_date": self.next_date.isoformat() if self.next_date else None,
            "source": self.source,
            "external_id": self.external_id
        }
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.type})>"

class Budget(Base):
    """Bütçe modeli."""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Bütçe bilgileri
    name = Column(String(100), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=False)
    
    # Notlar ve renk
    notes = Column(Text, nullable=True)
    color = Column(String(20), nullable=True)  # HEX color
    
    # İlişkiler
    user = relationship("User", back_populates="budgets")
    
    def to_dict(self):
        """Bütçe bilgilerini sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "category": self.category,
            "amount": self.amount,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "notes": self.notes,
            "color": self.color
        }
    
    def __repr__(self):
        return f"<Budget(id={self.id}, user_id={self.user_id}, name={self.name}, amount={self.amount})>"

class FinancialGoal(Base):
    """Finansal hedef modeli."""
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Hedef bilgileri
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0, nullable=False)
    start_date = Column(Date, nullable=False, default=date.today)
    deadline = Column(Date, nullable=False)
    
    # Tamamlanma durumu
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_date = Column(Date, nullable=True)
    
    # Notlar ve öncelik
    notes = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)  # 1: Düşük, 2: Orta, 3: Yüksek
    
    # İlişkiler
    user = relationship("User", back_populates="goals")
    
    def to_dict(self):
        """Hedef bilgilerini sözlük olarak döndürür."""
        progress = (self.current_amount / self.target_amount) * 100 if self.target_amount > 0 else 0
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "progress": round(progress, 2),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "is_completed": self.is_completed,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None,
            "notes": self.notes,
            "priority": self.priority
        }
    
    def __repr__(self):
        return f"<FinancialGoal(id={self.id}, user_id={self.user_id}, name={self.name}, progress={self.current_amount/self.target_amount:.2%})>"

class Receipt(Base):
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    image = Column(LargeBinary)  # Makbuz görüntüsü
    ocr_text = Column(Text)  # OCR ile çıkarılan metin
    amount = Column(Float, nullable=True)  # Tespit edilen tutar
    date = Column(Date, nullable=True)  # Tespit edilen tarih
    category = Column(String, nullable=True)  # Tespit edilen kategori
    created_at = Column(DateTime, default=datetime.now)
    processed = Column(Boolean, default=False)  # İşlenme durumu
    reviewed = Column(Boolean, default=False)  # Kullanıcı tarafından onaylanma durumu
    
    # İlişkiler
    user = relationship("User", back_populates="receipts")

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bank_name = Column(String)  # Banka adı
    account_number = Column(String)  # Hesap numarası (son 4 hane veya masked)
    account_name = Column(String)  # Hesap adı (örn. "Ana Hesap", "Maaş Hesabı")
    account_type = Column(String, nullable=True)  # Hesap tipi (vadesiz, vadeli, kredi kartı)
    access_token = Column(String)  # API erişim token'ı (şifrelenmiş)
    last_sync = Column(DateTime)  # Son senkronizasyon zamanı
    is_active = Column(Boolean, default=True)  # Hesap aktif mi
    
    # İlişkiler
    user = relationship("User", back_populates="bank_accounts")

# Veritabanı tablolarını oluştur
def init_db():
    Base.metadata.create_all(bind=engine)

# Veritabanı oturumu oluştur
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 