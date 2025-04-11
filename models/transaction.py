from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from models.base import Base
import datetime

class Transaction(Base):
    """İşlem (gelir/gider) modeli."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    date = Column(Date, default=datetime.datetime.now().date(), nullable=False)
    type = Column(String(20), nullable=False)  # "income", "expense", "saving", "transfer"
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    created_at = Column(Date, default=datetime.datetime.now().date(), nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    goal = relationship("Goal", back_populates="transactions")
    
    def __init__(self, user_id, amount, description, date, type, category_id=None, goal_id=None):
        """Transaction nesnesini başlatır."""
        self.user_id = user_id
        self.amount = amount
        self.description = description
        self.date = date
        self.type = type
        self.category_id = category_id
        self.goal_id = goal_id
        self.created_at = datetime.datetime.now().date()
    
    def __repr__(self):
        """Transaction temsilini döndürür."""
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.type})>"
    
    def to_dict(self):
        """Transaction'ı sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat() if self.date else None,
            "type": self.type,
            "category_id": self.category_id,
            "goal_id": self.goal_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "category_name": self.category.name if self.category else None
        } 