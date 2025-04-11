from sqlalchemy.orm import Session
from models.database import User, Transaction, Budget, FinancialGoal
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from utils.logger import FinanceLogger
from sqlalchemy import func, desc, and_
from functools import lru_cache

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
        self.logger = FinanceLogger()

    # Kullanıcı işlemleri
    def create_user(self, username: str, email: str, hashed_password: str) -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Log kaydı
        self.logger.log_transaction(
            user_id=user.id,
            action="create_user",
            data={"username": username, "email": email}
        )
        
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    @lru_cache(maxsize=100)
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Kullanıcı adına göre kullanıcıyı getirir."""
        return self.db.query(User).filter(User.username == username).first()

    @lru_cache(maxsize=100)
    def get_user_by_email(self, email: str) -> Optional[User]:
        """E-posta adresine göre kullanıcıyı getirir."""
        return self.db.query(User).filter(User.email == email).first()

    def add_user(self, user: User) -> None:
        """Kullanıcıyı veritabanına ekler."""
        self.db.add(user)
        self.logger.log_user_action(user.id, "create", {"username": user.username, "email": user.email})

    def commit(self) -> None:
        """Değişiklikleri kaydeder."""
        self.db.commit()

    def refresh(self, obj: object) -> None:
        """Nesneyi yeniler."""
        self.db.refresh(obj)

    @lru_cache(maxsize=100)
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ID'ye göre kullanıcıyı getirir."""
        return self.db.query(User).filter(User.id == user_id).first()

    def delete_user(self, user: User) -> None:
        """Kullanıcıyı veritabanından siler."""
        self.db.delete(user)
        self.logger.log_user_action(user.id, "delete", {"username": user.username, "email": user.email})

    # İşlem işlemleri
    def create_transaction(
        self,
        user_id: int,
        amount: float,
        type: str,
        category: str,
        description: str,
        date: date,
        is_recurring: bool = False,
        recurring_type: Optional[str] = None
    ) -> Transaction:
        """Yeni işlem oluşturur."""
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            type=type,
            category=category,
            description=description,
            date=date,
            is_recurring=is_recurring,
            recurring_type=recurring_type
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        self.logger.log_transaction(
            user_id,
            "create",
            {
                "amount": amount,
                "type": type,
                "category": category,
                "description": description,
                "date": date.isoformat(),
                "is_recurring": is_recurring,
                "recurring_type": recurring_type
            }
        )
        
        return transaction

    def get_user_transactions(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 10,
        transaction_type: Optional[str] = None,
        category: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source_filter: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> Dict:
        """
        Kullanıcının işlemlerini getirir.
        """
        # Toplam işlem sayısı
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Filtreleme
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        if category:
            query = query.filter(Transaction.category == category)
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        if source_filter:
            query = query.filter(Transaction.source.like(f"{source_filter}%"))
        if days_back:
            past_date = datetime.now().date() - timedelta(days=days_back)
            query = query.filter(Transaction.date >= past_date)
            
        total_transactions = query.count()
        
        # Toplam sayfa sayısı
        total_pages = (total_transactions + per_page - 1) // per_page
        
        # İşlemleri getir
        transactions = query.order_by(
            Transaction.date.desc()
        ).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return {
            "transactions": transactions,
            "total": total_transactions,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    @lru_cache(maxsize=100)
    def get_transaction_summary(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> Dict:
        """Belirli bir tarih aralığındaki işlem özetini getirir."""
        # SQL ile direkt hesaplama
        result = self.db.query(
            func.sum(Transaction.amount).filter(Transaction.type == "income").label("total_income"),
            func.sum(Transaction.amount).filter(Transaction.type == "expense").label("total_expense")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).first()

        total_income = result.total_income or 0
        total_expense = result.total_expense or 0
        net_amount = total_income - total_expense

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": net_amount
        }

    # Bütçe işlemleri
    def create_budget(
        self,
        user_id: int,
        category: str,
        amount: float,
        period: str,
        start_date: date,
        end_date: date
    ) -> Budget:
        """Yeni bütçe oluşturur."""
        budget = Budget(
            user_id=user_id,
            category=category,
            amount=amount,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        
        self.logger.log_budget(
            user_id,
            "create",
            {
                "category": category,
                "amount": amount,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        
        return budget

    def get_user_budgets(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 50,
        active_only: bool = True
    ) -> Dict:
        """Kullanıcının bütçelerini sayfalı olarak getirir."""
        query = self.db.query(Budget).filter(Budget.user_id == user_id)
        
        if active_only:
            query = query.filter(
                and_(
                    Budget.start_date <= date.today(),
                    Budget.end_date >= date.today()
                )
            )
        
        # Toplam kayıt sayısı
        total_count = query.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Sayfalama
        budgets = query.order_by(Budget.start_date.desc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "budgets": budgets,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }

    # Hedef işlemleri
    def create_goal(
        self,
        user_id: int,
        name: str,
        target_amount: float,
        current_amount: float,
        deadline: date,
        priority: str
    ) -> FinancialGoal:
        """Yeni finansal hedef oluşturur."""
        goal = FinancialGoal(
            user_id=user_id,
            name=name,
            target_amount=target_amount,
            current_amount=current_amount,
            deadline=deadline,
            priority=priority
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        
        self.logger.log_goal(
            user_id,
            "create",
            {
                "name": name,
                "target_amount": target_amount,
                "current_amount": current_amount,
                "deadline": deadline.isoformat(),
                "priority": priority
            }
        )
        
        return goal

    def get_user_goals(
        self, 
        user_id: int, 
        page: int = 1, 
        per_page: int = 50,
        active_only: bool = True
    ) -> Dict:
        """Kullanıcının hedeflerini sayfalı olarak getirir."""
        query = self.db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id)
        
        if active_only:
            query = query.filter(FinancialGoal.deadline >= date.today())
        
        # Toplam kayıt sayısı
        total_count = query.count()
        total_pages = (total_count + per_page - 1) // per_page
        
        # Sayfalama
        goals = query.order_by(FinancialGoal.deadline.asc())\
            .offset((page - 1) * per_page)\
            .limit(per_page)\
            .all()
        
        return {
            "goals": goals,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page
        }

    def update_goal_progress(self, goal_id: int, current_amount: float) -> Optional[FinancialGoal]:
        """Hedef ilerlemesini günceller."""
        goal = self.db.query(FinancialGoal).filter(FinancialGoal.id == goal_id).first()
        if goal:
            goal.current_amount = current_amount
            self.db.commit()
            self.db.refresh(goal)
            
            self.logger.log_goal(
                goal.user_id,
                "update",
                {
                    "goal_id": goal_id,
                    "current_amount": current_amount,
                    "progress": (current_amount / goal.target_amount) * 100
                }
            )
        
        return goal

    def get_category_summary(
        self, 
        user_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[Dict]:
        """Kategori bazlı özet bilgileri getirir."""
        result = self.db.query(
            Transaction.category,
            func.sum(Transaction.amount).filter(Transaction.type == "expense").label("total_expense"),
            func.count().label("transaction_count")
        ).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.type == "expense"
        ).group_by(Transaction.category).all()

        return [
            {
                "category": row.category,
                "total_expense": row.total_expense or 0,
                "transaction_count": row.transaction_count
            }
            for row in result
        ]

    def get_monthly_summary(
        self, 
        user_id: int, 
        year: int, 
        month: int
    ) -> Dict:
        """Aylık özet bilgileri getirir."""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # İşlem özeti
        transaction_summary = self.get_transaction_summary(user_id, start_date, end_date)
        
        # Kategori özeti
        category_summary = self.get_category_summary(user_id, start_date, end_date)
        
        # Aktif bütçeler
        active_budgets = self.get_user_budgets(user_id, active_only=True)["budgets"]
        
        # Aktif hedefler
        active_goals = self.get_user_goals(user_id, active_only=True)["goals"]

        return {
            "transaction_summary": transaction_summary,
            "category_summary": category_summary,
            "active_budgets": active_budgets,
            "active_goals": active_goals
        }

    def clear_cache(self):
        """Önbelleği temizler."""
        self.get_user_by_username.cache_clear()
        self.get_user_by_email.cache_clear()
        self.get_user_by_id.cache_clear()
        self.get_transaction_summary.cache_clear()

    # Yedekleme ve geri yükleme işlemleri
    def restore_from_backup(self, category: str) -> bool:
        """Yedekten veri geri yükler."""
        try:
            if category == "transactions":
                self.logger.restore_transactions(self.db)
            elif category == "budgets":
                self.logger.restore_budgets(self.db)
            elif category == "goals":
                self.logger.restore_goals(self.db)
            else:
                return False
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise e 

    def get_user_transaction_categories(self, user_id: int) -> List[str]:
        """
        Kullanıcının tüm işlem kategorilerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Benzersiz kategorilerin listesi
        """
        categories = self.db.query(Transaction.category).filter(
            Transaction.user_id == user_id
        ).distinct().all()
        
        return [category[0] for category in categories] 