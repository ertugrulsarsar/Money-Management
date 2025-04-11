import streamlit as st

def responsive_grid(content_list, num_columns=3, mobile_columns=1, gap="1rem", height="auto"):
    """
    Responsive grid oluşturur.
    
    Args:
        content_list: İçerik listesi
        num_columns: Normal ekranlarda gösterilecek sütun sayısı
        mobile_columns: Mobil ekranlarda gösterilecek sütun sayısı
        gap: Grid içindeki boşluk miktarı
        height: Grid yüksekliği
    """
    
    # CSS ile responsive grid tanımla
    st.markdown(f"""
        <style>
            .responsive-grid {{
                display: grid;
                grid-template-columns: repeat({num_columns}, 1fr);
                grid-gap: {gap};
                height: {height};
            }}
            
            @media (max-width: 768px) {{
                .responsive-grid {{
                    grid-template-columns: repeat({mobile_columns}, 1fr);
                }}
            }}
        </style>
        
        <div class="responsive-grid">
            {"".join(content_list)}
        </div>
    """, unsafe_allow_html=True)

def responsive_columns(widths=None):
    """
    Responsive sütunlar oluşturur.
    
    Args:
        widths: Sütun genişliklerinin oransal listesi
    
    Returns:
        Oluşturulan sütunlar
    """
    if not widths:
        return st.columns(1)
    return st.columns(widths)

def responsive_metrics(metrics_data):
    """
    Basit metrikler oluşturur (st.metric kullanarak)
    
    Args:
        metrics_data: [{"label": "", "value": "", "delta": ""}] formatında metrik listesi
    """
    cols = st.columns(len(metrics_data))
    for i, metric in enumerate(metrics_data):
        with cols[i]:
            st.metric(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta", None)
            )

def card(title, content, icon=None, border_color=None):
    """
    Özelleştirilmiş kart bileşeni.
    
    Args:
        title: Kart başlığı
        content: Kart içeriği (HTML olarak)
        icon: Kart ikonu (emoji)
        border_color: Kart kenar rengi
    """
    border_style = f"border-left: 4px solid {border_color};" if border_color else ""
    title_with_icon = f"{icon} {title}" if icon else title
    
    st.markdown(f"""
        <div style="background-color: white; padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); {border_style}">
            <h3 style="margin-top: 0; margin-bottom: 1rem; font-size: 1.2rem; color: #2c3e50;">{title_with_icon}</h3>
            {content}
        </div>
    """, unsafe_allow_html=True)

def mobile_hide(content):
    """
    Mobil cihazlarda saklanacak içerik oluşturur.
    
    Args:
        content: HTML içeriği
    """
    st.markdown(f"""
        <style>
            @media (max-width: 768px) {{
                .mobile-hidden {{
                    display: none;
                }}
            }}
        </style>
        <div class="mobile-hidden">
            {content}
        </div>
    """, unsafe_allow_html=True)

def mobile_only(content):
    """
    Sadece mobil ekranlarda gösterilecek içerik oluşturur.
    
    Args:
        content: Gösterilecek HTML içeriği
    """
    st.markdown(f"""
        <style>
            @media (min-width: 769px) {{
                .mobile-only {{
                    display: none;
                }}
            }}
        </style>
        <div class="mobile-only">
            {content}
        </div>
    """, unsafe_allow_html=True) 