from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base

class User(Base):
    """Kullanıcı modeli."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Bildirim tercihleri
    notification_preferences = Column(Text, nullable=True)  # JSON formatında bildirim tercihleri
    
    # İlişkiler
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    def get_notification_preferences(self):
        """Kullanıcının bildirim tercihlerini döndürür."""
        import json
        
        if not self.notification_preferences:
            # Varsayılan bildirim tercihleri
            return {
                "email_notifications": True,
                "app_notifications": True,
                "notification_types": {
                    "SYSTEM": True,
                    "TRANSACTION": True,
                    "BUDGET": True,
                    "GOAL": True,
                    "REPORT": True,
                    "SECURITY": True,
                    "REMINDER": True
                }
            }
        
        try:
            return json.loads(self.notification_preferences)
        except json.JSONDecodeError:
            # Hatalı JSON durumunda varsayılan değerleri döndür
            return {
                "email_notifications": True,
                "app_notifications": True,
                "notification_types": {
                    "SYSTEM": True,
                    "TRANSACTION": True,
                    "BUDGET": True,
                    "GOAL": True,
                    "REPORT": True,
                    "SECURITY": True,
                    "REMINDER": True
                }
            }
    
    def update_notification_preferences(self, preferences):
        """Kullanıcının bildirim tercihlerini günceller."""
        import json
        
        # Mevcut tercihleri al
        current_prefs = self.get_notification_preferences()
        
        # Yeni tercihlerle güncelle
        current_prefs.update(preferences)
        
        # JSON olarak kaydet
        self.notification_preferences = json.dumps(current_prefs)
        
        return current_prefs
        
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>" 