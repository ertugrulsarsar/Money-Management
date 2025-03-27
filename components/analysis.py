import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from models.finance_manager import FinanceManager
from models.transaction import TransactionType
from utils.date_utils import get_month_range, get_date_filters, month_name


def render_analysis(finance_manager: FinanceManager):
    """Finans analizi bileşeni."""
    st.subheader("Finansal Analiz")
    
    # Filtre bölümü
    date_filters = get_date_filters()
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_year = st.selectbox(
            "Yıl",
            options=date_filters["years"],
            index=date_filters["years"].index(date_filters["current_year"]),
            key="analysis_year"
        )
    
    with col2:
        selected_month = st.selectbox(
            "Ay",
            options=date_filters["months"],
            format_func=month_name,
            index=date_filters["current_month"] - 1,
            key="analysis_month"
        )
    
    # Tarihe göre filtrele
    start_date, end_date = get_month_range(selected_year, selected_month)
    
    # Özet tablosu için işlemleri al
    df_income = finance_manager.get_transactions_as_dataframe(
        transaction_type=TransactionType.INCOME, 
        start_date=start_date,
        end_date=end_date
    )
    
    df_expense = finance_manager.get_transactions_as_dataframe(
        transaction_type=TransactionType.EXPENSE, 
        start_date=start_date,
        end_date=end_date
    )
    
    # Bakiyeyi hesapla
    balance = finance_manager.get_balance(start_date=start_date, end_date=end_date)
    total_income = df_income['amount'].sum() if not df_income.empty else 0
    total_expense = df_expense['amount'].sum() if not df_expense.empty else 0
    
    # Özet göstergeleri
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Toplam Gelir",
            value=f"{total_income:,.2f} TL",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Toplam Gider",
            value=f"{total_expense:,.2f} TL",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Bakiye",
            value=f"{balance:,.2f} TL",
            delta=f"{balance:+,.2f} TL",
            delta_color="normal"
        )
    
    # Kategori bazlı harcama grafiği
    st.subheader("Kategori Analizi")
    
    tab1, tab2 = st.tabs(["Giderler", "Gelirler"])
    
    with tab1:
        render_category_analysis(finance_manager, TransactionType.EXPENSE, start_date, end_date)
    
    with tab2:
        render_category_analysis(finance_manager, TransactionType.INCOME, start_date, end_date)


def render_category_analysis(finance_manager: FinanceManager, 
                           transaction_type: TransactionType,
                           start_date: datetime, 
                           end_date: datetime):
    """Kategori bazlı analiz grafiklerini oluşturur."""
    # Kategori toplamlarını al
    category_summary = finance_manager.get_category_summary(
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    
    if not category_summary:
        st.info(f"Bu dönemde {transaction_type.value.lower()} kaydı bulunamadı.")
        return
    
    # Veriyi grafikler için hazırla
    df = pd.DataFrame({
        'Kategori': list(category_summary.keys()),
        'Miktar': list(category_summary.values())
    })
    
    # Pasta grafiği
    fig_pie = px.pie(
        df, 
        values='Miktar', 
        names='Kategori',
        title=f"Kategori Bazlı {transaction_type.value} Dağılımı",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Miktar: %{value:.2f} TL<br>Oran: %{percent}"
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Çubuk grafiği
    df = df.sort_values(by='Miktar', ascending=False)
    
    fig_bar = px.bar(
        df,
        x='Kategori',
        y='Miktar',
        title=f"Kategori Bazlı {transaction_type.value} Miktarları",
        color='Miktar',
        color_continuous_scale='Viridis'
    )
    
    fig_bar.update_traces(
        texttemplate='%{y:.2f} TL', 
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Miktar: %{y:.2f} TL"
    )
    
    fig_bar.update_layout(
        xaxis_title='Kategori',
        yaxis_title='Miktar (TL)'
    )
    
    st.plotly_chart(fig_bar, use_container_width=True) 