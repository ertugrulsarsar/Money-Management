import streamlit as st
import os
import base64

# Renk temaları
PRIMARY_COLOR = "#3498db"    # Mavi
SECONDARY_COLOR = "#e74c3c"  # Kırmızı
ACCENT_COLOR = "#2ecc71"     # Yeşil
NEUTRAL_COLOR = "#95a5a6"    # Gri
BACKGROUND_COLOR = "#f8f9fa" # Açık gri
TEXT_COLOR = "#2c3e50"       # Koyu mavi-gri

# Font ayarları
FONT_FAMILY = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
FONT_SIZE_SMALL = "12px"
FONT_SIZE_MEDIUM = "14px"
FONT_SIZE_LARGE = "16px"
FONT_SIZE_XLARGE = "20px"
FONT_SIZE_XXLARGE = "24px"

# Sayfa yapılandırması
APP_TITLE = "Kişisel Finans"
APP_ICON = "💰"
APP_DESCRIPTION = "Kişisel finans yönetim uygulaması"

# Veritabanı yapılandırması
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "finance.db")

# İşlemler için varsayılan kategoriler
DEFAULT_INCOME_CATEGORIES = [
    {"name": "Maaş", "color": "#27ae60", "icon": "briefcase"},
    {"name": "Yatırım", "color": "#8e44ad", "icon": "chart-line"},
    {"name": "Ek Gelir", "color": "#f39c12", "icon": "coins"},
    {"name": "Hediye", "color": "#e67e22", "icon": "gift"},
    {"name": "Diğer Gelir", "color": "#3498db", "icon": "plus-circle"}
]

DEFAULT_EXPENSE_CATEGORIES = [
    {"name": "Gıda", "color": "#e74c3c", "icon": "utensils"},
    {"name": "Ulaşım", "color": "#9b59b6", "icon": "car"},
    {"name": "Konaklama", "color": "#f1c40f", "icon": "home"},
    {"name": "Eğlence", "color": "#1abc9c", "icon": "music"},
    {"name": "Alışveriş", "color": "#e84393", "icon": "shopping-bag"},
    {"name": "Faturalar", "color": "#00cec9", "icon": "file-invoice"},
    {"name": "Sağlık", "color": "#d63031", "icon": "medkit"},
    {"name": "Eğitim", "color": "#6c5ce7", "icon": "book"},
    {"name": "Diğer Gider", "color": "#636e72", "icon": "minus-circle"}
]

# Bildirim ayarları
NOTIFICATION_TYPES = [
    {"id": "budget_exceeded", "name": "Bütçe Aşımı", "description": "Bir bütçe limit aşımında bildirim gönderir."},
    {"id": "goal_progress", "name": "Hedef İlerlemesi", "description": "Finansal hedeflerin ilerlemesi hakkında bildirim gönderir."},
    {"id": "weekly_summary", "name": "Haftalık Özet", "description": "Haftalık finans durumu özeti gönderir."},
    {"id": "monthly_summary", "name": "Aylık Özet", "description": "Aylık finans durumu özeti gönderir."},
    {"id": "large_transaction", "name": "Büyük İşlem", "description": "Belirlenen limitin üzerindeki işlemler için bildirim gönderir."}
]

# E-posta gönderimi için ayarlar
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_SENDER = "Kişisel Finans <your-email@gmail.com>"

# Uygulama sürümü
APP_VERSION = "1.0.0"

# Çeşitli sabitler
MAX_TRANSACTIONS_PER_PAGE = 20
MAX_BUDGETS_PER_PAGE = 10
MAX_GOALS_PER_PAGE = 10
BUDGET_WARNING_THRESHOLD = 80  # Bütçe kullanımı %80 üzerinde ise uyarı
BUDGET_DANGER_THRESHOLD = 95   # Bütçe kullanımı %95 üzerinde ise tehlike
GOAL_PROGRESS_MILESTONES = [25, 50, 75, 100]  # Hedef ilerlemesi için dönüm noktaları (yüzde)

# Rapor türleri
REPORT_TYPES = [
    {"id": "expense_by_category", "name": "Kategoriye Göre Harcama", "description": "Kategorilere göre harcama dağılımını gösterir."},
    {"id": "income_expense", "name": "Gelir-Gider Dengesi", "description": "Gelir ve gider dengesini gösterir."},
    {"id": "monthly_trend", "name": "Aylık Trend", "description": "Aylara göre gelir-gider trendini gösterir."},
    {"id": "savings_rate", "name": "Tasarruf Oranı", "description": "Gelire göre tasarruf oranını gösterir."},
    {"id": "budget_performance", "name": "Bütçe Performansı", "description": "Bütçe hedeflerine göre performansı gösterir."}
]

# API entegrasyonları
API_SETTINGS = {
    "exchange_rates_api": "https://api.exchangerate-api.com/v4/latest/TRY",
    "news_api": "https://newsapi.org/v2/top-headlines?country=tr&category=business"
}

# Tema ayarları
def set_page_theme():
    """Streamlit tema ayarlarını yapılandırır."""
    st.set_page_config(
        page_title="Kişisel Finans",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )

def load_css():
    """CSS dosyasını yükler ve uygular."""
    css_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "styles.css")
    
    if os.path.exists(css_file_path):
        with open(css_file_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        print(f"CSS dosyası bulunamadı: {css_file_path}")

def add_logo():
    """Sidebar'a logo ekler."""
    st.sidebar.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #3498db; font-size: 1.8rem;">💰 FinansApp</h1>
            <p style="font-size: 0.9rem; opacity: 0.8;">Kişisel finansınızı kontrol edin</p>
        </div>
    """, unsafe_allow_html=True)

def add_card(title, content, icon="📝", bg_color=None):
    """Özel kart bileşeni oluşturur."""
    bg_style = f"background-color: {bg_color};" if bg_color else ""
    st.markdown(f"""
        <div class="card-container" style="{bg_style}">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div style="font-size: 1.5rem; margin-right: 10px;">{icon}</div>
                <h3 style="margin: 0;">{title}</h3>
            </div>
            <div>{content}</div>
        </div>
    """, unsafe_allow_html=True)

def local_css():
    """Uygulama içi özel CSS tanımlamaları."""
    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background-color: #f8f9fa;
            }
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            .stApp {
                background-color: #f5f7fa;
            }
        </style>
    """, unsafe_allow_html=True)

def setup_page_config():
    """Sayfa konfigürasyonunu ayarlar ve CSS uygular."""
    set_page_theme()
    load_css()
    
    # Ekstra stiller
    st.markdown("""
        <style>
            .stApp {
                background-color: #f9f9f9;
            }
            
            .css-1d391kg, .css-1wrcr25 {
                background-color: #fff;
                border-radius: 10px;
                padding: 2rem 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            h1, h2, h3 {
                color: #2c3e50;
            }
            
            .stButton>button {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0.5rem 1rem;
                font-weight: 500;
            }
            
            .stButton>button:hover {
                background-color: #2980b9;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Logo ekle (önceden tanımlıysa)
    try:
        add_logo()
    except:
        pass 