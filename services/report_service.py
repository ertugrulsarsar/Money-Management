import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from models.database import Transaction, Budget, FinancialGoal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_monthly_report(
        self, 
        user_id: int, 
        year: int, 
        month: int,
        category_filter: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        transaction_type: Optional[str] = None
    ) -> Dict:
        """Aylık finansal rapor oluşturur."""
        # Tarih aralığını belirle
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # İşlemleri filtrele
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date < end_date
        )
        
        if category_filter:
            query = query.filter(Transaction.category == category_filter)
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        
        transactions = query.all()
        
        # Özet hesapla
        summary = {
            "total_income": sum(t.amount for t in transactions if t.type == "income"),
            "total_expense": sum(t.amount for t in transactions if t.type == "expense"),
            "net_amount": sum(t.amount for t in transactions)
        }
        
        # Kategori bazlı harcamalar
        expense_by_category = {}
        for t in transactions:
            if t.type == "expense":
                if t.category not in expense_by_category:
                    expense_by_category[t.category] = 0
                expense_by_category[t.category] += t.amount
        
        # Bütçe performansı
        budgets = self.db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.start_date <= end_date,
            Budget.end_date >= start_date
        ).all()
        
        budget_performance = {}
        for budget in budgets:
            budget_transactions = [t for t in transactions if t.category == budget.category]
            spent = sum(t.amount for t in budget_transactions if t.type == "expense")
            budget_performance[budget.category] = {
                "limit": budget.amount,
                "spent": spent,
                "remaining": budget.amount - spent
            }
        
        # Hedef ilerlemesi
        goals = self.db.query(FinancialGoal).filter(
            FinancialGoal.user_id == user_id,
            FinancialGoal.deadline >= start_date
        ).all()
        
        goal_progress = []
        for goal in goals:
            goal_progress.append({
                "name": goal.name,
                "target": goal.target_amount,
                "current": goal.current_amount,
                "progress": (goal.current_amount / goal.target_amount) * 100,
                "deadline": goal.deadline,
                "priority": goal.priority
            })
        
        return {
            "summary": summary,
            "expense_by_category": expense_by_category,
            "budget_performance": budget_performance,
            "goal_progress": goal_progress,
            "transactions": transactions
        }

    def create_expense_chart(self, expense_data: Dict[str, float]) -> Optional[go.Figure]:
        """Harcama dağılımı grafiği oluşturur."""
        if not expense_data:
            return None
            
        # Toplam harcamayı hesapla
        total_expense = sum(expense_data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=list(expense_data.keys()),
            values=list(expense_data.values()),
            hole=.3,
            textinfo='label+percent+value',
            texttemplate='%{label}<br>%{percent}<br>₺%{value:,.0f}',
            hovertemplate=(
                "<b>%{label}</b><br>" +
                "Harcama: ₺%{value:,.2f}<br>" +
                "Oran: %{percent}<br>" +
                "<extra></extra>"
            )
        )])
        
        fig.update_layout(
            title={
                'text': "Harcamalarınızın Dağılımı",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            annotations=[dict(
                text=f"Toplam Harcama: ₺{total_expense:,.2f}",
                showarrow=False,
                font=dict(size=14),
                x=0.5,
                y=-0.1
            )]
        )
        
        return fig

    def create_budget_chart(self, budget_data: Dict) -> Optional[go.Figure]:
        """Bütçe performans grafiği oluşturur."""
        if not budget_data:
            return None
            
        categories = list(budget_data.keys())
        limits = [data["limit"] for data in budget_data.values()]
        spent = [data["spent"] for data in budget_data.values()]
        
        fig = go.Figure()
        
        # Limit çubukları
        fig.add_trace(go.Bar(
            name="Bütçe Limiti",
            x=categories,
            y=limits,
            marker_color="#1f77b4",
            text=limits,
            texttemplate='₺%{text:,.0f}',
            textposition='auto',
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Bütçe Limiti: ₺%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Harcanan çubukları
        fig.add_trace(go.Bar(
            name="Harcanan",
            x=categories,
            y=spent,
            marker_color="#ff7f0e",
            text=spent,
            texttemplate='₺%{text:,.0f}',
            textposition='auto',
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Harcanan: ₺%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        fig.update_layout(
            title={
                'text': "Bütçe Durumunuz",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            barmode="group",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis_title="Miktar (₺)",
            xaxis_title="Kategori"
        )
        
        return fig

    def create_goal_chart(self, goal_progress: List[Dict]) -> go.Figure:
        """Hedef ilerleme grafiği oluşturur."""
        if not goal_progress:
            return None
            
        # Hedefleri önceliğe göre sırala
        goal_progress.sort(key=lambda x: x["priority"])
        
        # Grafik oluştur
        fig = go.Figure()
        
        # Her hedef için çubuk ekle
        for goal in goal_progress:
            progress = (goal["current"] / goal["target"]) * 100
            color = {
                "high": "#ff4444",
                "medium": "#ffbb33",
                "low": "#00C851"
            }.get(goal["priority"], "#4285f4")
            
            fig.add_trace(go.Bar(
                name=goal["name"],
                x=[goal["name"]],
                y=[progress],
                text=[f"%{progress:.1f}"],
                textposition="auto",
                marker_color=color,
                hovertemplate=(
                    f"<b>{goal['name']}</b><br>" +
                    f"Mevcut: ₺{goal['current']:,.2f}<br>" +
                    f"Hedef: ₺{goal['target']:,.2f}<br>" +
                    f"İlerleme: %{progress:.1f}<br>" +
                    f"Son Tarih: {goal['deadline'].strftime('%d.%m.%Y')}<br>" +
                    f"Öncelik: {goal['priority']}<br>" +
                    "<extra></extra>"
                )
            ))
        
        # Grafik ayarları
        fig.update_layout(
            title={
                'text': "Hedeflerinize Ulaşma Durumunuz",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            yaxis_title="İlerleme (%)",
            showlegend=False,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        return fig

    def export_to_excel(
        self, 
        report_data: Dict, 
        filename: str,
        include_transactions: bool = True,
        include_budgets: bool = True,
        include_goals: bool = True
    ) -> None:
        """Raporu Excel dosyasına aktarır."""
        with pd.ExcelWriter(filename) as writer:
            # Özet sayfası
            summary_df = pd.DataFrame([report_data["summary"]])
            summary_df.to_excel(writer, sheet_name="Özet", index=False)
            
            # İşlemler sayfası
            if include_transactions and report_data.get("transactions"):
                transactions_df = pd.DataFrame([{
                    "Tarih": t.date,
                    "Tip": t.type,
                    "Kategori": t.category,
                    "Miktar": t.amount,
                    "Açıklama": t.description
                } for t in report_data["transactions"]])
                transactions_df.to_excel(writer, sheet_name="İşlemler", index=False)
            
            # Bütçe sayfası
            if include_budgets and report_data.get("budget_performance"):
                budget_data = []
                for category, data in report_data["budget_performance"].items():
                    budget_data.append({
                        "Kategori": category,
                        "Limit": data["limit"],
                        "Harcanan": data["spent"],
                        "Kalan": data["remaining"]
                    })
                budget_df = pd.DataFrame(budget_data)
                budget_df.to_excel(writer, sheet_name="Bütçe", index=False)
            
            # Hedefler sayfası
            if include_goals and report_data.get("goal_progress"):
                goals_df = pd.DataFrame(report_data["goal_progress"])
                goals_df.to_excel(writer, sheet_name="Hedefler", index=False)
            
            # Kategori bazlı harcamalar sayfası
            if report_data.get("expense_by_category"):
                expense_df = pd.DataFrame(
                    list(report_data["expense_by_category"].items()),
                    columns=["Kategori", "Miktar"]
                )
                expense_df.to_excel(writer, sheet_name="Kategori Harcamaları", index=False) 