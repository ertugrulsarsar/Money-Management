from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base

class UserPreferences(Base):
    """Kullanıcı tercihleri modeli."""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Genel kullanıcı tercihleri
    theme = Column(String(50), default="light", nullable=False)  # Tema seçimi: light, dark
    language = Column(String(10), default="tr", nullable=False)  # Dil seçimi
    date_format = Column(String(20), default="DD.MM.YYYY", nullable=False)  # Tarih formatı
    currency = Column(String(10), default="TRY", nullable=False)  # Para birimi
    
    # Ana ekran tercihleri
    show_dashboard_summary = Column(Boolean, default=True, nullable=False)  # Ana sayfada özet bilgileri göster
    show_recent_transactions = Column(Boolean, default=True, nullable=False)  # Ana sayfada son işlemleri göster
    show_budget_status = Column(Boolean, default=True, nullable=False)  # Ana sayfada bütçe durumunu göster
    show_goals = Column(Boolean, default=True, nullable=False)  # Ana sayfada hedefleri göster
    
    # Bildirim tercihleri (JSON formatında)
    notification_settings = Column(Text, nullable=True)
    
    # İlişkiler
    user = relationship("User", backref="preferences", uselist=False)
    
    def to_dict(self):
        """Tercihleri sözlük olarak döndürür."""
        import json
        
        notification_settings = {}
        if self.notification_settings:
            try:
                notification_settings = json.loads(self.notification_settings)
            except json.JSONDecodeError:
                pass
        
        return {
            "id": self.id,
            "user_id": self.user_id,
            "theme": self.theme,
            "language": self.language,
            "date_format": self.date_format,
            "currency": self.currency,
            "show_dashboard_summary": self.show_dashboard_summary,
            "show_recent_transactions": self.show_recent_transactions,
            "show_budget_status": self.show_budget_status,
            "show_goals": self.show_goals,
            "notification_settings": notification_settings
        }
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id})>" 