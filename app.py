import streamlit as st
import os
import pandas as pd
from models.database import init_db, get_db, Transaction, Budget, FinancialGoal
from services.database_service import DatabaseService
from services.auth_service import AuthService
from datetime import datetime, timedelta
from datetime import date as dt_date
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List

from models.finance_manager import FinanceManager
from models.transaction import TransactionType
from models.category_manager import CategoryManager
from components.transaction_form import render_transaction_form
from components.transaction_list import render_transaction_list
from components.analysis import render_analysis
from components.category_manager_ui import render_category_manager
from config.settings import APP_TITLE, APP_ICON, APP_DESCRIPTION, DATA_FILE
from config.settings import PRIMARY_COLOR, BACKGROUND_COLOR, SECONDARY_BACKGROUND_COLOR, TEXT_COLOR
from services.report_service import ReportService
from services.notification_service import NotificationService
from services.budget_service import BudgetService
from utils.data_generator import DataGenerator
from utils.logger import FinanceLogger

# Tema renkleri
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#ff7f0e"
BACKGROUND_COLOR = "#f8f9fa"
CARD_BACKGROUND = "#ffffff"
TEXT_COLOR = "#2c3e50"

def setup_page():
    """Sayfa yapılandırmasını ayarlar."""
    st.set_page_config(
        page_title="Kişisel Finans Yönetimi",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS ile tema özelleştirmesi
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: #f8f9fa;
            color: #2c3e50;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .stButton button {{
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            border: none;
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        .stButton button:hover {{
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stSidebar .sidebar-content {{
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }}
        .stMetric {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 10px 0;
        }}
        .metric-label {{
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: 700;
            color: #3498db;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            white-space: pre-wrap;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 16px;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            font-weight: 500;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #3498db;
            color: white;
            border: none;
        }}
        .stForm {{
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stDataFrame {{
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stSelectbox, .stTextInput, .stNumberInput {{
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }}
        .stSelectbox:focus, .stTextInput:focus, .stNumberInput:focus {{
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }}
        .notification-container {{
            max-height: 300px;
            overflow-y: auto;
            padding: 10px;
            background-color: #ffffff;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        .notification-item {{
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .notification-item.error {{
            border-left-color: #e74c3c;
            background-color: #fde8e8;
        }}
        .notification-item.warning {{
            border-left-color: #f1c40f;
            background-color: #fff8e8;
        }}
        .notification-item.info {{
            border-left-color: #3498db;
            background-color: #e8f4f8;
        }}
        .menu-item {{
            padding: 12px;
            margin: 5px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }}
        .menu-item:hover {{
            background-color: #3498db;
            color: white;
            transform: translateX(5px);
        }}
        .menu-item.active {{
            background-color: #3498db;
            color: white;
        }}
        h1 {{
            color: #2c3e50;
            font-weight: 700;
            font-size: 2.5em;
            margin-bottom: 1em;
        }}
        h2 {{
            color: #2c3e50;
            font-weight: 600;
            font-size: 2em;
            margin-bottom: 0.8em;
        }}
        h3 {{
            color: #2c3e50;
            font-weight: 600;
            font-size: 1.5em;
            margin-bottom: 0.6em;
        }}
        p {{
            color: #34495e;
            line-height: 1.6;
        }}
        .stMarkdown {{
            color: #34495e;
        }}
    </style>
    """, unsafe_allow_html=True)


def check_auth():
    """Oturum kontrolü yapar."""
    if 'user_id' not in st.session_state or not st.session_state.user_id:
        st.warning("Lütfen giriş yapın!")
        st.switch_page("pages/login.py")


def create_dashboard_metrics(summary):
    """Dashboard metriklerini oluşturur."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Toplam Gelir",
            value=f"₺{summary['total_income']:,.2f}",
            delta=f"₺{summary['total_income'] - summary['total_expense']:,.2f}"
        )
    
    with col2:
        st.metric(
            label="Toplam Gider",
            value=f"₺{summary['total_expense']:,.2f}",
            delta=f"-₺{summary['total_expense']:,.2f}"
        )
    
    with col3:
        st.metric(
            label="Net Durum",
            value=f"₺{summary['net_amount']:,.2f}",
            delta=f"₺{summary['net_amount']:,.2f}"
        )


def create_transaction_chart(transactions):
    """İşlem grafiği oluşturur."""
    if not transactions or not transactions.get("transactions"):
        return None
        
    # İşlemleri tarihe göre grupla
    daily_transactions = {}
    for t in transactions["transactions"]:
        try:
            date_key = t.date.strftime("%Y-%m-%d")
            if date_key not in daily_transactions:
                daily_transactions[date_key] = {"income": 0, "expense": 0}
            daily_transactions[date_key][t.type] += t.amount
        except Exception as e:
            print(f"Hata: {str(e)}")
            continue
    
    # Tarihleri sırala
    dates = sorted(daily_transactions.keys())
    
    # Gelir ve giderleri ayır
    incomes = [daily_transactions[d]["income"] for d in dates]
    expenses = [daily_transactions[d]["expense"] for d in dates]
    
    # Grafik oluştur
    fig = go.Figure()
    
    # Gelir çizgisi
    fig.add_trace(go.Scatter(
        x=dates,
        y=incomes,
        name="Gelir",
        line=dict(color="#27ae60", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Gelir: ₺%{y:,.2f}<br>" +
            "<extra></extra>"
        )
    ))
    
    # Gider çizgisi
    fig.add_trace(go.Scatter(
        x=dates,
        y=expenses,
        name="Gider",
        line=dict(color="#e74c3c", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        hovertemplate=(
            "<b>%{x}</b><br>" +
            "Gider: ₺%{y:,.2f}<br>" +
            "<extra></extra>"
        )
    ))
    
    # Grafik ayarları
    fig.update_layout(
        title={
            'text': "Gelir ve Gider Trendi",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Tarih",
        yaxis_title="Miktar (₺)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=14)
        ),
        hovermode="x unified",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=50, l=50, r=50),
        height=400
    )
    
    # X ekseni ayarları
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        tickfont=dict(size=12)
    )
    
    # Y ekseni ayarları
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(0,0,0,0.1)',
        tickfont=dict(size=12),
        tickformat="₺,"
    )
    
    return fig


def main():
    """Ana uygulama fonksiyonu."""
    setup_page()
    
    # Veritabanını başlat
    init_db()
    
    # Oturum kontrolü
    check_auth()
    
    # Servisleri başlat
    db = next(get_db())
    db_service = DatabaseService(db)
    report_service = ReportService(db)
    notification_service = NotificationService(db)
    budget_service = BudgetService(db)
    data_generator = DataGenerator(db)
    
    # Son 30 günlük özet için tarihleri ayarla
    end_date = dt_date.today()
    start_date = end_date - timedelta(days=30)
    
    # Bildirimleri kontrol et
    notifications = notification_service.get_all_notifications(st.session_state.user_id)
    
    # Sidebar
    with st.sidebar:
        st.title("💰 Finans Yönetimi")
        st.markdown("---")
        
        # Kullanıcı bilgileri
        st.markdown(f"👤 **{st.session_state.username}**")
        
        # Veri üretme butonu
        if st.button("🎲 Rastgele Veri Üret"):
            try:
                result = data_generator.populate_user_data(st.session_state.user_id)
                st.success(f"""
                Veriler başarıyla üretildi:
                - {result['transactions']} işlem
                - {result['budgets']} bütçe
                - {result['goals']} hedef
                """)
            except Exception as e:
                st.error(f"Veri üretilirken hata oluştu: {str(e)}")
        
        # Menü
        st.markdown("### 📋 Menü")
        menu_items = [
            {"icon": "🏠", "label": "Ana Sayfa"},
            {"icon": "💰", "label": "Gelir/Gider"},
            {"icon": "📊", "label": "Bütçe"},
            {"icon": "🎯", "label": "Hedefler"},
            {"icon": "📈", "label": "Raporlar"},
            {"icon": "🔔", "label": "Bildirimler"},
            {"icon": "💾", "label": "Yedekleme"}
        ]
        
        page = st.radio(
            "Sayfa Seçimi",
            [item["label"] for item in menu_items],
            label_visibility="collapsed"
        )
        
        # Çıkış butonu
        st.markdown("---")
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            for key in ['user_id', 'username', 'token']:
                st.session_state.pop(key, None)
            st.switch_page("pages/login.py")

    # Ana sayfa
    if page == "Ana Sayfa":
        st.title("💰 Finansal Durumunuz")
        
        # Son 30 günlük özet
        summary = db_service.get_transaction_summary(
            st.session_state.user_id, 
            start_date, 
            end_date
        )
        
        # Metrikler
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <h3 style='color: #2c3e50; margin-bottom: 10px;'>Bu Ay Toplam Gelir</h3>
                    <h2 style='color: #27ae60; margin: 0;'>₺{:.2f}</h2>
                    <p style='color: #7f8c8d; margin: 5px 0 0 0;'>Geçen aya göre: ₺{:.2f}</p>
                </div>
            """.format(summary['total_income'], summary['total_income'] - summary['total_expense']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <h3 style='color: #2c3e50; margin-bottom: 10px;'>Bu Ay Toplam Gider</h3>
                    <h2 style='color: #e74c3c; margin: 0;'>₺{:.2f}</h2>
                    <p style='color: #7f8c8d; margin: 5px 0 0 0;'>Geçen aya göre: ₺{:.2f}</p>
                </div>
            """.format(summary['total_expense'], summary['total_expense']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>
                    <h3 style='color: #2c3e50; margin-bottom: 10px;'>Bu Ay Net Durum</h3>
                    <h2 style='color: #3498db; margin: 0;'>₺{:.2f}</h2>
                    <p style='color: #7f8c8d; margin: 5px 0 0 0;'>Geçen aya göre: ₺{:.2f}</p>
                </div>
            """.format(summary['net_amount'], summary['net_amount']), unsafe_allow_html=True)
        
        # Grafikler
        st.markdown("""
            <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-top: 20px;'>
                <h3 style='color: #2c3e50; margin-bottom: 20px;'>📈 Gelir/Gider Trendi</h3>
            </div>
        """, unsafe_allow_html=True)
        
        transactions = db_service.get_user_transactions(st.session_state.user_id)
        fig = create_transaction_chart(transactions)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Son işlemler
            st.markdown("""
                <div style='background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-top: 20px;'>
                    <h3 style='color: #2c3e50; margin-bottom: 20px;'>📋 Son İşlemleriniz</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if transactions and transactions.get("transactions"):
                df = pd.DataFrame([{
                    'Tarih': t.date,
                    'Tip': t.type,
                    'Kategori': t.category,
                    'Miktar': t.amount,
                    'Açıklama': t.description
                } for t in transactions["transactions"][:5]])  # Son 5 işlem
                
                # DataFrame'i özelleştir
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Tarih': st.column_config.DateColumn(
                            'Tarih',
                            format='DD.MM.YYYY'
                        ),
                        'Tip': st.column_config.SelectboxColumn(
                            'Tip',
                            options=['Gelir', 'Gider'],
                            default='Gelir'
                        ),
                        'Kategori': st.column_config.TextColumn('Kategori'),
                        'Miktar': st.column_config.NumberColumn(
                            'Miktar',
                            format='₺%.2f'
                        ),
                        'Açıklama': st.column_config.TextColumn('Açıklama')
                    }
                )
            else:
                st.info("Henüz işlem bulunmuyor.")
        else:
            st.info("Henüz işlem bulunmuyor.")

    # Gelir/Gider sayfası
    elif page == "Gelir/Gider":
        st.title("💰 Gelir/Gider Yönetimi")
        
        # İşlem ekleme formu
        with st.form("transaction_form"):
            st.subheader("➕ Yeni İşlem Ekle")
            col1, col2 = st.columns(2)
            
            with col1:
                transaction_type = st.selectbox("İşlem Tipi", ["Gelir", "Gider"])
                amount = st.number_input("Miktar", min_value=0.0)
                category = st.text_input("Kategori")
            
            with col2:
                date = st.date_input("Tarih")
                description = st.text_area("Açıklama")
                is_recurring = st.checkbox("Tekrarlayan İşlem")
            
            if is_recurring:
                recurring_type = st.selectbox(
                    "Tekrar Sıklığı",
                    ["Günlük", "Haftalık", "Aylık", "Yıllık"]
                )
            else:
                recurring_type = None
            
            submitted = st.form_submit_button("İşlem Ekle")
            
            if submitted:
                try:
                    db_service.create_transaction(
                        user_id=st.session_state.user_id,
                        amount=amount,
                        type=transaction_type.lower(),
                        category=category,
                        description=description,
                        date=date,
                        is_recurring=is_recurring,
                        recurring_type=recurring_type.lower() if recurring_type else None
                    )
                    st.success("İşlem başarıyla eklendi!")
                    # Önbelleği temizle
                    db_service.clear_cache()
                except Exception as e:
                    st.error(f"İşlem eklenirken hata oluştu: {str(e)}")
        
        # İşlem listesi
        st.subheader("📋 Son İşlemler")
        
        # Filtreler
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            transaction_type_filter = st.selectbox(
                "İşlem Tipi",
                ["Tümü", "Gelir", "Gider"],
                key="transaction_type_filter"
            )
        
        with col2:
            # Kategori filtresi
            categories = ["Tümü"]
            transactions_data = db_service.get_user_transactions(st.session_state.user_id)
            if transactions_data and transactions_data.get("transactions"):
                categories.extend(list(set(t.category for t in transactions_data["transactions"])))
            category_filter = st.selectbox("Kategori", categories)
        
        with col3:
            min_amount = st.number_input(
                "Min. Miktar",
                min_value=0.0,
                value=0.0,
                step=100.0
            )
        
        with col4:
            max_amount = st.number_input(
                "Max. Miktar",
                min_value=0.0,
                value=1000000000.0,  # 1 milyar TL
                step=100.0
            )
        
        # Sayfalama
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
        
        # İşlemleri getir
        transactions_data = db_service.get_user_transactions(
            user_id=st.session_state.user_id,
            page=st.session_state.current_page,
            per_page=50,
            transaction_type=transaction_type_filter.lower() if transaction_type_filter != "Tümü" else None,
            category=category_filter if category_filter != "Tümü" else None
        )
        
        if transactions_data and transactions_data.get("transactions"):
            df = pd.DataFrame([{
                'Tarih': t.date,
                'Tip': t.type,
                'Kategori': t.category,
                'Miktar': t.amount,
                'Açıklama': t.description
            } for t in transactions_data["transactions"]])
            
            # DataFrame'i özelleştir
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Tarih': st.column_config.DateColumn(
                        'Tarih',
                        format='DD.MM.YYYY'
                    ),
                    'Tip': st.column_config.SelectboxColumn(
                        'Tip',
                        options=['Gelir', 'Gider'],
                        default='Gelir'
                    ),
                    'Kategori': st.column_config.TextColumn('Kategori'),
                    'Miktar': st.column_config.NumberColumn(
                        'Miktar',
                        format='₺%.2f'
                    ),
                    'Açıklama': st.column_config.TextColumn('Açıklama')
                }
            )
            
            # Sayfalama kontrolleri
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("◀️ Önceki Sayfa") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col2:
                st.write(f"Sayfa {st.session_state.current_page}/{transactions_data['total_pages']}")
            
            with col3:
                if st.button("Sonraki Sayfa ▶️") and st.session_state.current_page < transactions_data["total_pages"]:
                    st.session_state.current_page += 1
                    st.rerun()
        else:
            st.info("Henüz işlem bulunmuyor.")

    # Bütçe sayfası
    elif page == "Bütçe":
        st.title("💰 Bütçe Planlama")
        
        # Bütçe önerileri
        st.subheader("📊 Bütçe Önerileri")
        recommendations = budget_service.get_category_recommendations(st.session_state.user_id)
        
        if recommendations:
            st.markdown("### Kategori Bazlı Öneriler")
            for rec in recommendations:
                with st.expander(f"{rec['category']} - Güven Skoru: %{rec['confidence']*100:.1f}"):
                    st.write(f"Önerilen Bütçe: ₺{rec['suggested_budget']:,.2f}")
                    st.write(f"Ortalama Harcama: ₺{rec['average_spending']:,.2f}")
                    st.write(f"Trend: {'📈 Artıyor' if rec['trend'] > 0 else '📉 Azalıyor' if rec['trend'] < 0 else '➡️ Sabit'}")
        
        # Bütçe optimizasyonu
        st.markdown("### 🎯 Bütçe Optimizasyonu")
        with st.form("budget_optimization"):
            total_budget = st.number_input("Toplam Bütçe", min_value=0.0)
            
            if st.form_submit_button("Optimize Et"):
                optimized_budgets = budget_service.optimize_budget(st.session_state.user_id, total_budget)
                
                if optimized_budgets:
                    st.markdown("#### Optimize Edilmiş Bütçe Dağılımı")
                    for budget in optimized_budgets:
                        st.write(f"**{budget['category']}**")
                        st.write(f"Önerilen: ₺{budget['suggested_budget']:,.2f}")
                        st.write(f"Optimize: ₺{budget['optimized_budget']:,.2f}")
                        st.write(f"Güven Skoru: %{budget['confidence']*100:.1f}")
                        st.markdown("---")
        
        # Bütçe ekleme formu
        st.subheader("➕ Yeni Bütçe Ekle")
        with st.form("budget_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.text_input("Kategori")
                amount = st.number_input("Bütçe Limiti", min_value=0.0)
                period = st.selectbox("Dönem", ["Aylık", "Yıllık"])
            
            with col2:
                start_date = st.date_input("Başlangıç Tarihi")
                end_date = st.date_input("Bitiş Tarihi")
            
            submitted = st.form_submit_button("Bütçe Ekle")
            
            if submitted:
                try:
                    db_service.create_budget(
                        user_id=st.session_state.user_id,
                        category=category,
                        amount=amount,
                        period=period.lower(),
                        start_date=start_date,
                        end_date=end_date
                    )
                    st.success("Bütçe başarıyla eklendi!")
                    # Önbelleği temizle
                    db_service.clear_cache()
                except Exception as e:
                    st.error(f"Bütçe eklenirken hata oluştu: {str(e)}")
        
        # Bütçe listesi
        st.subheader("📋 Bütçeler")
        
        # Sayfalama
        if "budget_page" not in st.session_state:
            st.session_state.budget_page = 1
        
        # Bütçeleri getir
        budgets_data = db_service.get_user_budgets(
            user_id=st.session_state.user_id,
            page=st.session_state.budget_page,
            per_page=50,
            active_only=True
        )
        
        if budgets_data and budgets_data.get("budgets"):
            df = pd.DataFrame([{
                'Kategori': b.category,
                'Miktar': b.amount,
                'Dönem': b.period,
                'Başlangıç': b.start_date,
                'Bitiş': b.end_date
            } for b in budgets_data["budgets"]])
            
            # DataFrame'i özelleştir
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Kategori': st.column_config.TextColumn('Kategori'),
                    'Miktar': st.column_config.NumberColumn(
                        'Miktar',
                        format='₺%.2f'
                    ),
                    'Dönem': st.column_config.SelectboxColumn(
                        'Dönem',
                        options=['Aylık', 'Yıllık'],
                        default='Aylık'
                    ),
                    'Başlangıç': st.column_config.DateColumn(
                        'Başlangıç',
                        format='DD.MM.YYYY'
                    ),
                    'Bitiş': st.column_config.DateColumn(
                        'Bitiş',
                        format='DD.MM.YYYY'
                    )
                }
            )
            
            # Sayfalama kontrolleri
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("◀️ Önceki Sayfa", key="budget_prev") and st.session_state.budget_page > 1:
                    st.session_state.budget_page -= 1
                    st.rerun()
            
            with col2:
                st.write(f"Sayfa {st.session_state.budget_page}/{budgets_data['total_pages']}")
            
            with col3:
                if st.button("Sonraki Sayfa ▶️", key="budget_next") and st.session_state.budget_page < budgets_data["total_pages"]:
                    st.session_state.budget_page += 1
                    st.rerun()
        else:
            st.info("Henüz bütçe bulunmuyor.")

    # Hedefler sayfası
    elif page == "Hedefler":
        st.title("🎯 Finansal Hedefler")
        
        # Hedef ekleme formu
        st.subheader("➕ Yeni Hedef Ekle")
        with st.form("goal_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Hedef Adı")
                target_amount = st.number_input("Hedef Miktar", min_value=0.0)
                current_amount = st.number_input("Mevcut Miktar", min_value=0.0)
            
            with col2:
                deadline = st.date_input("Son Tarih")
                priority = st.selectbox("Öncelik", ["Düşük", "Orta", "Yüksek"])
            
            submitted = st.form_submit_button("Hedef Ekle")
            
            if submitted:
                try:
                    db_service.create_goal(
                        user_id=st.session_state.user_id,
                        name=name,
                        target_amount=target_amount,
                        current_amount=current_amount,
                        deadline=deadline,
                        priority=priority.lower()
                    )
                    st.success("Hedef başarıyla eklendi!")
                    # Önbelleği temizle
                    db_service.clear_cache()
                except Exception as e:
                    st.error(f"Hedef eklenirken hata oluştu: {str(e)}")
        
        # Hedef listesi
        st.subheader("📋 Hedefler")
        
        # Sayfalama
        if "goal_page" not in st.session_state:
            st.session_state.goal_page = 1
        
        # Hedefleri getir
        goals_data = db_service.get_user_goals(
            user_id=st.session_state.user_id,
            page=st.session_state.goal_page,
            per_page=50,
            active_only=True
        )
        
        if goals_data and goals_data.get("goals"):
            df = pd.DataFrame([{
                'Hedef': g.name,
                'Hedef Miktar': g.target_amount,
                'Mevcut Miktar': g.current_amount,
                'İlerleme': f"%{(g.current_amount / g.target_amount * 100):.1f}",
                'Son Tarih': g.deadline,
                'Öncelik': g.priority
            } for g in goals_data["goals"]])
            
            # DataFrame'i özelleştir
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'Hedef': st.column_config.TextColumn('Hedef'),
                    'Hedef Miktar': st.column_config.NumberColumn(
                        'Hedef Miktar',
                        format='₺%.2f'
                    ),
                    'Mevcut Miktar': st.column_config.NumberColumn(
                        'Mevcut Miktar',
                        format='₺%.2f'
                    ),
                    'İlerleme': st.column_config.TextColumn('İlerleme'),
                    'Son Tarih': st.column_config.DateColumn(
                        'Son Tarih',
                        format='DD.MM.YYYY'
                    ),
                    'Öncelik': st.column_config.SelectboxColumn(
                        'Öncelik',
                        options=['Düşük', 'Orta', 'Yüksek'],
                        default='Orta'
                    )
                }
            )
            
            # Sayfalama kontrolleri
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("◀️ Önceki Sayfa", key="goal_prev") and st.session_state.goal_page > 1:
                    st.session_state.goal_page -= 1
                    st.rerun()
            
            with col2:
                st.write(f"Sayfa {st.session_state.goal_page}/{goals_data['total_pages']}")
            
            with col3:
                if st.button("Sonraki Sayfa ▶️", key="goal_next") and st.session_state.goal_page < goals_data["total_pages"]:
                    st.session_state.goal_page += 1
                    st.rerun()
        else:
            st.info("Henüz hedef bulunmuyor.")

    # Raporlar sayfası
    elif page == "Raporlar":
        st.title("📊 Finansal Raporlar")
        
        # Rapor dönemi seçimi
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Yıl", range(2020, datetime.now().year + 1), 
                              index=datetime.now().year - 2020)
        with col2:
            month = st.selectbox("Ay", range(1, 13), index=datetime.now().month - 1)
        
        # Rapor oluştur
        report_data = report_service.generate_monthly_report(
            st.session_state.user_id, 
            year, 
            month
        )
        
        # Özet metrikler
        st.markdown("### 📈 Aylık Özet")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Toplam Gelir",
                f"₺{report_data['summary']['total_income']:,.2f}"
            )
        
        with col2:
            st.metric(
                "Toplam Gider",
                f"₺{report_data['summary']['total_expense']:,.2f}"
            )
        
        with col3:
            st.metric(
                "Net Durum",
                f"₺{report_data['summary']['net_amount']:,.2f}"
            )
        
        # Grafikler
        st.markdown("### 📊 Görsel Analizler")
        
        # Harcama dağılımı
        if report_data['expense_by_category']:
            st.markdown("#### 💰 Harcamalarınızın Dağılımı")
            expense_chart = report_service.create_expense_chart(report_data['expense_by_category'])
            if expense_chart:
                st.plotly_chart(expense_chart, use_container_width=True)
        
        # Bütçe performansı
        if report_data['budget_performance']:
            st.markdown("#### 📈 Bütçe Durumunuz")
            budget_chart = report_service.create_budget_chart(report_data['budget_performance'])
            if budget_chart:
                st.plotly_chart(budget_chart, use_container_width=True)
        
        # Hedef ilerlemesi
        if report_data['goal_progress']:
            st.markdown("#### 🎯 Hedeflerinize Ulaşma Durumunuz")
            goal_chart = report_service.create_goal_chart(report_data['goal_progress'])
            if goal_chart:
                st.plotly_chart(goal_chart, use_container_width=True)
        
        # Excel'e aktar
        st.markdown("### 💾 Raporu Kaydet")
        if st.button("Excel'e Aktar"):
            filename = f"finansal_rapor_{year}_{month:02d}.xlsx"
            report_service.export_to_excel(
                report_data, 
                filename,
                include_transactions=True,
                include_budgets=True,
                include_goals=True
            )
            st.success(f"Rapor başarıyla {filename} dosyasına kaydedildi!")

    # Bildirimler sayfası
    elif page == "Bildirimler":
        st.title("🔔 Bildirimler")
        
        # Bildirimleri kategorilere ayır
        budget_alerts = [n for n in notifications if n["type"] in ["budget_alert", "budget_warning"]]
        goal_reminders = [n for n in notifications if n["type"] == "goal_reminder"]
        recurring_reminders = [n for n in notifications if n["type"] == "recurring_reminder"]
        
        # Bütçe uyarıları
        if budget_alerts:
            st.subheader("💰 Bütçe Uyarıları")
            for alert in budget_alerts:
                with st.expander(f"{'⚠️ AŞIM' if alert['type'] == 'budget_alert' else '⚠️ UYARI'} - {alert['category']}"):
                    st.write(f"Bütçe Limiti: ₺{alert['limit']:,.2f}")
                    st.write(f"Harcanan: ₺{alert['spent']:,.2f}")
                    st.write(f"Kalan: ₺{alert['remaining']:,.2f}")
        
        # Hedef hatırlatmaları
        if goal_reminders:
            st.subheader("🎯 Hedef Hatırlatmaları")
            for reminder in goal_reminders:
                with st.expander(f"{reminder['name']} - {reminder['days_left']} gün kaldı"):
                    st.write(f"Hedef: ₺{reminder['target']:,.2f}")
                    st.write(f"Mevcut: ₺{reminder['current']:,.2f}")
                    st.write(f"İlerleme: %{reminder['progress']:.1f}")
                    st.write(f"Son Tarih: {reminder['deadline'].strftime('%d.%m.%Y')}")
        
        # Tekrarlayan işlem hatırlatmaları
        if recurring_reminders:
            st.subheader("🔄 Tekrarlayan İşlemler")
            for reminder in recurring_reminders:
                with st.expander(f"{reminder['category']} - {reminder['frequency']}"):
                    st.write(f"Miktar: ₺{reminder['amount']:,.2f}")
                    st.write(f"Son İşlem: {reminder['last_date'].strftime('%d.%m.%Y')}")
        
        if not notifications:
            st.info("Henüz bildirim bulunmuyor.")

    # Yedekleme sayfası
    elif page == "Yedekleme":
        st.title("💾 Yedekleme ve Geri Yükleme")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Yedekleri Görüntüle")
            logger = FinanceLogger()
            
            # İşlem yedekleri
            st.markdown("### 📝 İşlem Yedekleri")
            transaction_backups = sorted(logger.backup_dir.glob("transactions_*.json"))
            if transaction_backups:
                for backup in transaction_backups:
                    st.text(f"📄 {backup.name}")
            else:
                st.info("Henüz işlem yedeği bulunmuyor.")
            
            # Bütçe yedekleri
            st.markdown("### 💰 Bütçe Yedekleri")
            budget_backups = sorted(logger.backup_dir.glob("budgets_*.json"))
            if budget_backups:
                for backup in budget_backups:
                    st.text(f"📄 {backup.name}")
            else:
                st.info("Henüz bütçe yedeği bulunmuyor.")
            
            # Hedef yedekleri
            st.markdown("### 🎯 Hedef Yedekleri")
            goal_backups = sorted(logger.backup_dir.glob("goals_*.json"))
            if goal_backups:
                for backup in goal_backups:
                    st.text(f"📄 {backup.name}")
            else:
                st.info("Henüz hedef yedeği bulunmuyor.")
        
        with col2:
            st.subheader("Geri Yükleme")
            
            # Geri yükleme formu
            with st.form("restore_form"):
                category = st.selectbox(
                    "Yedek Kategorisi",
                    ["transactions", "budgets", "goals"]
                )
                
                if st.form_submit_button("Geri Yükle"):
                    try:
                        if db_service.restore_from_backup(category):
                            st.success(f"{category.title()} başarıyla geri yüklendi!")
                        else:
                            st.warning(f"{category.title()} için yedek bulunamadı.")
                    except Exception as e:
                        st.error(f"Geri yükleme sırasında hata oluştu: {str(e)}")
            
            # Log dosyalarını görüntüle
            st.markdown("### 📋 Log Dosyaları")
            log_files = sorted(logger.log_dir.glob("finance_*.log"))
            if log_files:
                for log_file in log_files:
                    st.text(f"📄 {log_file.name}")
            else:
                st.info("Henüz log dosyası bulunmuyor.")


if __name__ == "__main__":
    main() 