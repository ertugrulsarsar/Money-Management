from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Text
from sqlalchemy.orm import relationship
from models.base import Base

class NotificationType(str, Enum):
    """Bildirim türleri."""
    SYSTEM = "SYSTEM"  # Sistem bildirimleri
    TRANSACTION = "TRANSACTION"  # İşlem bildirimleri
    BUDGET = "BUDGET"  # Bütçe bildirimleri (ör. bütçe aşımı)
    GOAL = "GOAL"  # Hedef bildirimleri (ör. hedefe ulaşıldı) 
    REPORT = "REPORT"  # Rapor bildirimleri (ör. aylık rapor)
    SECURITY = "SECURITY"  # Güvenlik bildirimleri
    REMINDER = "REMINDER"  # Hatırlatıcılar

class Notification(Base):
    """Bildirim modeli."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    type = Column(SQLAlchemyEnum(NotificationType), nullable=False, default=NotificationType.SYSTEM)
    source_id = Column(Integer, nullable=True)  # İlgili varlık ID'si (ör. işlem ID, bütçe ID)
    
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    read_at = Column(DateTime, nullable=True)
    
    data = Column(Text, nullable=True)  # JSON formatında ekstra bilgiler
    
    # İlişkiler
    user = relationship("User", back_populates="notifications")
    
    def to_dict(self):
        """Bildirim verilerini sözlük olarak döndürür."""
        notification_dict = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value if self.type else None,
            "source_id": self.source_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "data": self.data
        }
        return notification_dict
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type={self.type}, is_read={self.is_read})>" 