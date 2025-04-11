import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, User, Transaction, Budget, FinancialGoal
from services.report_service import ReportService
from datetime import date, timedelta

# Test veritabanı oluşturmak için
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Test veritabanı için oturum oluşturur."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def report_service(db_session):
    """Test için ReportService nesnesi oluşturur."""
    return ReportService(db_session)

@pytest.fixture
def test_user(db_session):
    """Test için kullanıcı oluşturur."""
    # Önce bu e-posta ile kullanıcı var mı kontrol et
    existing_user = db_session.query(User).filter_by(email="test@example.com").first()
    
    if existing_user:
        return existing_user
        
    user = User(
        username="test_user",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_data(db_session, test_user):
    """Test için işlemler oluşturur."""
    # Bugünün tarihi
    today = date.today()
    
    # Mevcut ay için işlemler (örneğin, Nisan 2023)
    current_month = today.month
    current_year = today.year
    
    # Önceki ay için işlemler (örneğin, Mart 2023)
    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_year = current_year
    
    # Mevcut ay işlemleri
    current_transactions = [
        # Gelirler
        Transaction(
            user_id=test_user.id,
            amount=5000,
            type="income",
            category="Maaş",
            description="Aylık maaş",
            date=date(current_year, current_month, 15)
        ),
        Transaction(
            user_id=test_user.id,
            amount=1000,
            type="income",
            category="Ek Gelir",
            description="Freelance iş",
            date=date(current_year, current_month, 20)
        ),
        # Giderler
        Transaction(
            user_id=test_user.id,
            amount=1500,
            type="expense",
            category="Kira",
            description="Aylık kira",
            date=date(current_year, current_month, 1)
        ),
        Transaction(
            user_id=test_user.id,
            amount=800,
            type="expense",
            category="Gıda",
            description="Market alışverişi",
            date=date(current_year, current_month, 5)
        ),
        Transaction(
            user_id=test_user.id,
            amount=300,
            type="expense",
            category="Ulaşım",
            description="Benzin",
            date=date(current_year, current_month, 10)
        ),
        Transaction(
            user_id=test_user.id,
            amount=400,
            type="expense",
            category="Eğlence",
            description="Sinema ve restoran",
            date=date(current_year, current_month, 25)
        )
    ]
    
    # Önceki ay işlemleri
    previous_transactions = [
        # Gelirler
        Transaction(
            user_id=test_user.id,
            amount=4800,
            type="income",
            category="Maaş",
            description="Aylık maaş",
            date=date(previous_year, previous_month, 15)
        ),
        Transaction(
            user_id=test_user.id,
            amount=500,
            type="income",
            category="Ek Gelir",
            description="Freelance iş",
            date=date(previous_year, previous_month, 20)
        ),
        # Giderler
        Transaction(
            user_id=test_user.id,
            amount=1500,
            type="expense",
            category="Kira",
            description="Aylık kira",
            date=date(previous_year, previous_month, 1)
        ),
        Transaction(
            user_id=test_user.id,
            amount=600,
            type="expense",
            category="Gıda",
            description="Market alışverişi",
            date=date(previous_year, previous_month, 5)
        ),
        Transaction(
            user_id=test_user.id,
            amount=200,
            type="expense",
            category="Ulaşım",
            description="Benzin",
            date=date(previous_year, previous_month, 10)
        ),
        Transaction(
            user_id=test_user.id,
            amount=300,
            type="expense",
            category="Eğlence",
            description="Sinema",
            date=date(previous_year, previous_month, 25)
        )
    ]
    
    # Tüm işlemleri ekle
    db_session.add_all(current_transactions + previous_transactions)
    db_session.commit()
    
    return {
        "user_id": test_user.id,
        "current_year": current_year,
        "current_month": current_month,
        "previous_year": previous_year,
        "previous_month": previous_month
    }

def test_generate_comparative_analysis(report_service, test_data):
    """Karşılaştırmalı analiz oluşturma fonksiyonunu test eder."""
    # Karşılaştırmalı analiz oluştur
    comparative_data = report_service.generate_comparative_analysis(
        user_id=test_data["user_id"],
        current_year=test_data["current_year"],
        current_month=test_data["current_month"],
        comparison_type="previous_month"
    )
    
    # Veri yapısı kontrol
    assert comparative_data is not None
    assert "current_report" in comparative_data
    assert "previous_report" in comparative_data
    assert "comparison" in comparative_data
    
    # Mevcut dönem verileri kontrol
    current_report = comparative_data["current_report"]
    assert current_report["summary"]["total_income"] == 6000  # 5000 + 1000
    assert current_report["summary"]["total_expense"] == 3000  # 1500 + 800 + 300 + 400
    assert current_report["summary"]["net_amount"] == 3000  # 6000 - 3000
    
    # Önceki dönem verileri kontrol
    previous_report = comparative_data["previous_report"]
    assert previous_report["summary"]["total_income"] == 5300  # 4800 + 500
    assert previous_report["summary"]["total_expense"] == 2600  # 1500 + 600 + 200 + 300
    assert previous_report["summary"]["net_amount"] == 2700  # 5300 - 2600
    
    # Karşılaştırma verileri kontrol
    comparison = comparative_data["comparison"]
    
    # Gelir değişimi
    assert comparison["income_change"]["amount"] == 700  # 6000 - 5300
    assert abs(comparison["income_change"]["percentage"] - 13.2) < 0.1  # (700 / 5300) * 100 ≈ 13.2%
    
    # Gider değişimi
    assert comparison["expense_change"]["amount"] == 400  # 3000 - 2600
    assert abs(comparison["expense_change"]["percentage"] - 15.4) < 0.1  # (400 / 2600) * 100 ≈ 15.4%
    
    # Net değişim
    assert comparison["net_amount_change"]["amount"] == 300  # 3000 - 2700
    assert abs(comparison["net_amount_change"]["percentage"] - 11.1) < 0.1  # (300 / 2700) * 100 ≈ 11.1%
    
    # Kategori karşılaştırması kontrolü
    category_comparison = comparison["category_comparison"]
    assert "Gıda" in category_comparison
    assert "Ulaşım" in category_comparison
    assert "Eğlence" in category_comparison
    assert "Kira" in category_comparison
    
    # Gıda kategorisi
    assert category_comparison["Gıda"]["old_value"] == 600
    assert category_comparison["Gıda"]["new_value"] == 800
    assert category_comparison["Gıda"]["change"] == 200
    assert abs(category_comparison["Gıda"]["percentage"] - 33.33) < 0.1  # (200 / 600) * 100 ≈ 33.33%
    
    # Ulaşım kategorisi
    assert category_comparison["Ulaşım"]["old_value"] == 200
    assert category_comparison["Ulaşım"]["new_value"] == 300
    assert category_comparison["Ulaşım"]["change"] == 100
    assert abs(category_comparison["Ulaşım"]["percentage"] - 50.0) < 0.1  # (100 / 200) * 100 = 50%
    
    # Eğlence kategorisi
    assert category_comparison["Eğlence"]["old_value"] == 300
    assert category_comparison["Eğlence"]["new_value"] == 400
    assert category_comparison["Eğlence"]["change"] == 100
    assert abs(category_comparison["Eğlence"]["percentage"] - 33.33) < 0.1  # (100 / 300) * 100 ≈ 33.33%
    
    # Kira kategorisi (değişim yok)
    assert category_comparison["Kira"]["old_value"] == 1500
    assert category_comparison["Kira"]["new_value"] == 1500
    assert category_comparison["Kira"]["change"] == 0
    assert category_comparison["Kira"]["percentage"] == 0.0  # (0 / 1500) * 100 = 0%

def test_create_comparison_chart(report_service, test_data):
    """Karşılaştırma grafiği oluşturma fonksiyonunu test eder."""
    # Örnek karşılaştırma verisi
    comparison_data = {
        "category_comparison": {
            "Gıda": {
                "old_value": 600,
                "new_value": 800,
                "change": 200,
                "percentage": 33.33
            },
            "Ulaşım": {
                "old_value": 200,
                "new_value": 300,
                "change": 100,
                "percentage": 50.0
            },
            "Eğlence": {
                "old_value": 300,
                "new_value": 400,
                "change": 100,
                "percentage": 33.33
            },
            "Kira": {
                "old_value": 1500,
                "new_value": 1500,
                "change": 0,
                "percentage": 0.0
            }
        },
        "current_period": {
            "year": test_data["current_year"],
            "month": test_data["current_month"]
        },
        "previous_period": {
            "year": test_data["previous_year"],
            "month": test_data["previous_month"]
        }
    }
    
    # Grafik oluştur
    chart = report_service.create_comparison_chart(comparison_data)
    
    # Grafiğin var olduğunu kontrol et
    assert chart is not None
    
    # Grafiğin doğru tipe sahip olduğunu kontrol et
    assert chart.layout.title.text == "Kategori Bazlı Harcama Karşılaştırması"
    
    # En az iki veri seti olduğunu kontrol et (önceki ve mevcut dönem)
    assert len(chart.data) == 2
    
    # İlk veri setinin (önceki dönem) özelliklerini kontrol et
    assert chart.data[0].name == f"Önceki Dönem ({test_data['previous_month']}/{test_data['previous_year']})"
    
    # İkinci veri setinin (mevcut dönem) özelliklerini kontrol et
    assert chart.data[1].name == f"Mevcut Dönem ({test_data['current_month']}/{test_data['current_year']})"

def test_create_trend_chart(report_service, test_data):
    """Trend grafiği oluşturma fonksiyonunu test eder."""
    # Trend grafiği oluştur
    chart = report_service.create_trend_chart(test_data["user_id"], 2)
    
    # Grafiğin var olduğunu kontrol et
    assert chart is not None
    
    # Grafiğin doğru tipe sahip olduğunu kontrol et
    assert chart.layout.title.text == "Aylık Finansal Trend"
    
    # En az üç veri seti olduğunu kontrol et (gelir, gider, net durum)
    assert len(chart.data) == 3
    
    # Veri setlerinin isimlerini kontrol et
    assert chart.data[0].name == "Gelir"
    assert chart.data[1].name == "Gider"
    assert chart.data[2].name == "Net Durum" 