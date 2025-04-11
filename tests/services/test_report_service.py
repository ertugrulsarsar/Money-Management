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
def test_transactions(db_session, test_user):
    """Test için işlemler oluşturur."""
    today = date.today()
    
    # Bu ayki tarihler için
    current_month = today.month
    current_year = today.year
    
    # Gelirler - Bu ay içinde olduğundan emin ol
    income1 = Transaction(
        user_id=test_user.id,
        amount=1000,
        type="income",
        category="Maaş",
        description="Aylık maaş",
        date=date(current_year, current_month, 5)
    )
    
    income2 = Transaction(
        user_id=test_user.id,
        amount=500,
        type="income",
        category="Ek Gelir",
        description="Danışmanlık",
        date=date(current_year, current_month, 10)
    )
    
    # Giderler - Bu ay içinde olduğundan emin ol
    expense1 = Transaction(
        user_id=test_user.id,
        amount=300,
        type="expense",
        category="Gıda",
        description="Market alışverişi",
        date=date(current_year, current_month, 15)
    )
    
    expense2 = Transaction(
        user_id=test_user.id,
        amount=150,
        type="expense",
        category="Ulaşım",
        description="Benzin",
        date=date(current_year, current_month, 20)
    )
    
    expense3 = Transaction(
        user_id=test_user.id,
        amount=200,
        type="expense",
        category="Eğlence",
        description="Sinema",
        date=date(current_year, current_month, 25)
    )
    
    db_session.add_all([income1, income2, expense1, expense2, expense3])
    db_session.commit()
    
    return [income1, income2, expense1, expense2, expense3]

@pytest.fixture
def test_budgets(db_session, test_user):
    """Test için bütçeler oluşturur."""
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    end_of_month = end_of_month - timedelta(days=1)
    
    budget1 = Budget(
        user_id=test_user.id,
        category="Gıda",
        amount=500,
        period="monthly",
        start_date=start_of_month,
        end_date=end_of_month
    )
    
    budget2 = Budget(
        user_id=test_user.id,
        category="Ulaşım",
        amount=300,
        period="monthly",
        start_date=start_of_month,
        end_date=end_of_month
    )
    
    budget3 = Budget(
        user_id=test_user.id,
        category="Eğlence",
        amount=200,
        period="monthly",
        start_date=start_of_month,
        end_date=end_of_month
    )
    
    db_session.add_all([budget1, budget2, budget3])
    db_session.commit()
    
    return [budget1, budget2, budget3]

@pytest.fixture
def test_goals(db_session, test_user):
    """Test için hedefler oluşturur."""
    today = date.today()
    
    goal1 = FinancialGoal(
        user_id=test_user.id,
        name="Araba",
        target_amount=50000,
        current_amount=10000,
        deadline=today + timedelta(days=365),
        priority="high"
    )
    
    goal2 = FinancialGoal(
        user_id=test_user.id,
        name="Tatil",
        target_amount=15000,
        current_amount=5000,
        deadline=today + timedelta(days=180),
        priority="medium"
    )
    
    db_session.add_all([goal1, goal2])
    db_session.commit()
    
    return [goal1, goal2]

