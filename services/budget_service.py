from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.database import Budget, Transaction
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from utils.db import db_session

class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_category_spending(self, user_id: int, category: str, months: int = 6) -> Dict[str, Any]:
        """Kategori bazlı harcama analizi yapar."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30 * months)
        
        # Kategori harcamalarını al
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.category == category,
            Transaction.date.between(start_date, end_date)
        ).all()
        
        if not transactions:
            return None
        
        # Aylık harcamaları hesapla
        monthly_spending = {}
        for transaction in transactions:
            month_key = transaction.date.strftime("%Y-%m")
            monthly_spending[month_key] = monthly_spending.get(month_key, 0) + transaction.amount
        
        # Trend analizi
        df = pd.DataFrame(list(monthly_spending.items()), columns=["month", "amount"])
        df["month_num"] = range(len(df))
        
        X = df[["month_num"]].values
        y = df["amount"].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Gelecek ay tahmini
        next_month = len(df)
        predicted_amount = model.predict([[next_month]])[0]
        
        return {
            "category": category,
            "monthly_spending": monthly_spending,
            "average_spending": sum(monthly_spending.values()) / len(monthly_spending),
            "trend": model.coef_[0],
            "predicted_next_month": predicted_amount
        }

    def suggest_budget(self, user_id: int, category: str) -> Dict[str, Any]:
        """Kategori için bütçe önerisi oluşturur."""
        analysis = self.analyze_category_spending(user_id, category)
        
        if not analysis:
            return None
        
        # Bütçe önerisi hesaplama
        avg_spending = analysis["average_spending"]
        trend = analysis["trend"]
        
        # Trende göre bütçe ayarlama
        if trend > 0:  # Artan trend
            suggested_budget = avg_spending * 1.1
        elif trend < 0:  # Azalan trend
            suggested_budget = avg_spending * 0.9
        else:  # Sabit trend
            suggested_budget = avg_spending
        
        return {
            "category": category,
            "suggested_budget": suggested_budget,
            "average_spending": avg_spending,
            "trend": trend,
            "confidence": abs(trend) / avg_spending if avg_spending > 0 else 0
        }

    def get_budget_performance(self, user_id: int, budget_id: int) -> Dict[str, Any]:
        """Bütçe performans analizi yapar."""
        budget = self.db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()
        
        if not budget:
            return None
        
        # Dönem harcamalarını al
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.category == budget.category,
            Transaction.date.between(budget.start_date, budget.end_date)
        ).all()
        
        # Harcamaları günlere göre grupla
        daily_spending = {}
        for transaction in transactions:
            date_key = transaction.date.strftime("%Y-%m-%d")
            daily_spending[date_key] = daily_spending.get(date_key, 0) + transaction.amount
        
        # Performans metrikleri
        total_spent = sum(daily_spending.values())
        daily_average = total_spent / len(daily_spending) if daily_spending else 0
        
        # Tarih karşılaştırması için date objelerini kullan
        current_date = date.today()
        end_date = budget.end_date.date() if isinstance(budget.end_date, datetime) else budget.end_date
        remaining_days = (end_date - current_date).days
        projected_spending = daily_average * remaining_days if remaining_days > 0 else 0
        
        return {
            "budget_id": budget_id,
            "category": budget.category,
            "total_budget": budget.amount,
            "total_spent": total_spent,
            "remaining": budget.amount - total_spent,
            "daily_average": daily_average,
            "projected_spending": projected_spending,
            "daily_spending": daily_spending,
            "remaining_days": remaining_days
        }

    def get_category_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Kategori bazlı bütçe önerileri oluşturur."""
        # Tüm kategorileri al
        categories = self.db.query(Transaction.category).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        ).distinct().all()
        
        recommendations = []
        for category in categories:
            suggestion = self.suggest_budget(user_id, category[0])
            if suggestion:
                recommendations.append(suggestion)
        
        # Güven skoruna göre sırala
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations

    def optimize_budget(self, user_id: int, total_budget: float) -> List[Dict[str, Any]]:
        """Toplam bütçeyi kategorilere optimize eder."""
        recommendations = self.get_category_recommendations(user_id)
        
        if not recommendations:
            return None
        
        # Toplam önerilen bütçeyi hesapla
        total_suggested = sum(r["suggested_budget"] for r in recommendations)
        
        # Bütçeyi oransal olarak dağıt
        optimized_budgets = []
        for rec in recommendations:
            ratio = rec["suggested_budget"] / total_suggested
            optimized_budgets.append({
                "category": rec["category"],
                "suggested_budget": rec["suggested_budget"],
                "optimized_budget": total_budget * ratio,
                "confidence": rec["confidence"]
            })
        
        return optimized_budgets

    def get_budgets(self, limit: int = 100) -> List[Budget]:
        """Tüm bütçeleri getirir."""
        with db_session() as session:
            return session.query(Budget).order_by(Budget.start_date.desc()).limit(limit).all()
    
    def get_budget_by_id(self, budget_id: int) -> Optional[Budget]:
        """Belirli bir bütçeyi ID'sine göre getirir."""
        with db_session() as session:
            return session.query(Budget).filter(Budget.id == budget_id).first()
    
    def get_budgets_by_user(self, user_id: int) -> List[Budget]:
        """Belirli bir kullanıcıya ait bütçeleri getirir."""
        with db_session() as session:
            return session.query(Budget).filter(Budget.user_id == user_id).order_by(Budget.start_date.desc()).all()
    
    def get_active_budgets(self, user_id: Optional[int] = None) -> List[Budget]:
        """Aktif bütçeleri getirir."""
        today = datetime.now().date()
        with db_session() as session:
            query = session.query(Budget).filter(
                Budget.start_date <= today,
                Budget.end_date >= today
            )
            
            if user_id:
                query = query.filter(Budget.user_id == user_id)
                
            return query.order_by(Budget.start_date.desc()).all()
    
    def get_budgets_by_category(self, category_id: int) -> List[Budget]:
        """Belirli bir kategoriye ait bütçeleri getirir."""
        with db_session() as session:
            return session.query(Budget).filter(
                Budget.category_id == category_id
            ).order_by(Budget.start_date.desc()).all()
    
    def get_spent_amount(self, budget_id: int) -> float:
        """Belirli bir bütçe için harcanan tutarı hesaplar."""
        with db_session() as session:
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            
            if not budget:
                return 0.0
                
            # Bütçeye ait kategorideki tüm harcamaları topla
            query = session.query(Transaction).filter(
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date,
                Transaction.type == "expense"
            )
            
            # Eğer bütçe belirli bir kategoriye aitse sadece o kategorideki harcamaları al
            if budget.category_id:
                query = query.filter(Transaction.category_id == budget.category_id)
            elif budget.user_id:
                # Kategorisiz bütçe ise kullanıcının tüm harcamalarını al
                query = query.filter(Transaction.user_id == budget.user_id)
                
            transactions = query.all()
            return sum(t.amount for t in transactions)
    
    def get_budget_progress(self, budget_id: int) -> dict:
        """Belirli bir bütçenin ilerleme durumunu hesaplar."""
        with db_session() as session:
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            
            if not budget:
                return {
                    "total": 0,
                    "spent": 0,
                    "remaining": 0,
                    "percentage": 0
                }
                
            spent = self.get_spent_amount(budget_id)
            remaining = budget.amount - spent
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            
            return {
                "total": budget.amount,
                "spent": spent,
                "remaining": remaining,
                "percentage": min(percentage, 100)  # Yüzde 100'den fazla olmamalı
            }
    
    def create_budget(
        self,
        user_id: int,
        amount: float,
        start_date: datetime,
        end_date: datetime,
        description: str,
        category_id: Optional[int] = None
    ) -> Budget:
        """Yeni bir bütçe oluşturur."""
        with db_session() as session:
            budget = Budget(
                user_id=user_id,
                amount=amount,
                start_date=start_date,
                end_date=end_date,
                description=description,
                category_id=category_id
            )
            session.add(budget)
            session.commit()
            session.refresh(budget)
            return budget
    
    def update_budget(
        self,
        budget_id: int,
        amount: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None
    ) -> Optional[Budget]:
        """Mevcut bir bütçeyi günceller."""
        with db_session() as session:
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            if not budget:
                return None
                
            if amount is not None:
                budget.amount = amount
            if start_date is not None:
                budget.start_date = start_date
            if end_date is not None:
                budget.end_date = end_date
            if description is not None:
                budget.description = description
            if category_id is not None:
                budget.category_id = category_id
                
            session.commit()
            session.refresh(budget)
            return budget
    
    def delete_budget(self, budget_id: int) -> bool:
        """Bir bütçeyi siler."""
        with db_session() as session:
            budget = session.query(Budget).filter(Budget.id == budget_id).first()
            if not budget:
                return False
                
            session.delete(budget)
            session.commit()
            return True 