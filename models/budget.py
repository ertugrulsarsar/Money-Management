from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import Base
import datetime

class Budget(Base):
    """Bütçe modeli. Kategori bazlı harcama limitleri tanımlar."""
    
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    amount = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(Date, default=datetime.datetime.now().date(), nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
    
    def __init__(self, user_id, amount, start_date, end_date, description=None, category_id=None):
        """Budget nesnesini başlatır."""
        self.user_id = user_id
        self.amount = amount
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self.category_id = category_id
        self.created_at = datetime.datetime.now().date()
    
    def __repr__(self):
        """Budget temsilini döndürür."""
        return f"<Budget(id={self.id}, amount={self.amount})>"
    
    def to_dict(self):
        """Budget'i sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "amount": self.amount,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "category_name": self.category.name if self.category else "Genel"
        } 