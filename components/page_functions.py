import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from components.responsive import responsive_columns, card, responsive_metrics

def show_transactions():
    """İşlemler (Gelir/Gider) sayfasını gösterir."""
    st.title("💸 İşlemler")
    
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
                from models.database import SessionLocal
                from services.database_service import DatabaseService
                db = SessionLocal()
                db_service = DatabaseService(db)
                
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
                db.close()
            except Exception as e:
                st.error(f"İşlem eklenirken hata oluştu: {str(e)}")

def show_budgets():
    """Bütçe sayfasını gösterir."""
    st.title("💰 Bütçe Planlama")
    
    # Modern ve responsive tasarım kullan
    from components.responsive import card
    
    # Bütçe ekleme formu
    with st.form("budget_form"):
        st.subheader("➕ Yeni Bütçe Ekle")
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
                from models.database import SessionLocal
                from services.database_service import DatabaseService
                db = SessionLocal()
                db_service = DatabaseService(db)
                
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
                db.close()
            except Exception as e:
                st.error(f"Bütçe eklenirken hata oluştu: {str(e)}")

def show_goals():
    """Hedefler sayfasını gösterir."""
    st.title("🎯 Finansal Hedefler")
    
    # Hedef ekleme formu
    with st.form("goal_form"):
        st.subheader("➕ Yeni Hedef Ekle")
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
                from models.database import SessionLocal
                from services.database_service import DatabaseService
                db = SessionLocal()
                db_service = DatabaseService(db)
                
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
                db.close()
            except Exception as e:
                st.error(f"Hedef eklenirken hata oluştu: {str(e)}")

def show_reports():
    """Raporlar sayfasını gösterir."""
    st.title("📈 Finansal Raporlar")
    
    # İçeriği zenginleştirme
    st.info("Raporlar modülü yükleniyor. İlk yükleme birkaç saniye sürebilir.")
    
    # Analiz türü seçimi
    analysis_type = st.radio(
        "Analiz Türü",
        ["Aylık Rapor", "Karşılaştırmalı Analiz", "Trend Analizi"],
        horizontal=True
    )
    
    # Demo içerik
    if analysis_type == "Aylık Rapor":
        st.markdown("""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0;">Aylık Rapor Demo</h3>
                <p>Bu bölümde gelir/gider dağılımları ve kategorik harcama analizleri görüntülenecektir.</p>
            </div>
        """, unsafe_allow_html=True)
    elif analysis_type == "Karşılaştırmalı Analiz":
        st.markdown("""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0;">Karşılaştırmalı Analiz Demo</h3>
                <p>Bu bölümde seçilen dönemler arası karşılaştırma sonuçları ve değişim grafikleri görüntülenecektir.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin: 1rem 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0;">Trend Analizi Demo</h3>
                <p>Bu bölümde uzun vadeli trend grafikleri ve tahminleme sonuçları görüntülenecektir.</p>
            </div>
        """, unsafe_allow_html=True)

