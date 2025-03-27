import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Union

import pandas as pd

from models.transaction import Transaction, TransactionType, Category
from models.category_manager import CustomCategory


class FinanceManager:
    def __init__(self, data_file: str = "data/transactions.json"):
        self.data_file = data_file
        self.transactions: List[Transaction] = []
        self._ensure_data_directory()
        self.load_data()
    
    def _ensure_data_directory(self):
        """Veri dosyası için gerekli dizini oluşturur."""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def add_transaction(self, amount: float, category: Union[Category, CustomCategory], 
                      description: str, date: datetime, 
                      transaction_type: TransactionType) -> Transaction:
        """Yeni bir işlem ekler."""
        # CustomCategory veya Category nesnesi için kategori değerini al
        category_value = category.value if hasattr(category, 'value') else category.name
        
        transaction = Transaction(
            id=str(uuid.uuid4()),
            amount=amount,
            category=category_value,  # Sadece string değerini saklıyoruz
            description=description,
            date=date,
            transaction_type=transaction_type
        )
        self.transactions.append(transaction)
        self.save_data()
        return transaction
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """Belirli bir işlemi siler."""
        initial_count = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != transaction_id]
        
        if len(self.transactions) < initial_count:
            self.save_data()
            return True
        return False
    
    def get_transactions(self, 
                        transaction_type: Optional[TransactionType] = None,
                        category: Optional[str] = None,  # Artık string olarak kategori adı kabul eder
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Transaction]:
        """Belirli kriterlere göre işlemleri filtreler."""
        filtered = self.transactions.copy()
        
        if transaction_type:
            filtered = [t for t in filtered if t.transaction_type == transaction_type]
        
        if category:
            filtered = [t for t in filtered if t.category == category]
        
        if start_date:
            filtered = [t for t in filtered if t.date >= start_date]
        
        if end_date:
            filtered = [t for t in filtered if t.date <= end_date]
        
        return filtered
    
    def get_transactions_as_dataframe(self, **kwargs) -> pd.DataFrame:
        """İşlemleri pandas DataFrame olarak döndürür."""
        transactions = self.get_transactions(**kwargs)
        if not transactions:
            return pd.DataFrame()
        
        data = [t.to_dict() for t in transactions]
        df = pd.DataFrame(data)
        
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        return df
    
    def get_category_summary(self, transaction_type: Optional[TransactionType] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, float]:
        """Kategori bazında toplam miktarları hesaplar."""
        transactions = self.get_transactions(
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        summary = {}
        for transaction in transactions:
            category = transaction.category
            if category not in summary:
                summary[category] = 0
            summary[category] += transaction.amount
        
        return summary
    
    def get_balance(self, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> float:
        """Belirli bir dönem için bakiyeyi hesaplar."""
        incomes = sum(t.amount for t in self.get_transactions(
            transaction_type=TransactionType.INCOME,
            start_date=start_date,
            end_date=end_date
        ))
        
        expenses = sum(t.amount for t in self.get_transactions(
            transaction_type=TransactionType.EXPENSE,
            start_date=start_date,
            end_date=end_date
        ))
        
        return incomes - expenses
    
    def get_top_categories(self, transaction_type: TransactionType,
                         limit: int = 5,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Tuple[str, float]]:
        """En çok harcama/gelir yapılan kategorileri bulur."""
        summary = self.get_category_summary(
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # Kategorileri toplam miktara göre sırala
        sorted_categories = sorted(summary.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_categories[:limit]
    
    def save_data(self):
        """Verileri dosyaya kaydeder."""
        data = [t.to_dict() for t in self.transactions]
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """Dosyadan verileri yükler."""
        if not os.path.exists(self.data_file):
            self.transactions = []
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.transactions = [Transaction.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            self.transactions = [] 