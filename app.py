import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import json
import time
from utils.db import init_db
from services.transaction_service import TransactionService
from services.budget_service import BudgetService
from services.category_service import CategoryService
from services.goal_service import GoalService
from components.sidebar import create_sidebar
from components.notification_center import show_notification_center
from utils.format import format_currency
from utils.config import PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR

# Sayfa yapılandırması
st.set_page_config(
    page_title="Kişisel Finans",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'Kişisel Finans yönetim uygulaması'
    }
)

# JavaScript kodlarını enjekte et
st.markdown("""
<script>
// Sayfa navigasyonu için yardımcı fonksiyon
function navigateTo(path, pageName) {
    console.log('navigateTo called with', path, pageName);
    
    // Session state'i güncelle
    window.parent.postMessage(
        {
            type: 'streamlit:setSessionState',
            state: { page: pageName }
        },
        '*'
    );
    
    // URL'yi değiştir
    setTimeout(function() {
        console.log('Navigating to:', path);
        window.parent.location.href = path;
    }, 100);
    
    return false;
}

// Sayfa yüklendiğinde tüm bağlantıları bul ve onlara tıklama olay dinleyicileri ekle
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded');
    
    // Tüm sidebar bağlantılarını bul
    setTimeout(function() {
        const sidebarLinks = document.querySelectorAll('.sidebar-menu-item');
        console.log('Found sidebar links:', sidebarLinks.length);
        
        sidebarLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const path = this.getAttribute('data-path');
                const pageName = this.getAttribute('data-page');
                console.log('Link clicked:', path, pageName);
                navigateTo(path, pageName);
            });
        });
    }, 1000);
});
</script>
""", unsafe_allow_html=True)

