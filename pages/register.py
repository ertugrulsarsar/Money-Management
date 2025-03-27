import streamlit as st
from services.auth_service import AuthService
from models.database import init_db, get_db

def setup_page():
    """Sayfa yapılandırmasını ayarlar."""
    st.set_page_config(
        page_title="Kayıt Ol",
        page_icon="📝",
        layout="centered"
    )
    
    # CSS ile tema özelleştirmesi
    st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
            color: #2c3e50;
        }
        .register-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton button {
            background-color: #1f77b4;
            color: white;
            border-radius: 5px;
            padding: 0.5rem 1rem;
            border: none;
            transition: all 0.3s ease;
            width: 100%;
        }
        .stButton button:hover {
            background-color: #ff7f0e;
            transform: translateY(-2px);
        }
        .stTextInput input {
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem;
        }
        .stTextInput input:focus {
            border-color: #1f77b4;
            box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2);
        }
        .error-message {
            color: #dc3545;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .success-message {
            color: #28a745;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 5px;
            padding: 1rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Ana uygulama fonksiyonu."""
    setup_page()
    
    # Veritabanını başlat
    init_db()
    
    # Auth servisini başlat
    db = next(get_db())
    auth_service = AuthService(db)
    
    # Sayfa başlığı
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1 style='color: #1f77b4;'>📝 Yeni Hesap Oluştur</h1>
        <p style='color: #6c757d;'>Finansal yolculuğunuza başlayın</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Kayıt formu
    with st.container():
        st.markdown('<div class="register-container">', unsafe_allow_html=True)
        
        st.markdown("### 👤 Kayıt Bilgileri")
        
        with st.form("register_form"):
            username = st.text_input("Kullanıcı Adı")
            email = st.text_input("E-posta")
            password = st.text_input("Şifre", type="password")
            confirm_password = st.text_input("Şifre Tekrar", type="password")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                submitted = st.form_submit_button("Kayıt Ol")
            with col2:
                if st.form_submit_button("Giriş Yap", type="secondary"):
                    st.switch_page("pages/login.py")
        
        if submitted:
            try:
                if password != confirm_password:
                    st.markdown("""
                    <div class="error-message">
                        ❌ Şifreler eşleşmiyor!
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    user = auth_service.create_user(username, email, password)
                    if user:
                        st.markdown("""
                        <div class="success-message">
                            ✅ Kayıt başarılı! Giriş yapabilirsiniz.
                        </div>
                        """, unsafe_allow_html=True)
                        st.switch_page("pages/login.py")
                    else:
                        st.markdown("""
                        <div class="error-message">
                            ❌ Bu kullanıcı adı zaten kullanılıyor!
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="error-message">
                    ❌ Kayıt olurken bir hata oluştu: {str(e)}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Alt bilgi
        st.markdown("""
        <div style='text-align: center; margin-top: 2rem; color: #6c757d;'>
            <p>Zaten hesabınız var mı? Giriş yapın</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 