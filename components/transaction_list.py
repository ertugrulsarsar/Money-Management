import streamlit as st
import pandas as pd
from datetime import datetime

from models.finance_manager import FinanceManager
from models.transaction import TransactionType
from utils.date_utils import get_month_range, get_date_filters, month_name


def render_transaction_list(finance_manager: FinanceManager):
    """İşlem listesi bileşeni."""
    st.subheader("İşlem Listesi")
    
    # Filtre bölümü
    with st.expander("Filtreleme Seçenekleri", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        date_filters = get_date_filters()
        
        with col1:
            filter_type = st.radio(
                "İşlem Türü",
                options=["Tümü", "Gelir", "Gider"],
                horizontal=True
            )
            
            if filter_type == "Gelir":
                transaction_type = TransactionType.INCOME
            elif filter_type == "Gider":
                transaction_type = TransactionType.EXPENSE
            else:
                transaction_type = None
        
        with col2:
            selected_year = st.selectbox(
                "Yıl",
                options=date_filters["years"],
                index=date_filters["years"].index(date_filters["current_year"])
            )
        
        with col3:
            selected_month = st.selectbox(
                "Ay",
                options=date_filters["months"],
                format_func=month_name,
                index=date_filters["current_month"] - 1
            )
    
    # Tarihe göre filtrele
    start_date, end_date = get_month_range(selected_year, selected_month)
    
    # İşlemleri getir
    df = finance_manager.get_transactions_as_dataframe(
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    
    if df.empty:
        st.info("Bu kriterlere uygun işlem bulunamadı.")
        return
    
    # DataFrame'i görüntülemek için hazırla
    display_df = df.copy()
    
    # Verileri formatla
    if 'date' in display_df.columns:
        display_df['date'] = display_df['date'].dt.strftime('%d.%m.%Y')
    
    if 'amount' in display_df.columns:
        display_df['amount'] = display_df['amount'].apply(lambda x: f"{x:,.2f} TL")
    
    # Sütun adlarını düzenle
    column_names = {
        'date': 'Tarih',
        'description': 'Açıklama',
        'category': 'Kategori',
        'amount': 'Miktar',
        'transaction_type': 'İşlem Türü'
    }
    
    display_df = display_df.rename(columns=column_names)
    
    if 'id' in display_df.columns:
        display_df = display_df.drop(columns=['id'])
    
    # Tabloyu göster
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # İşlem silme
    if not df.empty and 'id' in df.columns:
        with st.expander("İşlem Sil", expanded=False):
            transaction_ids = df['id'].tolist()
            transaction_descriptions = df['description'].tolist()
            
            options = [f"{desc} ({df.loc[i, 'amount']:.2f} TL) - {df.loc[i, 'category']}" 
                      for i, desc in enumerate(transaction_descriptions)]
            
            selected_index = st.selectbox(
                "Silinecek İşlem",
                options=range(len(options)),
                format_func=lambda i: options[i]
            )
            
            if st.button("İşlemi Sil", type="primary"):
                selected_id = transaction_ids[selected_index]
                if finance_manager.delete_transaction(selected_id):
                    st.success("İşlem başarıyla silindi!")
                    st.rerun()
                else:
                    st.error("İşlem silinirken bir hata oluştu.") 