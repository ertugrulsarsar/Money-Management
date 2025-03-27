import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models.database import Transaction, Budget, FinancialGoal
from sqlalchemy.orm import Session
import calendar

class DataGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.categories = {
            "income": [
                "Maaş", "Freelance", "Yatırım", "Kira Geliri", "Diğer Gelirler"
            ],
            "expense": [
                "Market", "Faturalar", "Ulaşım", "Sağlık", "Eğlence", 
                "Alışveriş", "Kira", "Sigorta", "Eğitim", "Diğer"
            ]
        }
        
        self.goal_names = [
            "Ev Almak", "Araba Almak", "Tatil", "Emeklilik", 
            "Eğitim", "Yatırım", "Acil Durum Fonu"
        ]

    def generate_random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Rastgele bir tarih üretir."""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randint(0, days_between)
        return start_date + timedelta(days=random_days)

    def generate_random_amount(self, min_amount: float, max_amount: float) -> float:
        """Rastgele bir miktar üretir."""
        return round(random.uniform(min_amount, max_amount), 2)

    def populate_user_data(self, user_id: int) -> Dict:
        """Kullanıcı için örnek veriler üretir."""
        # Son 1 yıllık tarih aralığı
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # İşlemler
        transactions = []
        for _ in range(50):  # 50 işlem
            transaction_type = random.choice(["income", "expense"])
            category = random.choice(self.categories[transaction_type])
            
            # Gelir ve gider için farklı miktar aralıkları
            if transaction_type == "income":
                amount = self.generate_random_amount(5000, 50000)
            else:
                amount = self.generate_random_amount(100, 5000)
            
            transaction = Transaction(
                user_id=user_id,
                amount=amount,
                type=transaction_type,
                category=category,
                description=f"Örnek {transaction_type} işlemi",
                date=self.generate_random_date(start_date, end_date),
                is_recurring=random.choice([True, False]),
                recurring_type=random.choice(["daily", "weekly", "monthly", "yearly"]) if random.choice([True, False]) else None
            )
            transactions.append(transaction)
        
        # Bütçeler
        budgets = []
        for category in self.categories["expense"]:
            amount = self.generate_random_amount(1000, 10000)
            budget = Budget(
                user_id=user_id,
                category=category,
                amount=amount,
                period="monthly",
                start_date=start_date,
                end_date=end_date
            )
            budgets.append(budget)
        
        # Hedefler
        goals = []
        for _ in range(3):  # 3 hedef
            name = random.choice(self.goal_names)
            target_amount = self.generate_random_amount(50000, 500000)
            current_amount = self.generate_random_amount(0, target_amount)
            
            goal = FinancialGoal(
                user_id=user_id,
                name=name,
                target_amount=target_amount,
                current_amount=current_amount,
                deadline=self.generate_random_date(end_date, end_date + timedelta(days=365)),
                priority=random.choice(["low", "medium", "high"])
            )
            goals.append(goal)
        
        # Veritabanına kaydet
        self.db.add_all(transactions + budgets + goals)
        self.db.commit()
        
        return {
            "transactions": len(transactions),
            "budgets": len(budgets),
            "goals": len(goals)
        } 