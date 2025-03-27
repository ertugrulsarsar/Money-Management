from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from datetime import datetime

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

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    type = Column(String)  # "income" veya "expense"
    category = Column(String)
    description = Column(String)
    date = Column(Date)
    is_recurring = Column(Boolean, default=False)
    recurring_type = Column(String, nullable=True)  # "daily", "weekly", "monthly", "yearly"
    
    # İlişkiler
    user = relationship("User", back_populates="transactions")

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String)
    amount = Column(Float)
    period = Column(String)  # "monthly" veya "yearly"
    start_date = Column(Date)
    end_date = Column(Date)
    
    # İlişkiler
    user = relationship("User", back_populates="budgets")

class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    target_amount = Column(Float)
    current_amount = Column(Float, default=0)
    deadline = Column(Date)
    priority = Column(String)  # "low", "medium", "high"
    
    # İlişkiler
    user = relationship("User", back_populates="goals")

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