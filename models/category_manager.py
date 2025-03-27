import json
import os
import uuid
from typing import List, Dict, Optional

from models.transaction import TransactionType


class CustomCategory:
    def __init__(self, id: str, name: str, transaction_type: TransactionType):
        self.id = id
        self.name = name
        self.transaction_type = transaction_type
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "transaction_type": self.transaction_type.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CustomCategory":
        transaction_type = TransactionType.INCOME if data["transaction_type"] == TransactionType.INCOME.value else TransactionType.EXPENSE
        return cls(
            id=data["id"],
            name=data["name"],
            transaction_type=transaction_type
        )
    
    @property
    def value(self) -> str:
        """Category enum ile aynı arayüzü sağlamak için."""
        return self.name


class CategoryManager:
    def __init__(self, data_file: str = "data/categories.json"):
        self.data_file = data_file
        self.categories: List[CustomCategory] = []
        self.default_categories = self._get_default_categories()
        self._ensure_data_directory()
        self.load_data()
    
    def _ensure_data_directory(self):
        """Veri dosyası için gerekli dizini oluşturur."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _get_default_categories(self) -> List[CustomCategory]:
        """Varsayılan kategorileri oluşturur."""
        default_categories = []
        
        # Gelir kategorileri
        default_categories.extend([
            CustomCategory(id=str(uuid.uuid4()), name="Maaş", transaction_type=TransactionType.INCOME),
            CustomCategory(id=str(uuid.uuid4()), name="Yatırım", transaction_type=TransactionType.INCOME),
            CustomCategory(id=str(uuid.uuid4()), name="Hediye", transaction_type=TransactionType.INCOME),
            CustomCategory(id=str(uuid.uuid4()), name="Diğer Gelir", transaction_type=TransactionType.INCOME),
        ])
        
        # Gider kategorileri
        default_categories.extend([
            CustomCategory(id=str(uuid.uuid4()), name="Yemek", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Kira", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Faturalar", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Ulaşım", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Eğlence", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Alışveriş", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Sağlık", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Eğitim", transaction_type=TransactionType.EXPENSE),
            CustomCategory(id=str(uuid.uuid4()), name="Diğer Gider", transaction_type=TransactionType.EXPENSE),
        ])
        
        return default_categories
    
    def add_category(self, name: str, transaction_type: TransactionType) -> CustomCategory:
        """Yeni bir kategori ekler."""
        # Aynı isimde ve aynı türde kategori var mı kontrol et
        for category in self.categories:
            if category.name.lower() == name.lower() and category.transaction_type == transaction_type:
                return category  # Aynı kategori zaten var, mevcut kategoriyi döndür
        
        # Yeni kategori oluştur
        category = CustomCategory(
            id=str(uuid.uuid4()),
            name=name,
            transaction_type=transaction_type
        )
        
        self.categories.append(category)
        self.save_data()
        return category
    
    def delete_category(self, category_id: str) -> bool:
        """Belirli bir kategoriyi siler."""
        initial_count = len(self.categories)
        self.categories = [c for c in self.categories if c.id != category_id]
        
        if len(self.categories) < initial_count:
            self.save_data()
            return True
        return False
    
    def update_category(self, category_id: str, name: str) -> Optional[CustomCategory]:
        """Kategori adını günceller."""
        for category in self.categories:
            if category.id == category_id:
                category.name = name
                self.save_data()
                return category
        return None
    
    def get_categories(self, transaction_type: Optional[TransactionType] = None) -> List[CustomCategory]:
        """Belirli bir türdeki kategorileri döndürür."""
        if transaction_type is None:
            return self.categories
        
        return [c for c in self.categories if c.transaction_type == transaction_type]
    
    def get_income_categories(self) -> List[CustomCategory]:
        """Gelir kategorilerini döndürür."""
        return self.get_categories(TransactionType.INCOME)
    
    def get_expense_categories(self) -> List[CustomCategory]:
        """Gider kategorilerini döndürür."""
        return self.get_categories(TransactionType.EXPENSE)
    
    def save_data(self):
        """Verileri dosyaya kaydeder."""
        data = [c.to_dict() for c in self.categories]
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """Dosyadan verileri yükler veya varsayılan kategorileri kullanır."""
        if not os.path.exists(self.data_file):
            self.categories = self.default_categories.copy()
            self.save_data()
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.categories = [CustomCategory.from_dict(item) for item in data]
            
            # Eğer kategoriler boşsa varsayılanları ekle
            if not self.categories:
                self.categories = self.default_categories.copy()
                self.save_data()
                
        except (json.JSONDecodeError, FileNotFoundError):
            self.categories = self.default_categories.copy()
            self.save_data() 