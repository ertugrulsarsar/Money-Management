import streamlit as st
import json
import random

def create_sidebar():
    """Gelişmiş sidebar navigasyonu oluşturur ve seçilen sayfayı döndürür."""
    
    # Kullanıcı bilgileri
    user_id = st.session_state.get("user_id", 1)
    username = st.session_state.get("username", "Kullanıcı")
    
    # Sidebar için rastgele bir anahtar oluştur
    if "sidebar_key" not in st.session_state:
        st.session_state.sidebar_key = random.randint(10000, 99999)
    
    # CSS stilleri
    sidebar_css = """
    <style>
    [data-testid=stSidebar] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    [data-testid=stSidebar] > div:first-child {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    
    .sidebar-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .sidebar-header img {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        object-fit: cover;
        margin-bottom: 0.5rem;
        border: 3px solid white;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .sidebar-header h3 {
        margin: 0;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    .sidebar-header p {
        margin: 0;
        color: #6c757d;
        font-size: 0.85rem;
    }
    
    .sidebar-menu {
        margin-top: 1.5rem;
    }
    
    .menu-item {
        display: flex;
        align-items: center;
        padding: 0.7rem 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        text-decoration: none;
        color: #495057;
    }
    
    .menu-item:hover {
        background-color: rgba(52, 152, 219, 0.1);
        color: #3498db;
    }
    
    .menu-item.selected {
        background-color: #3498db;
        color: white;
    }
    
    .menu-icon {
        margin-right: 0.75rem;
        width: 24px;
        text-align: center;
    }
    
    .badge {
        margin-left: auto;
        background-color: #e74c3c;
        color: white;
        border-radius: 10px;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
    }
    
    .menu-section {
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
        color: #6c757d;
        padding-left: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .sidebar-footer {
        text-align: center;
        margin-top: 3rem;
        padding: 0 1rem;
    }
    
    .version {
        font-size: 0.75rem;
        color: #adb5bd;
    }
    </style>
    """
    
    # JavaScript kodu
    sidebar_js = """
    <script>
    // Sayfa navigasyonu için yardımcı fonksiyon
    function navigateTo(path, pageName) {
        console.log('Navigating to', path, 'with page name', pageName);
        
        // Session state güncelleme
        window.parent.postMessage({
            type: 'streamlit:setSessionState',
            state: { page: pageName }
        }, '*');
        
        // Sayfaya git
        setTimeout(() => {
            window.parent.location.href = path;
        }, 100);
        
        return false;
    }
    
    // Çıkış yap
    function logOut() {
        console.log('Logging out');
        
        // Session state'i temizle
        window.parent.postMessage({
            type: 'streamlit:setSessionState',
            state: { user_id: null, username: null, page: null }
        }, '*');
        
        // Login sayfasına git
        setTimeout(() => {
            window.parent.location.href = 'pages/login.py';
        }, 100);
        
        return false;
    }
    
    // Sayfa yüklendiğinde
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Setting up click handlers for navigation');
        
        // Menü öğelerine tıklama olayı ekle
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const path = this.getAttribute('data-path');
                const page = this.getAttribute('data-page');
                
                if (path === 'logout') {
                    logOut();
                } else {
                    navigateTo(path, page);
                }
                
                return false;
            });
        });
    });
    </script>
    """
    
    # Menü öğeleri
    menu_items = [
        {"name": "Genel Bakış", "icon": "📊", "path": "app.py"},
        {"name": "İşlemler", "icon": "💸", "path": "pages/transactions.py"},
        {"name": "Bütçe", "icon": "📋", "path": "pages/budget.py"},
        {"name": "Hedefler", "icon": "🎯", "path": "pages/goals.py"},
        {"name": "Raporlar", "icon": "📈", "path": "pages/reports.py"},
        {"name": "Bildirimler", "icon": "🔔", "path": "pages/notifications.py", "badge": 3}
    ]
    
    # Ayarlar menüsü
    settings_menu = [
        {"name": "Hesap Ayarları", "icon": "👤", "path": "pages/account.py"},
        {"name": "Kategoriler", "icon": "🏷️", "path": "pages/categories.py"},
        {"name": "Bildirim Tercihleri", "icon": "🔔", "path": "pages/notification_settings.py"},
        {"name": "Yardım", "icon": "❓", "path": "pages/help.py"},
        {"name": "Çıkış Yap", "icon": "🚪", "path": "logout"}
    ]
    
    # Mevcut seçili sayfa
    current_page = st.session_state.get("page", "Genel Bakış")
    
    # Sidebar HTML
    sidebar_html = f"""
    {sidebar_css}
    {sidebar_js}
    
    <div class="sidebar-container">
        <div class="sidebar-header">
            <img src="https://ui-avatars.com/api/?name={username}&background=random" alt="{username}" />
            <h3>{username}</h3>
            <p>Hoş geldiniz!</p>
        </div>
        
        <div class="sidebar-menu">
    """
    
    # Menü öğelerini ekle
    for item in menu_items:
        selected = "selected" if item["name"] == current_page else ""
        badge_html = f'<span class="badge">{item.get("badge", "")}</span>' if "badge" in item else ""
        
        sidebar_html += f"""
            <a class="menu-item {selected}" 
               href="#" 
               data-path="{item['path']}" 
               data-page="{item['name']}">
                <span class="menu-icon">{item['icon']}</span>
                {item['name']}
                {badge_html}
            </a>
        """
    
    # Ayarlar bölümü
    sidebar_html += '<div class="menu-section">Ayarlar</div>'
    
    for item in settings_menu:
        selected = "selected" if item["name"] == current_page else ""
        
        sidebar_html += f"""
            <a class="menu-item {selected}" 
               href="#" 
               data-path="{item['path']}" 
               data-page="{item['name']}">
                <span class="menu-icon">{item['icon']}</span>
                {item['name']}
            </a>
        """
    
    # Sidebar alt kısmı
    sidebar_html += """
        </div>
        
        <div class="sidebar-footer">
            <p class="version">Kişisel Finans v1.0.0</p>
        </div>
    </div>
    
    <!-- JavaScript kullanılamadığında yedek butonlar (gizli) -->
    <div id="fallback-buttons" style="display: none;">
    """
    
    # Sidebar HTML'i ekle
    st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)
    
    # JavaScript kullanılamadığında yedek butonlar
    for item in menu_items + settings_menu:
        if item["path"] != "logout":
            button_key = f"nav_{item['name']}_{st.session_state.sidebar_key}"
            if st.sidebar.button(item["name"], key=button_key, use_container_width=True, type="secondary"):
                st.session_state.page = item["name"]
                st.switch_page(item["path"])
        else:
            if st.sidebar.button("Çıkış Yap", key=f"logout_{st.session_state.sidebar_key}", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.switch_page("pages/login.py")
    
    return current_page 