def test_generate_monthly_report(report_service, test_user, test_transactions, test_budgets, test_goals):
    """Aylık rapor oluşturma fonksiyonunu test eder."""
    today = date.today()
    year = today.year
    month = today.month
    
    report = report_service.generate_monthly_report(test_user.id, year, month)
    
    # Rapor oluşturuldu mu kontrol et
    assert report is not None
    
    # Özet doğru mu kontrol et
    assert report["summary"]["total_income"] == 1500  # 1000 + 500
    assert report["summary"]["total_expense"] == 650  # 300 + 150 + 200
    assert report["summary"]["net_amount"] == 850  # 1500 - 650
    
    # Kategori bazlı harcamalar doğru mu kontrol et
    assert report["expense_by_category"]["Gıda"] == 300
    assert report["expense_by_category"]["Ulaşım"] == 150
    assert report["expense_by_category"]["Eğlence"] == 200
    
    # Bütçe performansı doğru mu kontrol et
    assert report["budget_performance"]["Gıda"]["limit"] == 500
    assert report["budget_performance"]["Gıda"]["spent"] == 300
    assert report["budget_performance"]["Gıda"]["remaining"] == 200
    
    assert report["budget_performance"]["Ulaşım"]["limit"] == 300
    assert report["budget_performance"]["Ulaşım"]["spent"] == 150
    assert report["budget_performance"]["Ulaşım"]["remaining"] == 150
    
    assert report["budget_performance"]["Eğlence"]["limit"] == 200
    assert report["budget_performance"]["Eğlence"]["spent"] == 200
    assert report["budget_performance"]["Eğlence"]["remaining"] == 0
    
    # Hedef ilerlemesi doğru mu kontrol et
    assert len(report["goal_progress"]) == 2
    
    # İşlemler var mı kontrol et
    assert len(report["transactions"]) == 5

def test_create_expense_chart(report_service):
    """Harcama grafiği oluşturma fonksiyonunu test eder."""
    expense_data = {
        "Gıda": 300,
        "Ulaşım": 150,
        "Eğlence": 200
    }
    
    chart = report_service.create_expense_chart(expense_data)
    
    # Grafik oluşturuldu mu kontrol et
    assert chart is not None
    
    # Grafik doğru tipe sahip mi kontrol et
    assert chart.layout.title.text == "Harcamalarınızın Dağılımı"
    
    # Veri noktaları doğru mu kontrol et
    pie_data = chart.data[0]
    assert sorted(list(pie_data.labels)) == sorted(["Gıda", "Ulaşım", "Eğlence"])
    assert sorted(list(pie_data.values)) == sorted([300, 150, 200])

def test_create_budget_chart(report_service):
    """Bütçe grafiği oluşturma fonksiyonunu test eder."""
    budget_data = {
        "Gıda": {
            "limit": 500,
            "spent": 300,
            "remaining": 200
        },
        "Ulaşım": {
            "limit": 300,
            "spent": 150,
            "remaining": 150
        },
        "Eğlence": {
            "limit": 200,
            "spent": 200,
            "remaining": 0
        }
    }
    
    chart = report_service.create_budget_chart(budget_data)
    
    # Grafik oluşturuldu mu kontrol et
    assert chart is not None
    
    # Grafik doğru tipe sahip mi kontrol et
    assert chart.layout.title.text == "Bütçe Durumunuz"
    
    # Veri noktaları doğru mu kontrol et
    assert len(chart.data) == 2  # İki çubuk tipi: limit ve harcanan
    
    # Limitler doğru mu kontrol et
    limit_data = chart.data[0]
    assert limit_data.name == "Bütçe Limiti"
    assert sorted(list(limit_data.x)) == sorted(["Gıda", "Ulaşım", "Eğlence"])
    assert sorted(list(limit_data.y)) == sorted([500, 300, 200])
    
    # Harcamalar doğru mu kontrol et
    spent_data = chart.data[1]
    assert spent_data.name == "Harcanan"
    assert sorted(list(spent_data.y)) == sorted([300, 150, 200])

def test_create_goal_chart(report_service):
    """Hedef grafiği oluşturma fonksiyonunu test eder."""
    goal_progress = [
        {
            "name": "Araba",
            "target": 50000,
            "current": 10000,
            "progress": 20.0,
            "deadline": date.today() + timedelta(days=365),
            "priority": "high"
        },
        {
            "name": "Tatil",
            "target": 15000,
            "current": 5000,
            "progress": 33.33,
            "deadline": date.today() + timedelta(days=180),
            "priority": "medium"
        }
    ]
    
    chart = report_service.create_goal_chart(goal_progress)
    
    # Grafik oluşturuldu mu kontrol et
    assert chart is not None 