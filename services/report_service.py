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
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        
        summary = {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_amount": total_income - total_expense
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
        
        # Lists oluştur, tuple kullanmayı engelle
        labels = list(expense_data.keys())
        values = list(expense_data.values())
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
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
            
        # Lists oluştur, tuple kullanmayı engelle
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

    def generate_comparative_analysis(
        self, 
        user_id: int, 
        current_year: int, 
        current_month: int,
        comparison_type: str = "previous_month"
    ) -> Dict:
        """
        İki dönem arasında karşılaştırmalı analiz yapar.
        
        Args:
            user_id: Kullanıcı ID'si
            current_year: Mevcut yıl
            current_month: Mevcut ay
            comparison_type: Karşılaştırma tipi ("previous_month", "previous_year", "custom")
            
        Returns:
            Karşılaştırmalı analiz sonuçları
        """
        # Mevcut dönem için tarih aralığını belirle
        current_start_date = date(current_year, current_month, 1)
        if current_month == 12:
            current_end_date = date(current_year + 1, 1, 1) - timedelta(days=1)
        else:
            current_end_date = date(current_year, current_month + 1, 1) - timedelta(days=1)
        
        # Karşılaştırma dönemini belirle
        if comparison_type == "previous_month":
            if current_month == 1:
                previous_year = current_year - 1
                previous_month = 12
            else:
                previous_year = current_year
                previous_month = current_month - 1
        elif comparison_type == "previous_year":
            previous_year = current_year - 1
            previous_month = current_month
        else:  # custom
            previous_year = current_year
            previous_month = current_month - 1  # varsayılan olarak bir önceki ay
        
        previous_start_date = date(previous_year, previous_month, 1)
        if previous_month == 12:
            previous_end_date = date(previous_year + 1, 1, 1) - timedelta(days=1)
        else:
            previous_end_date = date(previous_year, previous_month + 1, 1) - timedelta(days=1)
        
        # Mevcut dönem raporu
        current_report = self.generate_monthly_report(user_id, current_year, current_month)
        
        # Karşılaştırma dönemi raporu
        previous_report = self.generate_monthly_report(user_id, previous_year, previous_month)
        
        # Karşılaştırmalı analiz
        comparison = {
            "income_change": {
                "amount": current_report["summary"]["total_income"] - previous_report["summary"]["total_income"],
                "percentage": self._calculate_percentage_change(
                    previous_report["summary"]["total_income"],
                    current_report["summary"]["total_income"]
                )
            },
            "expense_change": {
                "amount": current_report["summary"]["total_expense"] - previous_report["summary"]["total_expense"],
                "percentage": self._calculate_percentage_change(
                    previous_report["summary"]["total_expense"],
                    current_report["summary"]["total_expense"]
                )
            },
            "net_amount_change": {
                "amount": current_report["summary"]["net_amount"] - previous_report["summary"]["net_amount"],
                "percentage": self._calculate_percentage_change(
                    previous_report["summary"]["net_amount"],
                    current_report["summary"]["net_amount"]
                )
            },
            "category_comparison": self._compare_categories(
                previous_report["expense_by_category"],
                current_report["expense_by_category"]
            ),
            "current_period": {
                "year": current_year,
                "month": current_month,
                "start_date": current_start_date,
                "end_date": current_end_date
            },
            "previous_period": {
                "year": previous_year,
                "month": previous_month,
                "start_date": previous_start_date,
                "end_date": previous_end_date
            }
        }
        
        return {
            "current_report": current_report,
            "previous_report": previous_report,
            "comparison": comparison
        }
    
    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """
        İki değer arasındaki yüzde değişimini hesaplar.
        """
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        
        return ((new_value - old_value) / abs(old_value)) * 100
    
    def _compare_categories(self, old_categories: Dict[str, float], new_categories: Dict[str, float]) -> Dict[str, Dict]:
        """
        Kategorilerin eski ve yeni değerlerini karşılaştırır.
        """
        all_categories = set(list(old_categories.keys()) + list(new_categories.keys()))
        comparison = {}
        
        for category in all_categories:
            old_value = old_categories.get(category, 0)
            new_value = new_categories.get(category, 0)
            
            comparison[category] = {
                "old_value": old_value,
                "new_value": new_value,
                "change": new_value - old_value,
                "percentage": self._calculate_percentage_change(old_value, new_value)
            }
        
        return comparison
        
    def create_comparison_chart(self, comparison_data: Dict) -> go.Figure:
        """
        İki dönem arasındaki karşılaştırma grafiği oluşturur.
        """
        if not comparison_data:
            return None
            
        # Kategorileri çıkar
        categories = list(comparison_data["category_comparison"].keys())
        old_values = [comparison_data["category_comparison"][cat]["old_value"] for cat in categories]
        new_values = [comparison_data["category_comparison"][cat]["new_value"] for cat in categories]
        
        # En büyük değişime göre sırala
        percentage_changes = [comparison_data["category_comparison"][cat]["percentage"] for cat in categories]
        sorted_indices = sorted(range(len(percentage_changes)), key=lambda i: abs(percentage_changes[i]), reverse=True)
        
        # Sadece en büyük 5 değişimi göster
        if len(sorted_indices) > 5:
            sorted_indices = sorted_indices[:5]
            
        categories = [categories[i] for i in sorted_indices]
        old_values = [old_values[i] for i in sorted_indices]
        new_values = [new_values[i] for i in sorted_indices]
        percentage_changes = [percentage_changes[i] for i in sorted_indices]
        
        # Grafik oluştur
        fig = go.Figure()
        
        previous_period = f"{comparison_data['previous_period']['month']}/{comparison_data['previous_period']['year']}"
        current_period = f"{comparison_data['current_period']['month']}/{comparison_data['current_period']['year']}"
        
        # Önceki dönem çubukları
        fig.add_trace(go.Bar(
            name=f"Önceki Dönem ({previous_period})",
            x=categories,
            y=old_values,
            marker_color="#6c757d",
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Önceki Dönem ({previous_period}): ₺%{{y:,.2f}}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Mevcut dönem çubukları
        fig.add_trace(go.Bar(
            name=f"Mevcut Dönem ({current_period})",
            x=categories,
            y=new_values,
            marker_color="#007bff",
            hovertemplate=(
                "<b>%{x}</b><br>" +
                f"Mevcut Dönem ({current_period}): ₺%{{y:,.2f}}<br>" +
                f"Değişim: " +
                "%{customdata:+.2f}% if %{customdata} != 0 else 'Değişim Yok'" +
                "<br>" +
                "<extra></extra>"
            ),
            customdata=percentage_changes
        ))
        
        # Grafik ayarları
        fig.update_layout(
            title={
                'text': "Kategori Bazlı Harcama Karşılaştırması",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24}
            },
            barmode='group',
            xaxis_title="Kategori",
            yaxis_title="Miktar (₺)",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=14)
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        # Yüzde değişimini ekle
        annotations = []
        for i, (cat, old_val, new_val, pct) in enumerate(zip(categories, old_values, new_values, percentage_changes)):
            if abs(pct) < 1:
                pct_text = "≈0%"
            else:
                pct_text = f"{'+' if pct > 0 else ''}{pct:.1f}%"
                
            annotations.append(dict(
                x=cat,
                y=max(old_val, new_val) + 50,
                text=pct_text,
                showarrow=False,
                font=dict(
                    size=14,
                    color="#28a745" if pct < 0 else "#dc3545" if pct > 0 else "#6c757d"
                )
            ))
        
        fig.update_layout(annotations=annotations)
        
        return fig
        
    def create_trend_chart(self, user_id: int, months: int = 6) -> go.Figure:
        """
        Son n ay için gelir/gider trendini gösteren çizgi grafiği oluşturur.
        """
        today = date.today()
        end_date = date(today.year, today.month, 1)
        
        # Son n ayın başlangıç tarihini bul
        if today.month <= months:
            start_year = today.year - 1
            start_month = 12 - (months - today.month)
        else:
            start_year = today.year
            start_month = today.month - months
            
        start_date = date(start_year, start_month, 1)
        
        # Her ay için toplam gelir ve giderleri hesapla
        monthly_data = []
        current_date = start_date
        
        while current_date < end_date:
            year = current_date.year
            month = current_date.month
            
            # Ayın son gününü hesapla
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
                
            # Bu ay için tüm işlemleri getir
            transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.date >= current_date,
                Transaction.date < next_month
            ).all()
            
            # Gelir ve giderleri hesapla
            total_income = sum(t.amount for t in transactions if t.type == "income")
            total_expense = sum(t.amount for t in transactions if t.type == "expense")
            net_amount = total_income - total_expense
            
            monthly_data.append({
                "year": year,
                "month": month,
                "date": current_date,
                "total_income": total_income,
                "total_expense": total_expense,
                "net_amount": net_amount
            })
            
            # Bir sonraki aya geç
            if month == 12:
                current_date = date(year + 1, 1, 1)
            else:
                current_date = date(year, month + 1, 1)
        
        # Grafik oluştur
        fig = go.Figure()
        
        # X ekseni için tarih etiketleri
        date_labels = [f"{d['month']}/{d['year']}" for d in monthly_data]
        
        # Gelir çizgisi
        fig.add_trace(go.Scatter(
            x=date_labels,
            y=[d["total_income"] for d in monthly_data],
            name="Gelir",
            line=dict(color="#27ae60", width=3),
            mode="lines+markers",
            marker=dict(size=8),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Gelir: ₺%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Gider çizgisi
        fig.add_trace(go.Scatter(
            x=date_labels,
            y=[d["total_expense"] for d in monthly_data],
            name="Gider",
            line=dict(color="#e74c3c", width=3),
            mode="lines+markers",
            marker=dict(size=8),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Gider: ₺%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Net durum çizgisi
        fig.add_trace(go.Scatter(
            x=date_labels,
            y=[d["net_amount"] for d in monthly_data],
            name="Net Durum",
            line=dict(color="#3498db", width=3, dash="dot"),
            mode="lines+markers",
            marker=dict(size=8),
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Net Durum: ₺%{y:,.2f}<br>" +
                "<extra></extra>"
            )
        ))
        
        # Grafik ayarları
        fig.update_layout(
            title={
                'text': "Aylık Finansal Trend",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24}
            },
            xaxis_title="Ay",
            yaxis_title="Miktar (₺)",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=14)
            ),
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=50, r=50),
            height=500
        )
        
        # X ekseni ayarları
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            tickfont=dict(size=12)
        )
        
        # Y ekseni ayarları
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.1)',
            tickfont=dict(size=12),
            tickformat="₺,"
        )
        
        return fig 