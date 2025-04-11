import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
from services.notification_service import NotificationService
from models.notification import Notification, NotificationType
from utils.db import db_session

def notification_badge(count: int = 0):
    """
    Bildirim sayısını gösteren badge bileşeni
    
    Args:
        count: Bildirim sayısı
    """
    if count > 0:
        st.markdown(f"""
            <div style="position: relative; display: inline-block;">
                <span style="position: absolute; top: -8px; right: -8px; 
                       background-color: #e74c3c; color: white; 
                       border-radius: 50%; width: 18px; height: 18px; 
                       display: flex; align-items: center; justify-content: center;
                       font-size: 12px; font-weight: bold;">
                    {count if count < 100 else '99+'}
                </span>
                <span style="font-size: 1.5rem;">🔔</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <span style="font-size: 1.5rem;">🔔</span>
        """, unsafe_allow_html=True)

def notification_item(notification: Dict[str, Any], on_read: callable = None, on_delete: callable = None):
    """
    Tek bir bildirim öğesi bileşeni
    
    Args:
        notification: Bildirim bilgileri
        on_read: Okundu işaretleme işlevi
        on_delete: Silme işlevi
    """
    # Bildirim tipi için renk kodu
    type_colors = {
        "SYSTEM": "#3498db",    # Mavi
        "TRANSACTION": "#2ecc71", # Yeşil
        "BUDGET": "#f39c12",    # Turuncu
        "GOAL": "#9b59b6",      # Mor
        "REPORT": "#34495e",    # Koyu gri
        "SECURITY": "#e74c3c",  # Kırmızı
        "REMINDER": "#1abc9c"   # Turkuaz
    }
    
    # Bildirim tipi için simge
    type_icons = {
        "SYSTEM": "ℹ️",       # Bilgi
        "TRANSACTION": "💸",   # Para
        "BUDGET": "📝",        # Not
        "GOAL": "🎯",          # Hedef
        "REPORT": "📊",        # Grafik
        "SECURITY": "🔒",      # Kilit
        "REMINDER": "⏰"       # Saat
    }
    
    # Bildirim tipi
    notification_type = notification.get("type", "SYSTEM")
    if isinstance(notification_type, NotificationType):
        notification_type = notification_type.value
    
    # Tarih formatı
    created_at = notification.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except:
            created_at = datetime.now()
    elif not isinstance(created_at, datetime):
        created_at = datetime.now()
    
    date_str = created_at.strftime("%d.%m.%Y %H:%M")
    
    # Okunma durumu için stil
    is_read = notification.get("is_read", False)
    bg_color = "#f8f9fa" if is_read else "#ffffff"
    border_left = f"4px solid {type_colors.get(notification_type, '#3498db')}"
    font_weight = "normal" if is_read else "bold"
    
    # Bildirim kartı
    st.markdown(f"""
        <div style="background-color: {bg_color}; 
                    border-left: {border_left}; 
                    padding: 12px 15px; 
                    margin-bottom: 10px; 
                    border-radius: 5px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.2rem; margin-right: 8px;">
                        {type_icons.get(notification_type, "ℹ️")}
                    </span>
                    <span style="font-weight: {font_weight}; color: #2c3e50;">
                        {notification.get('title', 'Bildirim')}
                    </span>
                </div>
                <small style="color: #7f8c8d;">{date_str}</small>
            </div>
            <p style="margin: 0 0 10px 0; color: #34495e;">
                {notification.get('message', '')}
            </p>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <span id="notification_{notification.get('id')}_read" style="cursor: pointer; color: #3498db;">
                    {'' if is_read else '✓ Okundu İşaretle'}
                </span>
                <span id="notification_{notification.get('id')}_delete" style="cursor: pointer; color: #e74c3c;">
                    🗑️ Sil
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # İşlemler için satır oluştur
    col1, col2 = st.columns([8, 2])
    with col2:
        # İşlem butonları
        if not is_read and on_read and st.button("Okundu", key=f"read_{notification.get('id')}"):
            on_read(notification.get('id'))
        
        if on_delete and st.button("Sil", key=f"delete_{notification.get('id')}"):
            on_delete(notification.get('id'))

def notification_center(max_notifications: int = 5):
    """
    Bildirim merkezi bileşeni
    
    Args:
        max_notifications: Gösterilecek maksimum bildirim sayısı
    """
    if "user_id" not in st.session_state:
        return
        
    user_id = st.session_state["user_id"]
    
    # Bildirim servisi oluştur
    with db_session() as session:
        notification_service = NotificationService(session)
        
        # Okunmamış bildirim sayısını al
        unread_count = notification_service.get_unread_count(user_id)
        
        # "Bildirimler" butonu
        col1, col2 = st.columns([1, 9])
        with col1:
            notification_badge(unread_count)
        with col2:
            st.markdown(f"### Bildirimler ({unread_count})")
        
        # Bildirim listesi container'ı
        with st.container():
            # Bildirim filtresi
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                show_unread_only = st.checkbox("Sadece Okunmamış", value=True)
            
            with filter_col2:
                notification_types = ["Tümü"] + [t.value for t in NotificationType]
                selected_type = st.selectbox("Bildirim Türü", notification_types)
            
            with filter_col3:
                time_filters = ["Son 7 gün", "Son 30 gün", "Tümü"]
                selected_time = st.selectbox("Zaman", time_filters)
            
            # Zaman filtresini güne çevir
            if selected_time == "Son 7 gün":
                days_back = 7
            elif selected_time == "Son 30 gün":
                days_back = 30
            else:
                days_back = None
            
            # Tür filtresini düzenle
            type_filter = None if selected_type == "Tümü" else selected_type
            
            # Bildirimleri getir
            notifications = notification_service.get_all_notifications(
                user_id=user_id,
                type_filter=type_filter,
                unread_only=show_unread_only,
                days_back=days_back,
                limit=max_notifications
            )
            
            # Bildirim yoksa mesaj göster
            if not notifications:
                st.info("Görüntülenecek bildirim bulunmuyor.")
            else:
                # Bildirimleri göster
                for notification in notifications:
                    # Bildirim gösterimi için yardımcı fonksiyon
                    def mark_as_read(notification_id):
                        notification_service.mark_as_read(notification_id, user_id)
                        st.experimental_rerun()
                    
                    def delete_notification(notification_id):
                        notification_service.delete_notification(notification_id, user_id)
                        st.experimental_rerun()
                    
                    notification_item(notification, mark_as_read, delete_notification)
            
            # Tümünü okundu işaretle butonu
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Tümünü Okundu İşaretle", use_container_width=True):
                    count = notification_service.mark_all_as_read(user_id)
                    st.success(f"{count} bildirim okundu olarak işaretlendi.")
                    st.experimental_rerun()
            
            with col2:
                if st.button("Tüm Bildirimleri Gör", use_container_width=True):
                    st.session_state.page = "Bildirimler"
                    st.switch_page("pages/notifications.py")

def mini_notification_center():
    """Kompakt bildirim merkezi"""
    if "user_id" not in st.session_state:
        return
        
    user_id = st.session_state["user_id"]
    
    # Bildirim servisi oluştur
    with db_session() as session:
        notification_service = NotificationService(session)
        
        # Okunmamış bildirim sayısını al
        unread_count = notification_service.get_unread_count(user_id)
        
        # Son 3 bildirimi al
        notifications = notification_service.get_user_notifications(
            user_id=user_id,
            limit=3,
            unread_only=True
        )
        
        # Buton ve popup
        if st.button(f"🔔 Bildirimler ({unread_count})", use_container_width=True):
            st.session_state.show_notifications = not st.session_state.get("show_notifications", False)
        
        if st.session_state.get("show_notifications", False):
            with st.container():
                if not notifications:
                    st.info("Okunmamış bildirim bulunmuyor.")
                else:
                    for notification in notifications:
                        # Dict formatına dönüştür
                        notification_dict = {
                            "id": notification.id,
                            "title": notification.title,
                            "message": notification.message,
                            "type": notification.type,
                            "is_read": notification.is_read,
                            "created_at": notification.created_at
                        }
                        
                        # Bildirim göster
                        notification_item(notification_dict)
                
                # Tüm bildirimler sayfasına yönlendirme butonu
                if st.button("Tüm Bildirimleri Gör", key="goto_all_notifications"):
                    st.session_state.page = "Bildirimler"
                    st.switch_page("pages/notifications.py")

if __name__ == "__main__":
    st.set_page_config(page_title="Bildirim Merkezi", layout="wide")
    st.title("Bildirim Merkezi")
    notification_center() 