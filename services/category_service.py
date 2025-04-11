from typing import List, Optional
from sqlalchemy.orm import Session
from models.category import Category
from utils.db import db_session

class CategoryService:
    """Kategori (Category) verilerini yöneten servis sınıfı."""
    
    def __init__(self):
        """Servis sınıfını başlatır."""
        pass
        
    def get_categories(self) -> List[Category]:
        """Tüm kategorileri getirir."""
        with db_session() as session:
            return session.query(Category).order_by(Category.name).all()
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Belirli bir kategoriyi ID'sine göre getirir."""
        with db_session() as session:
            return session.query(Category).filter(Category.id == category_id).first()
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Belirli bir kategoriyi ismine göre getirir."""
        with db_session() as session:
            return session.query(Category).filter(Category.name == name).first()
    
    def get_categories_by_user(self, user_id: int) -> List[Category]:
        """Belirli bir kullanıcıya ait kategorileri getirir."""
        with db_session() as session:
            return session.query(Category).filter(Category.user_id == user_id).order_by(Category.name).all()
    
    def get_or_create_category(self, name: str, user_id: int, color: str = "#3498db") -> Category:
        """Kategori varsa getirir, yoksa yeni kategori oluşturur."""
        with db_session() as session:
            category = session.query(Category).filter(
                Category.name == name,
                Category.user_id == user_id
            ).first()
            
            if category:
                return category
                
            # Kategori yoksa yeni oluştur
            new_category = Category(
                name=name,
                user_id=user_id,
                color=color
            )
            session.add(new_category)
            session.commit()
            session.refresh(new_category)
            return new_category
    
    def create_category(self, name: str, user_id: int, color: str = "#3498db", icon: str = "tag") -> Category:
        """Yeni bir kategori oluşturur."""
        with db_session() as session:
            category = Category(
                name=name,
                user_id=user_id,
                color=color,
                icon=icon
            )
            session.add(category)
            session.commit()
            session.refresh(category)
            return category
    
    def update_category(
        self,
        category_id: int,
        name: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Optional[Category]:
        """Mevcut bir kategoriyi günceller."""
        with db_session() as session:
            category = session.query(Category).filter(Category.id == category_id).first()
            if not category:
                return None
                
            if name is not None:
                category.name = name
            if color is not None:
                category.color = color
            if icon is not None:
                category.icon = icon
                
            session.commit()
            session.refresh(category)
            return category
    
    def delete_category(self, category_id: int) -> bool:
        """Bir kategoriyi siler."""
        with db_session() as session:
            category = session.query(Category).filter(Category.id == category_id).first()
            if not category:
                return False
                
            session.delete(category)
            session.commit()
            return True 