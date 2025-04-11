from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Category(Base):
    """Kategori modeli. İşlemler ve bütçeler için kategorizasyon sağlar."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    color = Column(String(20), nullable=True, default="#3498db")
    icon = Column(String(50), nullable=True, default="tag")
    
    # İlişkiler
    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    budgets = relationship("Budget", back_populates="category")
    
    def __init__(self, name, user_id, color="#3498db", icon="tag"):
        """Category nesnesini başlatır."""
        self.name = name
        self.user_id = user_id
        self.color = color
        self.icon = icon
    
    def __repr__(self):
        """Category temsilini döndürür."""
        return f"<Category(id={self.id}, name={self.name})>"
    
    def to_dict(self):
        """Category'i sözlük olarak döndürür."""
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "color": self.color,
            "icon": self.icon
        } 