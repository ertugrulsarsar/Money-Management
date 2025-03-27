from datetime import datetime, date, timedelta
from typing import Tuple, Dict, Any


def get_month_range(year: int, month: int) -> Tuple[datetime, datetime]:
    """Belirli bir ay için başlangıç ve bitiş tarihini döndürür."""
    start_date = datetime(year, month, 1)
    
    # Bir sonraki ayın ilk gününü bul ve 1 gün çıkar
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Gün sonuna ayarla
    end_date = datetime.combine(end_date, datetime.max.time())
    
    return start_date, end_date


def get_date_filters() -> Dict[str, Any]:
    """Tarih filtreleri için ortak parametreleri döndürür."""
    current_date = date.today()
    current_year = current_date.year
    years = list(range(current_year - 5, current_year + 1))
    months = list(range(1, 13))
    
    return {
        "years": years,
        "months": months,
        "current_year": current_year,
        "current_month": current_date.month
    }


def month_name(month_number: int) -> str:
    """Ay numarasından ay adını döndürür."""
    months = [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
    ]
    return months[month_number - 1] 