def show_receipts():
    """Fatura ve makbuz yönetimi sayfasını gösterir."""
    st.title("🧾 Fatura ve Makbuz Yönetimi")
    
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin: 0; color: #212529;'>Makbuz ve Faturalarınızı Otomatik İşleyin</h3>
            <p style='margin-top: 10px; margin-bottom: 0; color: #495057;'>
                Makbuz ve faturalarınızın fotoğraflarını yükleyin, yapay zeka ile otomatik tanıma yaparak işlemlerinize ekleyelim.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Makbuz yükleme bölümü
    st.subheader("📸 Makbuz Yükle")
    uploaded_file = st.file_uploader("Fatura/Makbuz Resmi", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        # Demo işlem
        st.image(uploaded_file, caption="Yüklenen Makbuz", use_column_width=True)
        st.success("Makbuz başarıyla yüklendi ve işleniyor...")

def show_bank_accounts():
    """Banka Hesapları sayfasını gösterir."""
    st.title("🏦 Banka Hesapları")
    
    st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin: 0; color: #212529;'>Banka Hesaplarınızı Yönetin</h3>
            <p style='margin-top: 10px; margin-bottom: 0; color: #495057;'>
                Banka hesaplarınızı ekleyin, işlemlerinizi senkronize edin ve finansal durumunuzu tek yerden takip edin.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Yeni hesap ekleme demo
    with st.form("bank_account_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            bank_name = st.selectbox(
                "Banka",
                ["Ziraat Bankası", "İş Bankası", "Garanti", "Akbank", "Yapı Kredi", "Diğer"]
            )
            account_number = st.text_input("Hesap No (son 4 hane)")
        
        with col2:
            account_name = st.text_input("Hesap Adı (opsiyonel)", placeholder="Örn: Ana Hesap")
            account_type = st.selectbox(
                "Hesap Tipi",
                ["Vadesiz", "Vadeli", "Kredi Kartı", "Diğer"]
            )
        
        access_token = st.text_input(
            "API Erişim Anahtarı (Simülasyon için herhangi bir değer girin)",
            type="password"
        )
        
        submitted = st.form_submit_button("Hesap Ekle")
        
        if submitted:
            st.success("Banka hesabı başarıyla eklendi!")

def show_notifications():
    """Bildirimler sayfasını gösterir."""
    st.title("🔔 Bildirimler")
    
    # Demo bildirimler
    st.markdown("""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #f39c12;">
            <div style="font-weight: 500;">⚠️ Bütçe Uyarısı</div>
            <div style="font-size: 0.9rem; color: #6c757d;">Eğlence kategorisinde bütçenizin %80'ini kullandınız.</div>
        </div>
        <div style="background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #e74c3c;">
            <div style="font-weight: 500;">🚨 Bütçe Aşıldı</div>
            <div style="font-size: 0.9rem; color: #6c757d;">Faturalar kategorisinde bütçenizi ₺120,45 aştınız.</div>
        </div>
        <div style="background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #2ecc71;">
            <div style="font-weight: 500;">✅ Hedef Hatırlatması</div>
            <div style="font-size: 0.9rem; color: #6c757d;">Tatil Fonu hedefinize ulaşmanıza %30 kaldı.</div>
        </div>
    """, unsafe_allow_html=True)

def show_backup():
    """Yedekleme ve geri yükleme sayfasını gösterir."""
    st.title("💾 Yedekleme ve Geri Yükleme")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Verileri Dışa Aktar")
        
        export_format = st.selectbox(
            "Dışa Aktarma Formatı",
            ["Excel", "CSV", "JSON"]
        )
        
        if st.button("Dışa Aktar"):
            st.success("Veriler başarıyla dışa aktarıldı!")
            st.download_button(
                label="İndirmek için tıklayın",
                data="İçerik örneği",
                file_name=f"finansal_veriler.{export_format.lower()}",
                mime="application/octet-stream"
            )
    
    with col2:
        st.subheader("Verileri İçe Aktar")
        
        uploaded_file = st.file_uploader("Yedek dosyasını yükleyin", type=["xlsx", "csv", "json"])
        
        if uploaded_file:
            st.info("Dosya yüklendi, içe aktarım için onaylayın.")
            if st.button("İçe Aktarımı Onayla"):
                st.success("Veriler başarıyla içe aktarıldı!")

def show_dashboard():
    """Genel bakış sayfasını gösterir."""
    st.title("📊 Genel Bakış")
    
    # Kullanıcı hoşgeldin mesajı
    st.markdown(f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;
                  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); border-left: 4px solid #3498db;">
            <h2 style="margin: 0;">Hoş Geldin, {st.session_state.get('username', 'Kullanıcı')}!</h2>
            <p style="margin-top: 0.5rem; margin-bottom: 0;">
                Finansal durumunuz ve hedefleriniz hakkında güncel bilgiler aşağıda görüntülenmektedir.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Üst metrikler
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Aylık Gelir", "₺5,840", "₺240 geçen aya göre")
    
    with col2:
        st.metric("Aylık Gider", "₺3,580", "-₺120 geçen aya göre")
    
    with col3:
        st.metric("Net Durum", "₺2,260", "₺360 geçen aya göre")
    
    # Orta kısım - iki sütunlu düzen
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Son işlemler kartı
        with st.container():
            st.markdown("""
                <div style="background-color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #2c3e50;">💸 Son İşlemler</h3>
                    <div style="max-height: 300px; overflow-y: auto;">
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee;">
                            <div>
                                <div style="font-weight: 500;">Market Alışverişi</div>
                                <div style="font-size: 0.8rem; color: #6c757d;">Gıda</div>
                            </div>
                            <div style="color: #e74c3c; font-weight: 500;">-₺245,60</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee;">
                            <div>
                                <div style="font-weight: 500;">Maaş</div>
                                <div style="font-size: 0.8rem; color: #6c757d;">Gelir</div>
                            </div>
                            <div style="color: #2ecc71; font-weight: 500;">+₺5,840</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee;">
                            <div>
                                <div style="font-weight: 500;">Elektrik Faturası</div>
                                <div style="font-size: 0.8rem; color: #6c757d;">Faturalar</div>
                            </div>
                            <div style="color: #e74c3c; font-weight: 500;">-₺168,75</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0;">
                            <div>
                                <div style="font-weight: 500;">Kira</div>
                                <div style="font-size: 0.8rem; color: #6c757d;">Konut</div>
                            </div>
                            <div style="color: #e74c3c; font-weight: 500;">-₺1,750</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Buton olarak ekle
            if st.button("Tüm İşlemleri Görüntüle →", key="btn_all_transactions"):
                st.session_state.page = "İşlemler"
                st.experimental_rerun()
        
        # Harcama Dağılımı Grafiği
        st.markdown("""
            <div style="background-color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #2c3e50;">📊 Harcama Dağılımı</h3>
                <div style="height: 200px; display: flex; align-items: center; justify-content: center;">
                    <img src="https://via.placeholder.com/500x200" style="max-width: 100%; max-height: 100%;" alt="Harcama grafiği">
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Bütçe Takibi Kartı
        with st.container():
            st.markdown("""
                <div style="background-color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #2c3e50;">💰 Bütçe Takibi</h3>
                    <div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: 500;">Gıda</div>
                                <div>₺845,30 / ₺1,200</div>
                            </div>
                            <div style="height: 8px; background-color: #f1f1f1; border-radius: 4px;">
                                <div style="width: 70%; height: 100%; background-color: #3498db; border-radius: 4px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: 500;">Ulaşım</div>
                                <div>₺320,45 / ₺500</div>
                            </div>
                            <div style="height: 8px; background-color: #f1f1f1; border-radius: 4px;">
                                <div style="width: 64%; height: 100%; background-color: #3498db; border-radius: 4px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: 500;">Eğlence</div>
                                <div>₺480,25 / ₺400</div>
                            </div>
                            <div style="height: 8px; background-color: #f1f1f1; border-radius: 4px;">
                                <div style="width: 120%; height: 100%; background-color: #e74c3c; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Buton olarak ekle
            if st.button("Tüm Bütçeleri Görüntüle →", key="btn_all_budgets"):
                st.session_state.page = "Bütçe"
                st.experimental_rerun()
        
        # Hedefler Kartı
        with st.container():
            st.markdown("""
                <div style="background-color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #2c3e50;">🎯 Hedefler</h3>
                    <div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: 500;">Tatil Fonu</div>
                                <div>₺3,500 / ₺5,000</div>
                            </div>
                            <div style="height: 8px; background-color: #f1f1f1; border-radius: 4px;">
                                <div style="width: 70%; height: 100%; background-color: #2ecc71; border-radius: 4px;"></div>
                            </div>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <div style="font-weight: 500;">Yeni Bilgisayar</div>
                                <div>₺4,200 / ₺8,000</div>
                            </div>
                            <div style="height: 8px; background-color: #f1f1f1; border-radius: 4px;">
                                <div style="width: 52.5%; height: 100%; background-color: #f39c12; border-radius: 4px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Buton olarak ekle
            if st.button("Tüm Hedefleri Görüntüle →", key="btn_all_goals"):
                st.session_state.page = "Hedefler"
                st.experimental_rerun()
        
    # Alt kısım - bildirimler
    st.markdown("### 🔔 Son Bildirimler")
    
    bildirim_col1, bildirim_col2 = st.columns([3, 1])
    
    with bildirim_col1:
        st.markdown("""
            <div style="background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #f39c12;">
                <div style="font-weight: 500;">⚠️ Eğlence bütçeniz aşıldı</div>
                <div style="font-size: 0.9rem; color: #6c757d;">Eğlence kategorisinde bütçenizi ₺80,25 aştınız.</div>
            </div>
            <div style="background-color: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border-left: 4px solid #2ecc71;">
                <div style="font-weight: 500;">✅ Tatil fonunuz %70 tamamlandı</div>
                <div style="font-size: 0.9rem; color: #6c757d;">Tatil hedefinize ulaşmak için ₺1,500 daha biriktirmeniz gerekiyor.</div>
            </div>
        """, unsafe_allow_html=True)
    
    with bildirim_col2:
        if st.button("Tüm Bildirimleri Gör", key="btn_all_notifications", use_container_width=True):
            st.session_state.page = "Bildirimler"
            st.experimental_rerun() 