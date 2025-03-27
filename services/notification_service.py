from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.database import Transaction, Budget, FinancialGoal

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def check_budget_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Bütçe aşımı uyarılarını kontrol eder."""
        alerts = []
        current_date = datetime.now()
        
        # Aktif bütçeleri al
        budgets = self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.start_date <= current_date,
            Budget.end_date >= current_date
        ).order_by(Budget.start_date.desc()).all()
        
        for budget in budgets:
            # Bu ayki harcamaları hesapla
            month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            expenses = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense",
                Transaction.category == budget.category,
                Transaction.date.between(month_start, month_end)
            ).all()
            
            total_expenses = sum(expense.amount for expense in expenses)
            
            # Bütçe limitini kontrol et
            if total_expenses >= budget.amount:
                alerts.append({
                    "type": "budget_alert",
                    "category": budget.category,
                    "limit": budget.amount,
                    "spent": total_expenses,
                    "remaining": budget.amount - total_expenses
                })
            elif total_expenses >= budget.amount * 0.8:  # %80 uyarısı
                alerts.append({
                    "type": "budget_warning",
                    "category": budget.category,
                    "limit": budget.amount,
                    "spent": total_expenses,
                    "remaining": budget.amount - total_expenses
                })
        
        return alerts

    def check_goal_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Hedef hatırlatmalarını kontrol eder."""
        reminders = []
        current_date = date.today()  # datetime yerine date kullan
        
        # Aktif hedefleri al
        goals = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.deadline >= current_date
        ).all()
        
        for goal in goals:
            # Hedef son tarihine yaklaşma kontrolü
            days_until_deadline = (goal.deadline - current_date).days
            
            if days_until_deadline <= 7:  # Son 7 gün
                progress = (goal.current_amount / goal.target_amount) * 100
                reminders.append({
                    "type": "goal_reminder",
                    "name": goal.name,
                    "target": goal.target_amount,
                    "current": goal.current_amount,
                    "progress": progress,
                    "deadline": goal.deadline,
                    "days_left": days_until_deadline
                })
        
        return reminders

    def check_recurring_transactions(self, user_id: int) -> List[Dict[str, Any]]:
        """Tekrarlayan işlem hatırlatmalarını kontrol eder."""
        reminders = []
        current_date = date.today()  # datetime yerine date kullan
        
        # Tekrarlayan işlemleri al
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_recurring == True
        ).all()
        
        for transaction in transactions:
            # Son işlem tarihini kontrol et
            last_transaction = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.category == transaction.category,
                Transaction.type == transaction.type,
                Transaction.is_recurring == True
            ).order_by(Transaction.date.desc()).first()
            
            if last_transaction:
                # Transaction.date'i date objesine çevir
                last_date = last_transaction.date.date() if isinstance(last_transaction.date, datetime) else last_transaction.date
                days_since_last = (current_date - last_date).days
                
                # Tekrar sıklığına göre kontrol et
                if transaction.recurring_type == "daily" and days_since_last >= 1:
                    reminders.append({
                        "type": "recurring_reminder",
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "frequency": "günlük",
                        "last_date": last_date
                    })
                elif transaction.recurring_type == "weekly" and days_since_last >= 7:
                    reminders.append({
                        "type": "recurring_reminder",
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "frequency": "haftalık",
                        "last_date": last_date
                    })
                elif transaction.recurring_type == "monthly" and days_since_last >= 30:
                    reminders.append({
                        "type": "recurring_reminder",
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "frequency": "aylık",
                        "last_date": last_date
                    })
                elif transaction.recurring_type == "yearly" and days_since_last >= 365:
                    reminders.append({
                        "type": "recurring_reminder",
                        "category": transaction.category,
                        "amount": transaction.amount,
                        "frequency": "yıllık",
                        "last_date": last_date
                    })
        
        return reminders

    def get_all_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Tüm bildirimleri getirir."""
        notifications = []
        
        # Bütçe uyarıları
        notifications.extend(self.check_budget_alerts(user_id))
        
        # Hedef hatırlatmaları
        notifications.extend(self.check_goal_reminders(user_id))
        
        # Tekrarlayan işlem hatırlatmaları
        notifications.extend(self.check_recurring_transactions(user_id))
        
        # Bildirimleri tarihe göre sırala
        notifications.sort(key=lambda x: x.get("deadline", datetime.max))
        
        return notifications 