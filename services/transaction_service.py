from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from models.transaction import Transaction
from models.category import Category
from utils.db import db_session

class TransactionService:
    """İşlem (Transaction) verilerini yöneten servis sınıfı."""
    
    def __init__(self):
        """Servis sınıfını başlatır."""
        pass
        
    def get_transactions(self, limit: int = 100) -> List[Transaction]:
        """Tüm işlemleri getirir."""
        with db_session() as session:
            return session.query(Transaction).order_by(Transaction.date.desc()).limit(limit).all()
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Belirli bir işlemi ID'sine göre getirir."""
        with db_session() as session:
            return session.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    def get_last_transactions(self, limit: int = 5) -> List[Transaction]:
        """Son işlemleri getirir."""
        with db_session() as session:
            return session.query(Transaction).order_by(Transaction.date.desc()).limit(limit).all()
    
    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Transaction]:
        """Belirli bir tarih aralığındaki işlemleri getirir."""
        with db_session() as session:
            return session.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).order_by(Transaction.date.desc()).all()
    
    def get_transactions_by_category(self, category_id: int) -> List[Transaction]:
        """Belirli bir kategoriye ait işlemleri getirir."""
        with db_session() as session:
            return session.query(Transaction).filter(
                Transaction.category_id == category_id
            ).order_by(Transaction.date.desc()).all()
    
    def get_transactions_by_type(self, transaction_type: str) -> List[Transaction]:
        """Belirli bir tipe (gelir/gider) ait işlemleri getirir."""
        with db_session() as session:
            return session.query(Transaction).filter(
                Transaction.type == transaction_type
            ).order_by(Transaction.date.desc()).all()
    
    def create_transaction(
        self, 
        user_id: int,
        amount: float, 
        description: str, 
        date: datetime,
        type: str,
        category_id: Optional[int] = None
    ) -> Transaction:
        """Yeni bir işlem oluşturur."""
        with db_session() as session:
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                description=description,
                date=date,
                type=type,
                category_id=category_id
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction
    
    def update_transaction(
        self,
        transaction_id: int,
        amount: Optional[float] = None,
        description: Optional[str] = None,
        date: Optional[datetime] = None,
        type: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> Optional[Transaction]:
        """Mevcut bir işlemi günceller."""
        with db_session() as session:
            transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not transaction:
                return None
                
            if amount is not None:
                transaction.amount = amount
            if description is not None:
                transaction.description = description
            if date is not None:
                transaction.date = date
            if type is not None:
                transaction.type = type
            if category_id is not None:
                transaction.category_id = category_id
                
            session.commit()
            session.refresh(transaction)
            return transaction
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Bir işlemi siler."""
        with db_session() as session:
            transaction = session.query(Transaction).filter(Transaction.id == transaction_id).first()
            if not transaction:
                return False
                
            session.delete(transaction)
            session.commit()
            return True
    
    def get_monthly_totals(self, months: int = 6) -> dict:
        """Son n aydaki aylık toplam gelir ve giderleri hesaplar."""
        today = datetime.now()
        start_date = today.replace(day=1) - timedelta(days=30 * (months - 1))
        
        with db_session() as session:
            transactions = session.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= today
            ).all()
            
            result = {}
            for month in range(months):
                month_date = start_date.replace(day=1) + timedelta(days=30 * month)
                month_name = month_date.strftime("%Y-%m")
                result[month_name] = {"income": 0, "expense": 0}
            
            for t in transactions:
                month_name = t.date.strftime("%Y-%m")
                if month_name in result:
                    if t.type == "income":
                        result[month_name]["income"] += t.amount
                    else:
                        result[month_name]["expense"] += t.amount
            
            return result
            
    def get_category_totals(self, start_date: datetime, end_date: datetime) -> dict:
        """Belirli bir zaman aralığında kategorilere göre toplam tutarları hesaplar."""
        with db_session() as session:
            transactions = session.query(Transaction).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            categories = session.query(Category).all()
            category_dict = {c.id: c.name for c in categories}
            
            result = {"Kategorisiz": 0}
            for c in categories:
                result[c.name] = 0
                
            for t in transactions:
                if t.type == "expense":  # Sadece giderleri kategorilere ayırıyoruz
                    if t.category_id and t.category_id in category_dict:
                        result[category_dict[t.category_id]] += t.amount
                    else:
                        result["Kategorisiz"] += t.amount
                        
            return result 