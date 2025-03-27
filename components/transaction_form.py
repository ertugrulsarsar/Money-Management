import streamlit as st
from datetime import datetime

from models.transaction import TransactionType
from models.finance_manager import FinanceManager
from models.category_manager import CategoryManager


def render_transaction_form(finance_manager: FinanceManager, category_manager: CategoryManager):
    """İşlem ekleme formu bileşeni."""
    # Form dışına taşıyalım, böylece form yeniden oluşturulmadan önce seçim yapılabilir
    transaction_type = st.radio(
        "İşlem Türü",
        options=[TransactionType.INCOME, TransactionType.EXPENSE],
        format_func=lambda x: x.value,
        horizontal=True,
        key="transaction_type_radio"
    )
    
    # İşlem türüne göre kategori listesini hazırla
    if transaction_type == TransactionType.INCOME:
        categories = category_manager.get_income_categories()
    else:
        categories = category_manager.get_expense_categories()
    
    # Kategori yoksa bilgi ver
    if not categories:
        st.warning(f"Henüz {transaction_type.value.lower()} kategorisi tanımlanmamış. Lütfen önce bir kategori ekleyin.")
        return False
        
    with st.form(key=f"transaction_form_{transaction_type.name}", clear_on_submit=True):
        st.subheader("Yeni İşlem Ekle")
        
        # Seçili işlem türünü gizli bir şekilde saklayalım
        st.text(f"İşlem Türü: {transaction_type.value}")
        
        # Kategori seçimi
        category = st.selectbox(
            "Kategori",
            options=categories,
            format_func=lambda x: x.name,
            key=f"category_select_{transaction_type.name}"
        )
        
        # Diğer form alanları
        description = st.text_input("Açıklama", placeholder="İşlem açıklaması")
        amount = st.number_input("Miktar (TL)", min_value=0.01, step=10.0, format="%.2f")
        date_value = st.date_input("Tarih", value=datetime.today())
        
        submit_button = st.form_submit_button(label="Kaydet")
        
        if submit_button:
            if not description:
                st.error("Lütfen bir açıklama girin.")
            elif amount <= 0:
                st.error("Miktar sıfırdan büyük olmalıdır.")
            else:
                # İşlemi ekle
                finance_manager.add_transaction(
                    amount=amount,
                    category=category,
                    description=description,
                    date=datetime.combine(date_value, datetime.min.time()),
                    transaction_type=transaction_type
                )
                
                st.success(f"{transaction_type.value} başarıyla eklendi!")
                return True
    
    return False 