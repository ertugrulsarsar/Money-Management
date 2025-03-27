from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.database import Budget, Transaction
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

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