def setup_page():
    """Sayfa yapılandırmasını yapar."""
    # Temel sayfa ayarları
    st.set_page_config(
        page_title="Kişisel Finans | Ana Sayfa",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS stilleri
    st.markdown("""
        <style>
            /* Genel sayfa stilleri */
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: #1E293B;
                background-color: #F8FAFC;
            }
            
            /* Başlık stilleri */
            h1, h2, h3, h4, h5, h6 {
                font-weight: 600;
                color: #0F172A;
            }
            
            /* Kart stilleri */
            .card {
                background-color: white;
                border-radius: 10px;
                padding: 1.5rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                margin-bottom: 1.5rem;
                border: 1px solid #E2E8F0;
            }
            
            .card-header {
                margin-bottom: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .card-title {
                font-weight: 600;
                font-size: 1.1rem;
                color: #1E293B;
                margin: 0;
            }
            
            /* İşlem satırı stilleri */
            .transaction-row {
                display: flex;
                align-items: center;
                padding: 0.75rem 0;
                border-bottom: 1px solid #E2E8F0;
            }
            
            .transaction-row:last-child {
                border-bottom: none;
            }
            
            .transaction-icon {
                width: 40px;
                height: 40px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 0.75rem;
                flex-shrink: 0;
            }
            
            .income {
                background-color: rgba(34, 197, 94, 0.1);
                color: #22C55E;
            }
            
            .expense {
                background-color: rgba(239, 68, 68, 0.1);
                color: #EF4444;
            }
            
            .transaction-details {
                flex: 1;
            }
            
            .transaction-title {
                font-weight: 500;
                color: #1E293B;
                margin: 0;
            }
            
            .transaction-meta {
                font-size: 0.8rem;
                color: #64748B;
                margin: 0;
            }
            
            .transaction-amount {
                font-weight: 600;
            }
            
            .positive {
                color: #22C55E;
            }
            
            .negative {
                color: #EF4444;
            }
            
            /* Metrik kartı */
            .metric-card {
                background-color: white;
                border-radius: 10px;
                padding: 1.2rem;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                height: 100%;
                transition: transform 0.2s;
                border: 1px solid #E2E8F0;
            }
            
            .metric-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .metric-title {
                font-size: 0.85rem;
                color: #64748B;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
            }
            
            .metric-icon {
                margin-right: 0.5rem;
                font-size: 1rem;
            }
            
            .metric-value {
                font-size: 1.5rem;
                font-weight: 700;
                color: #0F172A;
                margin: 0;
            }
            
            .metric-trend {
                font-size: 0.8rem;
                margin-top: 0.5rem;
            }
            
            .trend-up {
                color: #22C55E;
            }
            
            .trend-down {
                color: #EF4444;
            }
            
            /* Grafikler için stil düzenlemeleri */
            .stPlotlyChart {
                padding: 0 !important;
            }
            
            /* Sayfa arka plan rengi */
            .main .block-container {
                padding-top: 1rem;
                padding-left: 1.5rem; 
                padding-right: 1.5rem;
                padding-bottom: 1rem;
            }
            
            /* Tooltip */
            .tooltip {
                position: relative;
                display: inline-block;
                cursor: help;
                margin-left: 5px;
            }
            
            .tooltip .tooltip-text {
                visibility: hidden;
                width: 200px;
                background-color: #333;
                color: #fff;
                text-align: center;
                border-radius: 5px;
                padding: 5px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -100px;
                opacity: 0;
                transition: opacity 0.3s;
                font-size: 0.7rem;
            }
            
            .tooltip:hover .tooltip-text {
                visibility: visible;
                opacity: 1;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # JavaScript enjeksiyonu
    st.markdown("""
        <script>
            // Sayfa yüklendiğinde çalışacak fonksiyon
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Page fully loaded, setting up event listeners');
                
                // Session state kontrolü için yardımcı fonksiyonlar
                window.setSessionState = function(key, value) {
                    window.parent.postMessage({
                        type: 'streamlit:setSessionState',
                        state: { [key]: value }
                    }, '*');
                };
            });
            
            // URL'den sayfa parametresi alma
            function getPageFromUrl() {
                const params = new URLSearchParams(window.location.search);
                return params.get('page');
            }
        </script>
    """, unsafe_allow_html=True)

def check_auth():
    """Kullanıcı oturum durumunu kontrol eder."""
    if "user_id" not in st.session_state or "username" not in st.session_state:
        st.switch_page("pages/login.py")
    
    # Yeni sayfa seçimini izle
    if "page" not in st.session_state:
        st.session_state.page = "Genel Bakış"

def create_metrics(transaction_service):
    """Dashboard için metrikler oluşturur"""
    # Son 30 gün içindeki işlemleri al
    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=30)
    
    # Gelir, gider ve bakiye hesapla
    transactions = transaction_service.get_transactions_by_date_range(start_date, current_date)
    
    income = sum(t.amount for t in transactions if t.type == "income")
    expense = sum(t.amount for t in transactions if t.type == "expense")
    balance = income - expense
    
    # En son 5 işlemin toplam tutarı
    last_transactions = transaction_service.get_last_transactions(5)
    recent_total = sum(t.amount for t in last_transactions if t.type == "expense")
    
    # Metrikleri göster
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Toplam Gelir (30 gün)", 
                 value=format_currency(income), 
                 delta=format_currency(income*0.1))
    
    with col2:
        st.metric(label="Toplam Gider (30 gün)", 
                 value=format_currency(expense), 
                 delta=format_currency(-expense*0.05),
                 delta_color="inverse")
    
    with col3:
        st.metric(label="Net Bakiye (30 gün)", 
                 value=format_currency(balance), 
                 delta=format_currency(balance*0.15))
    
    with col4:
        st.metric(label="Son İşlemler (5)", 
                 value=format_currency(recent_total), 
                 delta=format_currency(-recent_total*0.02),
                 delta_color="inverse")
                 
def create_transaction_chart(transaction_service, chart_type="line"):
    """İşlem grafiği oluşturur"""
    # Son 30 günlük işlemleri al
    current_date = datetime.now().date()
    start_date = current_date - timedelta(days=30)
    
    transactions = transaction_service.get_transactions_by_date_range(start_date, current_date)
    
    # İşlemleri DataFrame'e dönüştür
    df_data = [
        {
            'date': t.date,
            'amount': t.amount if t.type == 'income' else -t.amount,
            'type': t.type,
            'category': t.category.name if t.category else 'Kategorisiz'
        }
        for t in transactions
    ]
    
    if not df_data:
        st.info("Grafik için yeterli işlem verisi bulunmuyor.")
        return
        
    df = pd.DataFrame(df_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Grafik tipine göre görselleştirme
    if chart_type == "line":
        # Günlük toplam işlemler
        daily_totals = df.groupby([df['date'].dt.date, 'type'])['amount'].sum().unstack().fillna(0)
        
        # Eksik günleri doldur
        date_range = pd.date_range(start=start_date, end=current_date)
        daily_totals = daily_totals.reindex(date_range.date, fill_value=0)
        
        # Çizgi grafiği
        st.line_chart(daily_totals, color=['#FF9800', '#4CAF50'] if 'expense' in daily_totals.columns and 'income' in daily_totals.columns else None)
        
    elif chart_type == "bar":
        # Kategori bazlı harcamalar
        category_expenses = df[df['type'] == 'expense'].groupby('category')['amount'].sum().abs().sort_values(ascending=False)
        
        # Bar chart
        st.bar_chart(category_expenses)
        
    elif chart_type == "area":
        # Kümülatif toplam
        df['cumulative'] = df.sort_values('date')['amount'].cumsum()
        cumulative_by_date = df.groupby(df['date'].dt.date)['cumulative'].last()
        
        # Alan grafiği
        st.area_chart(cumulative_by_date)

# Ana sayfa gösterimi
def show_dashboard():
    """Genel bakış sayfasını gösterir."""
    st.title("📊 Genel Bakış")
    
    # Servis örnekleri oluştur
    transaction_service = TransactionService()
    budget_service = BudgetService()
    category_service = CategoryService()
    goal_service = GoalService()
    
    # Kullanıcı bilgilerini göster
    st.markdown(f"""
    <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;
              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 4px solid {PRIMARY_COLOR};">
        <h3 style="margin-top: 0; color: {PRIMARY_COLOR};">Hoş Geldin, {st.session_state.get('username', 'Kullanıcı')}!</h3>
        <p style="margin-bottom: 0;">Finansal durumunuzun güncel özeti aşağıda görüntülenmektedir.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard metriklerini göster
    create_metrics(transaction_service)
    
    # Grafik seçenekleri
    chart_options = {
        "Çizgi Grafik": "line", 
        "Çubuk Grafik": "bar", 
        "Alan Grafik": "area"
    }
    
    selected_chart = st.selectbox("Grafik Tipi", list(chart_options.keys()))
    
    # Seçilen grafiği göster
    create_transaction_chart(transaction_service, chart_options[selected_chart])
    
    # Son işlemler ve bütçe ilerleme durumu
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Son İşlemler")
        transactions = transaction_service.get_last_transactions(5)
        
        if not transactions:
            st.info("Henüz işlem bulunmuyor.")
        else:
            for t in transactions:
                date_str = t.date.strftime("%d.%m.%Y")
                type_color = PRIMARY_COLOR if t.type == "income" else SECONDARY_COLOR
                type_icon = "↑" if t.type == "income" else "↓"
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px; background-color: white; padding: 12px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="background-color: {type_color}; color: white; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 50%; margin-right: 12px;">
                        {type_icon}
                    </div>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: 500;">{t.description}</div>
                        <div style="font-size: 0.8em; color: #6c757d;">{date_str} • {t.category.name if t.category else 'Kategorisiz'}</div>
                    </div>
                    <div style="font-weight: 500; color: {type_color};">
                        {format_currency(t.amount)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Bütçe Durumu")
        budgets = budget_service.get_active_budgets()
        
        if not budgets:
            st.info("Aktif bütçe bulunmuyor.")
        else:
            for b in budgets:
                category_name = b.category.name if b.category else "Genel"
                spent = budget_service.get_spent_amount(b.id)
                percentage = min(int((spent / b.amount) * 100), 100) if b.amount > 0 else 0
                
                status_color = ACCENT_COLOR
                if percentage >= 90:
                    status_color = "#e74c3c"
                elif percentage >= 70:
                    status_color = "#f39c12"
                
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <div style="font-weight: 500;">{category_name}</div>
                        <div>{format_currency(spent)} / {format_currency(b.amount)}</div>
                    </div>
                    <div style="background-color: #f1f1f1; border-radius: 5px; height: 10px; width: 100%;">
                        <div style="background-color: {status_color}; width: {percentage}%; height: 100%; border-radius: 5px;"></div>
                    </div>
                    <div style="font-size: 0.8em; color: #6c757d; margin-top: 5px;">
                        {b.description} • {percentage}% kullanıldı
                    </div>
                </div>
                """, unsafe_allow_html=True)

def main():
    """Ana uygulama fonksiyonu."""
    setup_page()
    
    # Veritabanını başlat
    init_db()
    
    # Veritabanı güncellemesi
    try:
        from utils.migrate_db import migrate_db
        migrate_db()
    except Exception as e:
        st.error(f"Veritabanı güncellenirken hata oluştu: {str(e)}")
    
    # Oturum kontrolü
    check_auth()
    
    # Debug özelliğini aktifleştirme (geliştirme için)
    if st.session_state.get("debug", False):
        if "page" in st.session_state:
            st.info(f"Mevcut sayfa: {st.session_state['page']}")
        st.write("Session state:", st.session_state)
    
    # Sidebar ve navigasyonu oluştur
    current_page = create_sidebar()
    
    # Bildirim merkezini göster
    notification_count = st.session_state.get("notification_count", 0)
    show_notification_center(notification_count)
    
    # Manuel sayfa geçişleri için
    if st.session_state.get("page", "Genel Bakış") == "Genel Bakış" and current_page == "Genel Bakış":
        show_dashboard()
    
if __name__ == "__main__":
    main() 