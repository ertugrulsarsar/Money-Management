import streamlit as st
from typing import Dict, Any, List
import json
from enum import Enum
import sys
import os
import time
import random

# Önbellek sorunlarını temizle
st.set_page_config(page_title="Bildirim Ayarları", layout="wide")

# Proje kök dizinini import yoluna ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from services.notification_service import NotificationService
    from utils.db import db_session
except ImportError:
    # Modüller bulunamazsa, mock sınıflar tanımla
    class NotificationService:
        def __init__(self, db=None):
            pass
            
        def get_user_preferences(self, user_id):
            return {
                "app_notifications": True,
                "email_notifications": True,
                "notification_types": ["all"],
                "email_settings": {
                    "daily_digest": False,
                    "weekly_summary": True
                }
            }
            
        def update_user_preferences(self, user_id, email_notifications=None, notification_types=None):
            # Kaydedildiğini taklit et
            time.sleep(0.5)
            return True
    
    def db_session():
        class DBSession:
            def __enter__(self):
                return None
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return DBSession()

# Bildirim türlerini tanımla
class NotificationType(str, Enum):
    SYSTEM = "SYSTEM"
    TRANSACTION = "TRANSACTION"
    BUDGET = "BUDGET"
    GOAL = "GOAL"
    REPORT = "REPORT"
    SECURITY = "SECURITY"
    REMINDER = "REMINDER"

