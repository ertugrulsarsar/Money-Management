from sqlalchemy import Column, Integer, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from models.base import Base
import enum
from typing import Dict, Any

class NotificationChannel(enum.Enum):
    """Bildirim kanalları."""
    APP = "app"     # Uygulama içi bildirimler
    EMAIL = "email" # E-posta bildirimleri
    # İleride SMS veya diğer kanallar eklenebilir

class NotificationPreferences(Base):
    """Kullanıcı bildirim tercih modeli."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Sistem Bildirimleri
    system_app = Column(Boolean, default=True, nullable=False)
    system_email = Column(Boolean, default=False, nullable=False)
    
    # İşlem Bildirimleri
    transaction_app = Column(Boolean, default=True, nullable=False)
    transaction_email = Column(Boolean, default=False, nullable=False)
    
    # Bütçe Bildirimleri
    budget_app = Column(Boolean, default=True, nullable=False)
    budget_email = Column(Boolean, default=False, nullable=False)
    
    # Hedef Bildirimleri
    goal_app = Column(Boolean, default=True, nullable=False)
    goal_email = Column(Boolean, default=False, nullable=False)
    
    # Rapor Bildirimleri
    report_app = Column(Boolean, default=True, nullable=False)
    report_email = Column(Boolean, default=False, nullable=False)
    
    # Güvenlik Bildirimleri
    security_app = Column(Boolean, default=True, nullable=False)
    security_email = Column(Boolean, default=True, nullable=False)  # Güvenlik bildirimleri için e-posta varsayılan olarak açık
    
    # Hatırlatıcı Bildirimleri
    reminder_app = Column(Boolean, default=True, nullable=False)
    reminder_email = Column(Boolean, default=False, nullable=False)
    
    # İlişkiler
    user = relationship("User", back_populates="notification_preferences")
    
    def to_dict(self) -> Dict[str, Any]:
        """Bildirim tercihlerini sözlük olarak döndürür."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "system_app": self.system_app,
            "system_email": self.system_email,
            "transaction_app": self.transaction_app,
            "transaction_email": self.transaction_email,
            "budget_app": self.budget_app,
            "budget_email": self.budget_email,
            "goal_app": self.goal_app,
            "goal_email": self.goal_email,
            "report_app": self.report_app,
            "report_email": self.report_email,
            "security_app": self.security_app,
            "security_email": self.security_email,
            "reminder_app": self.reminder_app,
            "reminder_email": self.reminder_email
        }
    
    def get_channel_preference(self, notification_type: str, channel: str) -> bool:
        """Belirli bir bildirim türü ve kanal için tercihi döndürür."""
        attribute = f"{notification_type}_{channel}"
        return getattr(self, attribute, True)  # Varsayılan olarak True döndürür
    
    def __repr__(self) -> str:
        return f"<NotificationPreferences(id={self.id}, user_id={self.user_id})>" 