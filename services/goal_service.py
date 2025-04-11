from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.goal import Goal
from models.transaction import Transaction
from utils.db import db_session

class GoalService:
    """Finansal hedef (Goal) verilerini yöneten servis sınıfı."""
    
    def __init__(self):
        """Servis sınıfını başlatır."""
        pass
        
    def get_goals(self, limit: int = 100) -> List[Goal]:
        """Tüm hedefleri getirir."""
        with db_session() as session:
            return session.query(Goal).order_by(Goal.target_date.desc()).limit(limit).all()
    
    def get_goal_by_id(self, goal_id: int) -> Optional[Goal]:
        """Belirli bir hedefi ID'sine göre getirir."""
        with db_session() as session:
            return session.query(Goal).filter(Goal.id == goal_id).first()
    
    def get_goals_by_user(self, user_id: int) -> List[Goal]:
        """Belirli bir kullanıcıya ait hedefleri getirir."""
        with db_session() as session:
            return session.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.target_date).all()
    
    def get_active_goals(self, user_id: Optional[int] = None) -> List[Goal]:
        """Aktif (tamamlanmamış) hedefleri getirir."""
        today = datetime.now().date()
        with db_session() as session:
            query = session.query(Goal).filter(
                Goal.is_completed == False,
                Goal.target_date >= today
            )
            
            if user_id:
                query = query.filter(Goal.user_id == user_id)
                
            return query.order_by(Goal.target_date).all()
    
    def get_completed_goals(self, user_id: Optional[int] = None) -> List[Goal]:
        """Tamamlanmış hedefleri getirir."""
        with db_session() as session:
            query = session.query(Goal).filter(Goal.is_completed == True)
            
            if user_id:
                query = query.filter(Goal.user_id == user_id)
                
            return query.order_by(Goal.target_date.desc()).all()
    
    def calculate_progress(self, goal_id: int) -> Dict[str, Any]:
        """Hedefin ilerleme durumunu hesaplar."""
        with db_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            
            if not goal:
                return {
                    "target_amount": 0,
                    "current_amount": 0,
                    "remaining_amount": 0,
                    "percentage": 0,
                    "days_left": 0,
                    "projected_completion": None
                }
                
            today = datetime.now().date()
            days_left = (goal.target_date - today).days if goal.target_date > today else 0
            
            # Hedefle ilişkili işlemleri al (birikim işlemleri)
            transactions = session.query(Transaction).filter(
                Transaction.goal_id == goal_id
            ).all()
            
            current_amount = sum(t.amount for t in transactions if t.type == "saving")
            remaining_amount = goal.target_amount - current_amount
            percentage = (current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            
            # Tamamlanma projeksiyonu
            projected_completion = None
            if transactions and len(transactions) > 1 and remaining_amount > 0 and days_left > 0:
                # Ortalama günlük birikim hesapla
                start_date = min(t.date for t in transactions)
                days_passed = (today - start_date).days if today > start_date else 1
                daily_average = current_amount / days_passed
                
                if daily_average > 0:
                    days_to_complete = remaining_amount / daily_average
                    projected_completion = today + timedelta(days=days_to_complete)
            
            return {
                "target_amount": goal.target_amount,
                "current_amount": current_amount,
                "remaining_amount": remaining_amount,
                "percentage": min(percentage, 100),  # 100%'den fazla olmamalı
                "days_left": days_left,
                "projected_completion": projected_completion
            }
    
    def update_goal_status(self, goal_id: int) -> Optional[Goal]:
        """Hedefin durumunu günceller, tamamlandıysa işaretler."""
        progress = self.calculate_progress(goal_id)
        
        if progress["percentage"] >= 100:
            with db_session() as session:
                goal = session.query(Goal).filter(Goal.id == goal_id).first()
                if not goal:
                    return None
                    
                goal.is_completed = True
                goal.completion_date = datetime.now().date()
                session.commit()
                session.refresh(goal)
                return goal
        
        return None
    
    def create_goal(
        self,
        user_id: int,
        name: str,
        target_amount: float,
        target_date: datetime,
        description: str = "",
        category_id: Optional[int] = None
    ) -> Goal:
        """Yeni bir hedef oluşturur."""
        with db_session() as session:
            goal = Goal(
                user_id=user_id,
                name=name,
                target_amount=target_amount,
                target_date=target_date,
                description=description,
                category_id=category_id,
                is_completed=False,
                creation_date=datetime.now().date(),
                completion_date=None
            )
            session.add(goal)
            session.commit()
            session.refresh(goal)
            return goal
    
    def update_goal(
        self,
        goal_id: int,
        name: Optional[str] = None,
        target_amount: Optional[float] = None,
        target_date: Optional[datetime] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        is_completed: Optional[bool] = None
    ) -> Optional[Goal]:
        """Mevcut bir hedefi günceller."""
        with db_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return None
                
            if name is not None:
                goal.name = name
            if target_amount is not None:
                goal.target_amount = target_amount
            if target_date is not None:
                goal.target_date = target_date
            if description is not None:
                goal.description = description
            if category_id is not None:
                goal.category_id = category_id
            if is_completed is not None:
                goal.is_completed = is_completed
                if is_completed:
                    goal.completion_date = datetime.now().date()
                
            session.commit()
            session.refresh(goal)
            return goal
    
    def delete_goal(self, goal_id: int) -> bool:
        """Bir hedefi siler."""
        with db_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return False
                
            session.delete(goal)
            session.commit()
            return True
    
    def add_transaction_to_goal(self, goal_id: int, amount: float, description: str = "Hedef için birikim") -> Optional[Transaction]:
        """Hedefe bir birikim işlemi ekler."""
        with db_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                return None
                
            transaction = Transaction(
                user_id=goal.user_id,
                amount=amount,
                description=description,
                date=datetime.now().date(),
                type="saving",
                goal_id=goal_id,
                category_id=goal.category_id
            )
            
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            
            # Hedefin durumunu güncelle
            self.update_goal_status(goal_id)
            
            return transaction 