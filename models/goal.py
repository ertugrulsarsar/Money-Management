from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models.base import Base
import datetime

class Goal(Base):
    """Finansal hedef modeli. Kullanıcıların tasarruf hedeflerini tanımlar."""
    
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, nullable=False)
    target_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    creation_date = Column(Date, default=datetime.datetime.now().date(), nullable=False)
    completion_date = Column(Date, nullable=True)
    
    # İlişkiler
    user = relationship("User", back_populates="goals")
    category = relationship("Category", back_populates="goals")
    transactions = relationship("Transaction", back_populates="goal")
    
    def __init__(self, user_id, name, target_amount, target_date, description=None, 
                 category_id=None, is_completed=False, creation_date=None, completion_date=None):
        """Goal nesnesini başlatır."""
        self.user_id = user_id
        self.name = name
        self.target_amount = target_amount
        self.target_date = target_date
        self.description = description
        self.category_id = category_id
        self.is_completed = is_completed
        self.creation_date = creation_date or datetime.datetime.now().date()
        self.completion_date = completion_date
    
    def __repr__(self):
        """Goal temsilini döndürür."""
        return f"<Goal(id={self.id}, name={self.name}, target_amount={self.target_amount})>"
    
    def to_dict(self):
        """Goal'ı sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "target_amount": self.target_amount,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "description": self.description,
            "category_id": self.category_id,
            "is_completed": self.is_completed,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "category_name": self.category.name if self.category else None
        } 