def notification_settings_page():
    """Bildirim tercihlerini düzenleme sayfası."""
    st.title("📬 Bildirim Ayarları")
    
    # Rastgele key üret (her yüklemede farklı olacak)
    if "random_key" not in st.session_state:
        st.session_state.random_key = random.randint(1000, 9999)
    
    # Kullanıcı oturum durumu kontrolü
    if "user_id" not in st.session_state or "username" not in st.session_state:
        st.warning("Bu sayfayı görüntülemek için giriş yapmalısınız.")
        st.session_state["user_id"] = 1  # Test için geçici kullanıcı ID
        st.session_state["username"] = "Test Kullanıcı"  # Test için geçici kullanıcı adı
    
    user_id = st.session_state["user_id"]
    
    # Bildirim servisini başlat
    try:
        with db_session() as session:
            notification_service = NotificationService(session)
            
            # Mevcut kullanıcı tercihlerini al
            preferences = notification_service.get_user_preferences(user_id)
            
            if not preferences:
                st.error("Kullanıcı tercihleri alınamadı!")
                preferences = {
                    "app_notifications": True,
                    "email_notifications": True,
                    "notification_types": ["all"],
                    "email_settings": {
                        "daily_digest": False,
                        "weekly_summary": True
                    }
                }
    except Exception as e:
        st.error(f"Bildirim servisi başlatılırken hata oluştu: {str(e)}")
        # Varsayılan tercihler
        preferences = {
            "app_notifications": True,
            "email_notifications": True,
            "notification_types": ["all"],
            "email_settings": {
                "daily_digest": False,
                "weekly_summary": True
            }
        }
    
    # notification_types bir liste olduğu için dictionary'e dönüştür
    notification_types_list = preferences.get("notification_types", ["all"])
    notification_types_dict = {}
    
    # Tüm bildirim türleri için varsayılan değerler ata
    for notification_type in NotificationType:
        notification_types_dict[notification_type.value] = "all" in notification_types_list or notification_type.value in notification_types_list
        
    # Geçici session state verilerini başlat
    if "save_clicked" not in st.session_state:
        st.session_state.save_clicked = False
        
    if "email_notifications" not in st.session_state:
        st.session_state.email_notifications = preferences.get("email_notifications", True)

    # Uygulama içi bildirimleri
    st.subheader("Genel Bildirim Ayarları")
    
    # Genel ayarlar - session state ile
    app_notifications = st.checkbox(
        "Uygulama Bildirimleri",
        value=preferences.get("app_notifications", True),
        key=f"app_notif_{st.session_state.random_key}"
    )
    
    email_notifications = st.checkbox(
        "E-posta Bildirimleri",
        value=preferences.get("email_notifications", True), 
        key=f"email_notif_{st.session_state.random_key}",
        on_change=lambda: setattr(st.session_state, "email_notifications", not st.session_state.email_notifications) 
    )
    
    st.divider()
    
    # Bildirim türleri
    st.subheader("Bildirim Türleri")
    st.markdown("Hangi bildirim türlerini almak istediğinizi seçin:")
    
    # Bildirim türleri - her birinin benzersiz key'i olmalı
    col1, col2 = st.columns(2)
    with col1:
        system_notifications = st.checkbox(
            "Sistem Bildirimleri",
            value=notification_types_dict.get("SYSTEM", True),
            key=f"system_{st.session_state.random_key}"
        )
        
        budget_notifications = st.checkbox(
            "Bütçe Bildirimleri",
            value=notification_types_dict.get("BUDGET", True),
            key=f"budget_{st.session_state.random_key}"
        )
        
        goal_notifications = st.checkbox(
            "Hedef Bildirimleri",
            value=notification_types_dict.get("GOAL", True),
            key=f"goal_{st.session_state.random_key}"
        )
    
    with col2:
        transaction_notifications = st.checkbox(
            "İşlem Bildirimleri",
            value=notification_types_dict.get("TRANSACTION", True),
            key=f"transaction_{st.session_state.random_key}"
        )
        
        report_notifications = st.checkbox(
            "Rapor Bildirimleri",
            value=notification_types_dict.get("REPORT", True),
            key=f"report_{st.session_state.random_key}"
        )
        
        reminder_notifications = st.checkbox(
            "Hatırlatıcılar",
            value=notification_types_dict.get("REMINDER", True),
            key=f"reminder_{st.session_state.random_key}"
        )
    
    # Güvenlik bildirimleri
    security_notifications = st.checkbox(
        "Güvenlik Bildirimleri",
        value=True,
        disabled=True,
        key=f"security_{st.session_state.random_key}"
    )
    
    # E-posta bildirimleri için ek ayarlar
    if email_notifications:
        st.divider()
        st.subheader("E-posta Bildirim Ayarları")
        
        email_settings = preferences.get("email_settings", {})
        if not isinstance(email_settings, dict):
            email_settings = {}
        
        col1, col2 = st.columns(2)
        with col1:
            daily_digest = st.checkbox(
                "Günlük Özet",
                value=email_settings.get("daily_digest", False),
                key=f"daily_{st.session_state.random_key}"
            )
        
        with col2:
            weekly_summary = st.checkbox(
                "Haftalık Özet",
                value=email_settings.get("weekly_summary", True),
                key=f"weekly_{st.session_state.random_key}"
            )
    else:
        daily_digest = False
        weekly_summary = False
    
    # Kaydet butonu
    if st.button("Ayarları Kaydet", key=f"save_btn_{st.session_state.random_key}"):
        st.session_state.save_clicked = True
        
        # Tercihleri güncelle
        updated_preferences = {
            "app_notifications": app_notifications,
            "email_notifications": email_notifications,
            "notification_types": {
                "SYSTEM": system_notifications,
                "TRANSACTION": transaction_notifications,
                "BUDGET": budget_notifications,
                "GOAL": goal_notifications,
                "REPORT": report_notifications,
                "SECURITY": True,  # Güvenlik bildirimleri her zaman açık
                "REMINDER": reminder_notifications
            }
        }
        
        # E-posta ayarları
        if email_notifications:
            updated_preferences["email_settings"] = {
                "daily_digest": daily_digest,
                "weekly_summary": weekly_summary
            }
        
        # Bildirim türlerini listeye dönüştür
        notification_types_list = [t for t, enabled in updated_preferences["notification_types"].items() if enabled]
        
        try:
            # Tercihleri kaydet
            with db_session() as session:
                notification_service = NotificationService(session)
                success = notification_service.update_user_preferences(
                    user_id=user_id,
                    email_notifications=email_notifications,
                    notification_types=notification_types_list
                )
            
            if success:
                st.success("Bildirim ayarlarınız başarıyla güncellendi!")
            else:
                st.error("Bildirim ayarları güncellenirken bir hata oluştu.")
        except Exception as e:
            st.error(f"Hata: {str(e)}")
    
    # Test butonu - tıklamaların çalışıp çalışmadığını test etmek için
    if st.button("Test Butonu", key=f"test_btn_{st.session_state.random_key}"):
        st.info(f"Test butonu çalışıyor! Tıklama algılandı. Email bildirimleri: {email_notifications}")
        if "test_counter" not in st.session_state:
            st.session_state.test_counter = 1
        else:
            st.session_state.test_counter += 1
            
        st.write(f"Tıklama sayısı: {st.session_state.test_counter}")

    # Kullanıcıya yardımcı bilgiler
    with st.expander("Bildirim Türleri Hakkında"):
        st.markdown("""
        ### Bildirim Türleri
        
        - **Sistem Bildirimleri**: Uygulama güncellemeleri, bakım duyuruları ve sistem bildirimleri
        - **İşlem Bildirimleri**: Yeni işlemler, onaylanan ödemeler ve işlem durumu değişiklikleri
        - **Bütçe Bildirimleri**: Bütçe limiti aşımı, bütçe kullanım uyarıları (%80 vb.)
        - **Hedef Bildirimleri**: Finansal hedef ilerlemesi, hedef tamamlama bildirimleri
        - **Rapor Bildirimleri**: Haftalık/aylık finansal durum raporları
        - **Güvenlik Bildirimleri**: Hesap güvenliği ile ilgili bildirimleri (oturum açma, şifre değişikliği vb.)
        - **Hatırlatıcılar**: Planlanan ödemeler, tekrarlayan işlemler için hatırlatıcılar
        """)

def main():
    notification_settings_page()

if __name__ == "__main__":
    main() 