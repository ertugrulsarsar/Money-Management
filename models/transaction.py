from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List


class TransactionType(Enum):
    INCOME = "Gelir"
    EXPENSE = "Gider"


class Category(Enum):
    # Gelir kategorileri
    SALARY = "Maaş"
    INVESTMENT = "Yatırım"
    GIFT = "Hediye"
    OTHER_INCOME = "Diğer Gelir"
    
    # Gider kategorileri
    FOOD = "Yemek"
    RENT = "Kira"
    UTILITIES = "Faturalar"
    TRANSPORTATION = "Ulaşım"
    ENTERTAINMENT = "Eğlence"
    SHOPPING = "Alışveriş"
    HEALTH = "Sağlık"
    EDUCATION = "Eğitim"
    OTHER_EXPENSE = "Diğer Gider"
    
    @classmethod
    def income_categories(cls) -> List["Category"]:
        return [cls.SALARY, cls.INVESTMENT, cls.GIFT, cls.OTHER_INCOME]
    
    @classmethod
    def expense_categories(cls) -> List["Category"]:
        return [cls.FOOD, cls.RENT, cls.UTILITIES, cls.TRANSPORTATION, 
                cls.ENTERTAINMENT, cls.SHOPPING, cls.HEALTH, cls.EDUCATION, 
                cls.OTHER_EXPENSE]


@dataclass
class Transaction:
    amount: float
    category: str  # Artık doğrudan string olarak kategori adını saklar
    description: str
    date: datetime
    transaction_type: TransactionType
    id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,  # Zaten string
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d"),
            "transaction_type": self.transaction_type.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data.get("id"),
            amount=float(data["amount"]),
            category=data["category"],  # Doğrudan string olarak kullan
            description=data["description"],
            date=datetime.strptime(data["date"], "%Y-%m-%d"),
            transaction_type=next(t for t in TransactionType if t.value == data["transaction_type"])
        ) 