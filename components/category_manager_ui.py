import streamlit as st
from typing import List

from models.category_manager import CategoryManager, CustomCategory
from models.transaction import TransactionType


def render_category_manager(category_manager: CategoryManager):
    """Kategori yönetim arayüzü."""
    st.subheader("Kategori Yönetimi")
    
    # Ana sekmeleri oluştur
    cat_tab1, cat_tab2 = st.tabs(["Kategori Ekle", "Kategorileri Yönet"])
    
    with cat_tab1:
        render_add_category(category_manager)
    
    with cat_tab2:
        render_manage_categories(category_manager)


def render_add_category(category_manager: CategoryManager):
    """Yeni kategori ekleme formu."""
    with st.form(key="add_category_form", clear_on_submit=True):
        st.subheader("Yeni Kategori Ekle")
        
        # Kategori türü seçimi
        transaction_type = st.radio(
            "Kategori Türü",
            options=[TransactionType.INCOME, TransactionType.EXPENSE],
            format_func=lambda x: x.value,
            horizontal=True,
            key="category_type_radio"
        )
        
        # Kategori adı
        category_name = st.text_input("Kategori Adı", placeholder="Örn: Kira, Market, Yatırım...")
        
        submit_button = st.form_submit_button(label="Kategori Ekle")
        
        if submit_button:
            if not category_name:
                st.error("Lütfen bir kategori adı girin.")
            else:
                # Kategoriyi ekle
                new_category = category_manager.add_category(
                    name=category_name,
                    transaction_type=transaction_type
                )
                
                if new_category:
                    st.success(f"'{new_category.name}' kategorisi başarıyla eklendi!")
                    return True
    
    return False


def render_manage_categories(category_manager: CategoryManager):
    """Kategori yönetim arayüzü."""
    # Filtreleme seçenekleri
    filter_type = st.radio(
        "Kategori Türü",
        options=["Tümü", "Gelir", "Gider"],
        horizontal=True,
        key="manage_category_filter"
    )
    
    # Filtreye göre kategorileri getir
    if filter_type == "Gelir":
        categories = category_manager.get_income_categories()
        transaction_type = TransactionType.INCOME
    elif filter_type == "Gider":
        categories = category_manager.get_expense_categories()
        transaction_type = TransactionType.EXPENSE
    else:
        categories = category_manager.get_categories()
        transaction_type = None
    
    if not categories:
        st.info(f"Bu tipte kategori bulunamadı.")
        return
    
    # Kategorileri listele
    st.subheader("Mevcut Kategoriler")
    
    for i, category in enumerate(categories):
        col1, col2, col3 = st.columns([4, 2, 1])
        
        with col1:
            # Form içerisinde benzersiz key değeri kullan
            new_name = st.text_input(
                f"Kategori Adı", 
                value=category.name,
                key=f"category_name_{category.id}"
            )
        
        with col2:
            st.text(category.transaction_type.value)
        
        with col3:
            update_col, delete_col = st.columns(2)
            
            with update_col:
                # Güncelleme butonu
                if st.button("✓", key=f"update_btn_{category.id}"):
                    if new_name and new_name != category.name:
                        updated = category_manager.update_category(category.id, new_name)
                        if updated:
                            st.success(f"Kategori '{updated.name}' olarak güncellendi!")
                            st.rerun()
            
            with delete_col:
                # Silme butonu
                if st.button("🗑️", key=f"delete_btn_{category.id}"):
                    if category_manager.delete_category(category.id):
                        st.success(f"'{category.name}' kategorisi silindi!")
                        st.rerun()
        
        st.divider() 