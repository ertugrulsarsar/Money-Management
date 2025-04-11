import locale
from typing import Optional, Union
from datetime import datetime, date

def format_currency(amount: Union[float, int], currency_symbol: str = "₺", decimal_places: int = 2) -> str:
    """Para birimini formatlar."""
    try:
        # Locale ayarını değiştirmeye çalış
        locale.setlocale(locale.LC_ALL, "tr_TR.UTF-8")
    except locale.Error:
        try:
            # Alternatif locale dene
            locale.setlocale(locale.LC_ALL, "tr_TR")
        except locale.Error:
            # Locale ayarlanamıyorsa manuel format kullan
            pass
    
    try:
        # Locale kullanarak para birimini formatla
        formatted = locale.currency(amount, symbol=False, grouping=True)
        # Sembol ekle
        return f"{formatted} {currency_symbol}"
    except (locale.Error, AttributeError):
        # Manuel formatlama
        formatted = f"{amount:,.{decimal_places}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{formatted} {currency_symbol}"

def format_date(dt: Optional[Union[datetime, date]] = None, format_str: str = "%d.%m.%Y") -> str:
    """Tarihi formatlar."""
    if dt is None:
        dt = datetime.now()
    
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    elif isinstance(dt, date):
        return dt.strftime(format_str)
    else:
        raise ValueError("Geçersiz tarih türü")

def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Yüzdeyi formatlar."""
    return f"%{value:.{decimal_places}f}".replace(".", ",")

def short_number(num: Union[int, float], decimal_places: int = 1) -> str:
    """Büyük sayıları kısa formatta gösterir. Örn: 1.2K, 3.4M"""
    abs_num = abs(num)
    sign = "-" if num < 0 else ""
    
    if abs_num < 1000:
        return f"{sign}{abs_num:.{decimal_places}f}".rstrip('0').rstrip('.') if '.' in f"{abs_num:.{decimal_places}f}" else f"{sign}{abs_num:.0f}"
    elif abs_num < 1000000:
        return f"{sign}{abs_num/1000:.{decimal_places}f}B".replace(".", ",")
    elif abs_num < 1000000000:
        return f"{sign}{abs_num/1000000:.{decimal_places}f}M".replace(".", ",")
    elif abs_num < 1000000000000:
        return f"{sign}{abs_num/1000000000:.{decimal_places}f}Mr".replace(".", ",")
    else:
        return f"{sign}{abs_num/1000000000000:.{decimal_places}f}T".replace(".", ",") 