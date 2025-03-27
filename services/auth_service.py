from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models.database import User
from services.database_service import DatabaseService
from utils.logger import FinanceLogger
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import timedelta

# Güvenlik ayarları
SECRET_KEY = "your-secret-key-here"  # Gerçek uygulamada .env dosyasından alınmalı
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    def __init__(self, db: Session):
        self.db_service = DatabaseService(db)
        self.logger = FinanceLogger()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Kullanıcı adına göre kullanıcıyı getirir."""
        return self.db_service.get_user_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """E-posta adresine göre kullanıcıyı getirir."""
        return self.db_service.get_user_by_email(email)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifreyi doğrular."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Şifreyi hashler."""
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Kullanıcıyı doğrular."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, username: str, email: str, password: str) -> Optional[User]:
        """Yeni kullanıcı oluşturur."""
        if self.get_user_by_username(username):
            return None
        if self.get_user_by_email(email):
            return None

        hashed_password = self.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            created_at=datetime.now()
        )

        self.db_service.add_user(user)
        self.db_service.commit()
        self.db_service.refresh(user)

        self.logger.log_user_action(
            user.id,
            "create",
            {
                "username": username,
                "email": email,
                "created_at": user.created_at.isoformat()
            }
        )

        return user

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Kullanıcı bilgilerini günceller."""
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if key == "password":
                value = self.get_password_hash(value)
            setattr(user, key, value)

        self.db_service.commit()
        self.db_service.refresh(user)

        self.logger.log_user_action(
            user_id,
            "update",
            {k: v for k, v in kwargs.items() if k != "password"}
        )

        return user

    def delete_user(self, user_id: int) -> bool:
        """Kullanıcıyı siler."""
        user = self.db_service.get_user_by_id(user_id)
        if not user:
            return False

        self.db_service.delete_user(user)
        self.db_service.commit()

        self.logger.log_user_action(
            user_id,
            "delete",
            {"username": user.username, "email": user.email}
        )

        return True

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None 