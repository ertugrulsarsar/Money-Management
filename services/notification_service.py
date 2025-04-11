from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from models.database import Transaction, Budget, FinancialGoal
from models.notification import Notification, NotificationType
from models.notification_preferences import NotificationPreferences, NotificationChannel
from models.user import User
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from models.user_preferences import UserPreferences
from config import settings  # Sadece settings'i import et
from services.user_service import UserService
import json
from services.email_service import EmailService
from utils.db import db_session

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, db: Session, email_service: Optional[EmailService] = None):
        self.db = db
        self.user_service = UserService(db)
        self.email_service = email_service or EmailService()
        self.email_config = {
            "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
            "sender_email": os.environ.get("SENDER_EMAIL", "finans.app@example.com"),
            "sender_password": os.environ.get("SENDER_PASSWORD", ""),
        }

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

    def get_all_notifications(self, user_id: int, 
                             type_filter: Optional[str] = None,
                             unread_only: bool = False,
                             days_back: int = 30,
                             limit: int = 100) -> List[Dict]:
        """
        Kullanıcının tüm bildirimlerini listeler.
        """
        try:
            query = self.db.query(Notification).filter(Notification.user_id == user_id)
            
            # Tip filtresi
            if type_filter:
                query = query.filter(Notification.type == type_filter)
                
            # Sadece okunmamış
            if unread_only:
                query = query.filter(Notification.is_read == False)
                
            # Tarih filtresi
            if days_back:
                date_threshold = datetime.now() - timedelta(days=days_back)
                query = query.filter(Notification.created_at >= date_threshold)
                
            # Sıralama ve limit
            query = query.order_by(Notification.created_at.desc()).limit(limit)
            
            # Sonuçları al
            notifications = query.all()
            
            # Dict formatına dönüştür
            result = []
            for notification in notifications:
                notification_dict = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at,
                }
                
                # Data varsa ekle
                if notification.data:
                    notification_dict.update(notification.data)
                    
                result.append(notification_dict)
                
            return result
        except Exception as e:
            logger.error(f"Bildirimler alınırken hata: {str(e)}")
            return []

    def get_user_notifications(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0, 
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Kullanıcının bildirimlerini getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            limit: Maksimum bildirim sayısı
            offset: Sayfalama başlangıç noktası
            unread_only: Sadece okunmamış bildirimleri getir
            
        Returns:
            Bildirim listesi
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        return notifications
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Kullanıcının okunmamış bildirim sayısını döndürür.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Okunmamış bildirim sayısı
        """
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Notification]:
        """
        Bildirimi okundu olarak işaretler.
        
        Args:
            notification_id: Bildirim ID'si
            user_id: Kullanıcı ID'si (güvenlik kontrolü için)
            
        Returns:
            Güncellenen bildirim nesnesi veya bulunamazsa None
        """
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.now()
            self.db.commit()
            self.db.refresh(notification)
            
        return notification
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Kullanıcının tüm bildirimlerini okundu olarak işaretler.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            İşaretlenen bildirim sayısı
        """
        now = datetime.now()
        result = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({
            "is_read": True,
            "read_at": now
        })
        
        self.db.commit()
        return result
    
    def create_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        notification_type: NotificationType,
        source_id: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None,
        send_email: bool = True
    ) -> Notification:
        """
        Yeni bir bildirim oluşturur ve kullanıcının tercihlerine göre kanallar üzerinden iletir.
        
        Args:
            user_id: Bildirim alıcısının ID'si
            title: Bildirim başlığı
            message: Bildirim mesajı
            notification_type: Bildirim türü (NotificationType enum)
            source_id: İlgili işlemin/kaynağın ID'si (varsa)
            data: Bildirim ile ilgili ekstra veriler (JSON olarak saklanır)
            channels: Hangi kanallar üzerinden bildirim gönderileceği (None ise tercihler kontrol edilir)
            send_email: E-posta bildirimi gönderilecek mi
        
        Returns:
            Oluşturulan bildirim nesnesi
        """
        try:
            with db_session() as session:
                # Kullanıcının var olup olmadığını kontrol et
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    logger.error(f"Bildirim oluşturulamadı: Kullanıcı bulunamadı (ID: {user_id})")
                    return None
                
                # Bildirim tercihleri
                preferences = self._get_user_preferences(user_id)
                
                # Bildirim verisini JSON formatına dönüştür
                data_json = json.dumps(data) if data else None
                
                # Bildirim oluştur ve veritabanına kaydet
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    type=notification_type,
                    is_read=False,
                    created_at=datetime.now(),
                    source_id=source_id,
                    data=data_json
                )
                
                session.add(notification)
                session.flush()  # ID oluşturmak için önce flush et
                
                # Bildirim kanallarını belirle
                if channels is None:
                    channels = []
                    # Uygulama içi bildirim tercihi kontrolü
                    if preferences.get_channel_preference(notification_type.name.lower(), NotificationChannel.APP.value):
                        channels.append(NotificationChannel.APP)
                    
                    # E-posta bildirimi tercihi kontrolü
                    if preferences.get_channel_preference(notification_type.name.lower(), NotificationChannel.EMAIL.value):
                        channels.append(NotificationChannel.EMAIL)
                
                # Bildirimi kanallara gönder
                for channel in channels:
                    try:
                        if channel == NotificationChannel.EMAIL:
                            self._send_email_notification(user, notification)
                        # Uygulama içi bildirimler otomatik olarak veritabanına kaydedildi
                    except Exception as e:
                        logger.error(f"Bildirim gönderme hatası ({channel}): {str(e)}")
                
                session.commit()
                logger.info(f"Bildirim oluşturuldu: ID={notification.id}, User={user_id}, Type={notification_type}")
                return notification
                
        except Exception as e:
            logger.error(f"Bildirim oluşturulurken hata oluştu: {str(e)}")
            return None
    
    def _get_user_preferences(self, user_id: int) -> NotificationPreferences:
        """
        Kullanıcının bildirim tercihlerini getirir, yoksa yeni oluşturur.
        
        Args:
            user_id: Kullanıcı ID'si
            
        Returns:
            Kullanıcının bildirim tercihleri
        """
        preferences = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == user_id
        ).first()
        
        # Kullanıcının bildirim tercihi yoksa yeni oluştur
        if not preferences:
            preferences = NotificationPreferences(user_id=user_id)
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
        return preferences
    
    def update_notification_preferences(
        self, 
        user_id: int, 
        preferences: Dict[str, bool]
    ) -> NotificationPreferences:
        """
        Kullanıcının bildirim tercihlerini günceller.
        
        Args:
            user_id: Kullanıcı ID'si
            preferences: Güncellenecek tercihler sözlüğü
            
        Returns:
            Güncellenen bildirim tercihleri nesnesi
        """
        user_prefs = self._get_user_preferences(user_id)
        
        # Tercihleri güncelle
        for key, value in preferences.items():
            if hasattr(user_prefs, key):
                setattr(user_prefs, key, value)
        
        self.db.commit()
        self.db.refresh(user_prefs)
        return user_prefs
    
    def _send_email_notification(self, user: User, notification: Notification) -> bool:
        """
        Bildirim e-postası gönderir.
        
        Args:
            user: Kullanıcı nesnesi
            notification: Bildirim nesnesi
            
        Returns:
            bool: Başarılı ise True, değilse False
        """
        try:
            # Kullanıcı tercihlerini kontrol et
            preferences = self._get_user_preferences(user.id)
            notification_type = notification.type.lower() if hasattr(notification.type, 'lower') else str(notification.type).lower()
            
            # Bu bildirim türü için e-posta gönderilmeyecekse hemen çık
            email_pref_field = f"{notification_type}_email"
            if hasattr(preferences, email_pref_field) and not getattr(preferences, email_pref_field):
                logger.info(f"Kullanıcının {notification_type} için e-posta tercihi kapalı: user_id={user.id}")
                return False
                
            # E-posta servisimiz yapılandırılmışsa, onu kullan
            if self.email_service.is_configured():
                return self.email_service.send_notification_email(user, notification)
                
            # Eski e-posta gönderme yöntemi (varsayılan)
            # SMTP ayarları kontrol et
            if not all([self.email_config["smtp_server"], 
                      str(self.email_config["smtp_port"]), 
                      self.email_config["sender_email"]]):
                logger.error("E-posta ayarları tamamlanmamış.")
                return False
            
            # Alıcı e-postası kontrol et
            if not user.email:
                logger.error(f"Kullanıcının e-posta adresi yok: user_id={user.id}")
                return False
            
            # E-posta içeriği hazırla
            subject = f"Kişisel Finans Bildirimi: {notification.title}"
            
            # Bildirim tipine özel içerik oluştur
            if notification.type == NotificationType.BUDGET:
                message = f"""
                <h2>Bütçe Uyarısı</h2>
                <p>{notification.message}</p>
                <p><a href="https://kisisel-finans.streamlit.app/pages/budgets">Bütçelerinizi incelemek için tıklayın</a></p>
                """
            elif notification.type == NotificationType.GOAL:
                message = f"""
                <h2>Finansal Hedef Bildirimi</h2>
                <p>{notification.message}</p>
                <p><a href="https://kisisel-finans.streamlit.app/pages/goals">Hedeflerinizi incelemek için tıklayın</a></p>
                """
            else:
                message = f"""
                <h2>{notification.title}</h2>
                <p>{notification.message}</p>
                """
                
            # HTML formatında e-posta
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #3498db; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
                    .notification {{ border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; background-color: white; }}
                    .footer {{ font-size: 12px; text-align: center; margin-top: 20px; color: #888; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Kişisel Finans</h2>
                    </div>
                    <div class="content">
                        <h3>Merhaba {user.username},</h3>
                        <div class="notification">
                            {message}
                        </div>
                    </div>
                    <div class="footer">
                        <p>Bu e-posta Kişisel Finans uygulaması tarafından otomatik olarak gönderilmiştir.</p>
                        <p>Bildirim tercihlerinizi değiştirmek için <a href="http://finans.app/settings">ayarlar sayfasını</a> ziyaret edebilirsiniz.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # E-posta oluştur
            msg = MIMEMultipart()
            msg['From'] = self.email_config["sender_email"]
            msg['To'] = user.email
            msg['Subject'] = subject
            
            # HTML içerik ekle
            msg.attach(MIMEText(html_content, 'html'))
            
            # SMTP sunucuya bağlan
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            
            # Şifre varsa giriş yap
            if self.email_config["sender_password"]:
                server.login(self.email_config["sender_email"], self.email_config["sender_password"])
            
            # E-postayı gönder
            server.send_message(msg)
            server.quit()
            
            logger.info(f"E-posta gönderildi: user_id={user.id}, email={user.email}, notification_id={notification.id}")
            return True
            
        except Exception as e:
            logger.error(f"E-posta gönderirken hata: {str(e)}")
            return False

    def get_notification(self, notification_id: int) -> Notification:
        """
        ID'ye göre bildirimi alır.
        """
        return self.db.query(Notification).filter(Notification.id == notification_id).first()
    
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """
        Bildirimi siler.
        
        Args:
            notification_id: Bildirim ID'si
            user_id: Kullanıcı ID'si (güvenlik kontrolü için)
            
        Returns:
            Silme işlemi başarılıysa True, değilse False
        """
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            self.db.delete(notification)
            self.db.commit()
            return True
            
        return False
    
    def delete_old_notifications(self, user_id: int, days: int = 90) -> int:
        """
        Belirli bir süreden eski bildirimleri siler.
        """
        try:
            date_threshold = datetime.now() - timedelta(days=days)
            result = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.created_at < date_threshold
            ).delete()
            
            self.db.commit()
            return result  # Silinen satır sayısı
        except Exception as e:
            self.db.rollback()
            logger.error(f"Eski bildirimler silinirken hata: {str(e)}")
            return 0
    
    def update_user_preferences(self, user_id: int, email: str = None, 
                              email_notifications: bool = None,
                              push_notifications: bool = None,
                              notification_types: List[str] = None) -> bool:
        """
        Kullanıcının bildirim tercihlerini günceller.
        """
        try:
            # Kullanıcı tercihlerini al veya oluştur
            user_pref = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
            
            if not user_pref:
                user_pref = UserPreferences(user_id=user_id)
                self.db.add(user_pref)
            
            # Değerleri güncelle
            if email is not None:
                user_pref.email = email
                
            if email_notifications is not None:
                user_pref.email_notifications = email_notifications
                
            if push_notifications is not None:
                user_pref.push_notifications = push_notifications
                
            if notification_types is not None:
                user_pref.notification_types = notification_types
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Kullanıcı tercihleri güncellenirken hata: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Kullanıcının bildirim tercihlerini alır.
        """
        try:
            user_pref = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
            
            if not user_pref:
                return {
                    "email": "",
                    "email_notifications": False,
                    "push_notifications": True,
                    "notification_types": ["all"]
                }
            
            return {
                "email": user_pref.email,
                "email_notifications": user_pref.email_notifications,
                "push_notifications": user_pref.push_notifications,
                "notification_types": user_pref.notification_types
            }
        except Exception as e:
            logger.error(f"Kullanıcı tercihleri alınırken hata: {str(e)}")
            return {
                "email": "",
                "email_notifications": False,
                "push_notifications": True,
                "notification_types": ["all"]
            }
    
    def get_notification_count(self, user_id: int, unread_only: bool = True) -> int:
        """
        Kullanıcının bildirim sayısını alır.
        """
        try:
            query = self.db.query(Notification).filter(Notification.user_id == user_id)
            
            if unread_only:
                query = query.filter(Notification.is_read == False)
                
            return query.count()
        except Exception as e:
            logger.error(f"Bildirim sayısı alınırken hata: {str(e)}")
            return 0 