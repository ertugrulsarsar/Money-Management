from sqlalchemy.orm import Session
from models.user import User
from models.user_preferences import UserPreference
from typing import Optional, Dict, Any, List
import hashlib
import os
import logging

# Loglama
logger = logging.getLogger(__name__)

class UserService:
    """Kullanıcı işlemleri için servis sınıfı."""
    
    def __init__(self, db: Session):
        """
        Kullanıcı servis sınıfı constructor.
        
        Args:
            db: Veritabanı oturumu
        """
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        ID'ye göre kullanıcı getirir.
        
        Args:
            user_id: Kullanıcı ID
            
        Returns:
            Kullanıcı nesnesi veya None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Kullanıcı adına göre kullanıcı getirir.
        
        Args:
            username: Kullanıcı adı
            
        Returns:
            Kullanıcı nesnesi veya None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        E-posta adresine göre kullanıcı getirir.
        
        Args:
            email: E-posta adresi
            
        Returns:
            Kullanıcı nesnesi veya None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """
        Yeni kullanıcı oluşturur.
        
        Args:
            username: Kullanıcı adı
            email: E-posta adresi
            password: Şifre
            
        Returns:
            Oluşturulan kullanıcı nesnesi
            
        Raises:
            ValueError: Kullanıcı adı veya e-posta zaten kullanılıyorsa
        """
        # Kullanıcı adı kontrol et
        if self.get_user_by_username(username):
            raise ValueError(f"Bu kullanıcı adı zaten kullanılıyor: {username}")
        
        # E-posta kontrol et
        if self.get_user_by_email(email):
            raise ValueError(f"Bu e-posta adresi zaten kullanılıyor: {email}")
        
        # Şifreyi hashle
        hashed_password = self._hash_password(password)
        
        # Kullanıcı oluştur
        user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Varsayılan kullanıcı tercihlerini oluştur
        self._create_default_preferences(user.id)
        
        return user
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """
        Kullanıcı adı/e-posta ve şifre ile kimlik doğrulama yapar.
        
        Args:
            username_or_email: Kullanıcı adı veya e-posta
            password: Şifre
            
        Returns:
            Doğrulanmış kullanıcı nesnesi veya None
        """
        # Kullanıcı adı veya e-posta ile kullanıcıyı bul
        user = self.get_user_by_username(username_or_email)
        if not user:
            user = self.get_user_by_email(username_or_email)
        
        if not user:
            return None
        
        # Şifreyi doğrula
        if not self._verify_password(password, user.password):
            return None
        
        return user
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Kullanıcı bilgilerini günceller.
        
        Args:
            user_id: Kullanıcı ID
            data: Güncellenecek veriler
            
        Returns:
            Güncellenmiş kullanıcı nesnesi veya None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Şifre güncellemesi varsa
        if "password" in data:
            data["password"] = self._hash_password(data["password"])
        
        # Güncellenebilir alanlar
        update_fields = ["email", "password", "is_active"]
        
        # Verileri güncelle
        for field in update_fields:
            if field in data:
                setattr(user, field, data[field])
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def _hash_password(self, password: str) -> str:
        """
        Şifreyi güvenli bir şekilde hashler.
        
        Args:
            password: Ham şifre
            
        Returns:
            Hashlenmiş şifre
        """
        # Salt oluştur
        salt = os.urandom(32)
        
        # Şifreyi hashle
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        # Salt ve hash'i birleştir
        return salt.hex() + ':' + key.hex()
    
    def _verify_password(self, password: str, stored_password: str) -> bool:
        """
        Şifreyi doğrular.
        
        Args:
            password: Doğrulanacak şifre
            stored_password: Kaydedilmiş hashlenmiş şifre
            
        Returns:
            Şifre doğruysa True, değilse False
        """
        try:
            # Salt ve hash'i ayır
            salt_hex, key_hex = stored_password.split(':')
            salt = bytes.fromhex(salt_hex)
            stored_key = bytes.fromhex(key_hex)
            
            # Girilen şifreyi aynı salt ile hashle
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt,
                100000
            )
            
            # Hashleri karşılaştır
            return key == stored_key
        except Exception as e:
            logger.error(f"Şifre doğrulama hatası: {str(e)}")
            return False
    
    def _create_default_preferences(self, user_id: int) -> UserPreference:
        """
        Yeni kullanıcı için varsayılan tercihler oluşturur.
        
        Args:
            user_id: Kullanıcı ID
            
        Returns:
            Oluşturulan tercih nesnesi
        """
        preferences = UserPreference(
            user_id=user_id,
            theme="light",
            language="tr",
            date_format="DD.MM.YYYY",
            currency="TRY",
            show_dashboard_summary=True,
            show_recent_transactions=True,
            show_budget_status=True,
            show_goals=True
        )
        
        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)
        
        return preferences
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı tercihlerini getirir.
        
        Args:
            user_id: Kullanıcı ID
            
        Returns:
            Tercihler sözlük olarak veya None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        preferences = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not preferences:
            # Tercihler yoksa varsayılanları oluştur
            preferences = self._create_default_preferences(user_id)
        
        return preferences.to_dict()
    
    def update_user_preferences(self, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Kullanıcı tercihlerini günceller.
        
        Args:
            user_id: Kullanıcı ID
            data: Güncellenecek tercih verileri
            
        Returns:
            Güncellenmiş tercihler sözlük olarak veya None
        """
        preferences = self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not preferences:
            # Tercihler yoksa varsayılanları oluştur
            preferences = self._create_default_preferences(user_id)
        
        # Güncellenebilir alanlar
        update_fields = [
            "theme", "language", "date_format", "currency", 
            "show_dashboard_summary", "show_recent_transactions", 
            "show_budget_status", "show_goals", "notification_settings"
        ]
        
        # Verileri güncelle
        for field in update_fields:
            if field in data:
                setattr(preferences, field, data[field])
        
        self.db.commit()
        self.db.refresh(preferences)
        
        return preferences.to_dict() 