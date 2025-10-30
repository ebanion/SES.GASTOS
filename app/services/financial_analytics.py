"""
Servicio de análisis financiero avanzado
Calcula KPIs hoteleros, salud financiera, predicciones y recomendaciones
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
import calendar

from ..models import Expense, Income, Reservation, Apartment


class FinancialAnalytics:
    """Servicio de análisis financiero y KPIs hoteleros"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== KPIs HOTELEROS ====================
    
    def calculate_adr(
        self, 
        account_id: str, 
        apartment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        ADR (Average Daily Rate): Ingreso medio por noche ocupada
        Fórmula: Total ingresos / Total noches ocupadas
        """
        query = self.db.query(
            func.sum(Income.amount_gross_gross).label('total_income'),
            func.count(Reservation.id).label('total_reservations')
        ).join(
            Reservation, Income.reservation_id == Reservation.id
        ).join(
            Apartment, Reservation.apartment_id == Apartment.id
        ).filter(
            Apartment.account_id == account_id
        )
        
        if apartment_id:
            query = query.filter(Reservation.apartment_id == apartment_id)
        
        if start_date and end_date:
            query = query.filter(
                and_(
                    Income.date >= start_date,
                    Income.date <= end_date
                )
            )
        
        result = query.first()
        
        if not result or not result.total_income or not result.total_reservations:
            return Decimal('0.00')
        
        # Calcular noches totales
        reservations = self.db.query(Reservation).join(Apartment).filter(
            Apartment.account_id == account_id
        )
        
        if apartment_id:
            reservations = reservations.filter(Reservation.apartment_id == apartment_id)
        
        if start_date and end_date:
            reservations = reservations.filter(
                Reservation.check_in >= start_date,
                Reservation.check_out <= end_date
            )
        
        total_nights = sum(
            (r.check_out - r.check_in).days 
            for r in reservations.all()
        )
        
        if total_nights == 0:
            return Decimal('0.00')
        
        adr = Decimal(str(result.total_income)) / Decimal(str(total_nights))
        return adr.quantize(Decimal('0.01'))
    
    def calculate_occupancy_rate(
        self,
        account_id: str,
        apartment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        Tasa de ocupación: % de noches ocupadas sobre disponibles
        Fórmula: (Noches ocupadas / Noches disponibles) * 100
        """
        if not start_date or not end_date:
            # Por defecto mes actual
            today = date.today()
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        
        # Calcular noches disponibles
        days_in_period = (end_date - start_date).days + 1
        
        apartments_query = self.db.query(Apartment).filter(
            Apartment.account_id == account_id,
            Apartment.is_active == True
        )
        
        if apartment_id:
            apartments_query = apartments_query.filter(Apartment.id == apartment_id)
        
        num_apartments = apartments_query.count()
        
        if num_apartments == 0:
            return Decimal('0.00')
        
        available_nights = days_in_period * num_apartments
        
        # Calcular noches ocupadas
        reservations = self.db.query(Reservation).join(Apartment).filter(
            Apartment.account_id == account_id,
            Reservation.status == 'CONFIRMED'
        )
        
        if apartment_id:
            reservations = reservations.filter(Reservation.apartment_id == apartment_id)
        
        reservations = reservations.filter(
            Reservation.check_out > start_date,
            Reservation.check_in < end_date
        )
        
        occupied_nights = 0
        for reservation in reservations.all():
            # Calcular solapamiento con el periodo
            overlap_start = max(reservation.check_in, start_date)
            overlap_end = min(reservation.check_out, end_date)
            
            if overlap_start < overlap_end:
                occupied_nights += (overlap_end - overlap_start).days
        
        if available_nights == 0:
            return Decimal('0.00')
        
        occupancy_rate = (Decimal(str(occupied_nights)) / Decimal(str(available_nights))) * 100
        return occupancy_rate.quantize(Decimal('0.01'))
    
    def calculate_revpar(
        self,
        account_id: str,
        apartment_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        RevPAR (Revenue Per Available Room): Ingreso por habitación disponible
        Fórmula: Total ingresos / Total noches disponibles
        O bien: ADR × Tasa de ocupación
        """
        if not start_date or not end_date:
            today = date.today()
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
        
        # Calcular ingresos totales
        income_query = self.db.query(
            func.sum(Income.amount_gross).label('total')
        ).join(
            Reservation, Income.reservation_id == Reservation.id
        ).join(
            Apartment, Reservation.apartment_id == Apartment.id
        ).filter(
            Apartment.account_id == account_id,
            Income.date >= start_date,
            Income.date <= end_date
        )
        
        if apartment_id:
            income_query = income_query.filter(Apartment.id == apartment_id)
        
        total_income = income_query.scalar() or Decimal('0.00')
        
        # Calcular noches disponibles
        days_in_period = (end_date - start_date).days + 1
        
        apartments_query = self.db.query(Apartment).filter(
            Apartment.account_id == account_id,
            Apartment.is_active == True
        )
        
        if apartment_id:
            apartments_query = apartments_query.filter(Apartment.id == apartment_id)
        
        num_apartments = apartments_query.count()
        available_nights = days_in_period * num_apartments
        
        if available_nights == 0:
            return Decimal('0.00')
        
        revpar = Decimal(str(total_income)) / Decimal(str(available_nights))
        return revpar.quantize(Decimal('0.01'))
    
    # ==================== SALUD FINANCIERA ====================
    
    def calculate_financial_health(
        self,
        account_id: str,
        period_months: int = 1
    ) -> Dict:
        """
        Calcula el estado de salud financiera (Verde/Amarillo/Rojo)
        Basado en margen, ocupación y tendencia de gastos
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=30 * period_months)
        
        # 1. Calcular ingresos y gastos
        total_income = self.db.query(
            func.sum(Income.amount_gross)
        ).join(Reservation).join(Apartment).filter(
            Apartment.account_id == account_id,
            Income.date >= start_date,
            Income.date <= end_date
        ).scalar() or Decimal('0.00')
        
        total_expenses = self.db.query(
            func.sum(Expense.amount_gross)
        ).join(Apartment).filter(
            Apartment.account_id == account_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).scalar() or Decimal('0.00')
        
        # 2. Calcular margen
        if total_income > 0:
            margin_percent = ((total_income - total_expenses) / total_income) * 100
        else:
            margin_percent = Decimal('0.00')
        
        # 3. Calcular ocupación
        occupancy_rate = self.calculate_occupancy_rate(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # 4. Ratio de gastos sobre ingresos
        if total_income > 0:
            expense_ratio = (total_expenses / total_income) * 100
        else:
            expense_ratio = Decimal('100.00')
        
        # 5. Determinar estado (semáforo)
        status = self._determine_health_status(
            margin_percent=margin_percent,
            occupancy_rate=occupancy_rate,
            expense_ratio=expense_ratio
        )
        
        # 6. Generar mensaje explicativo
        message = self._generate_health_message(
            status=status,
            margin_percent=margin_percent,
            occupancy_rate=occupancy_rate,
            expense_ratio=expense_ratio
        )
        
        return {
            "status": status,  # "green", "yellow", "red"
            "score": self._calculate_health_score(margin_percent, occupancy_rate, expense_ratio),
            "margin_percent": float(margin_percent),
            "occupancy_rate": float(occupancy_rate),
            "expense_ratio": float(expense_ratio),
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_profit": float(total_income - total_expenses),
            "message": message,
            "period_days": (end_date - start_date).days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    def _determine_health_status(
        self,
        margin_percent: Decimal,
        occupancy_rate: Decimal,
        expense_ratio: Decimal
    ) -> Literal["green", "yellow", "red"]:
        """Determina el color del semáforo basado en métricas"""
        
        # Verde: Excelente salud
        if (margin_percent >= 25 and 
            occupancy_rate >= 70 and 
            expense_ratio <= 60):
            return "green"
        
        # Rojo: Salud crítica
        if (margin_percent < 10 or 
            occupancy_rate < 40 or 
            expense_ratio > 85):
            return "red"
        
        # Amarillo: Salud moderada
        return "yellow"
    
    def _calculate_health_score(
        self,
        margin_percent: Decimal,
        occupancy_rate: Decimal,
        expense_ratio: Decimal
    ) -> int:
        """Calcula un score de 0-100 de salud financiera"""
        
        # Pesos: margen 40%, ocupación 35%, control de gastos 25%
        margin_score = min(float(margin_percent) * 2, 100) * 0.40
        occupancy_score = min(float(occupancy_rate) * 1.2, 100) * 0.35
        expense_score = max(100 - float(expense_ratio), 0) * 0.25
        
        total_score = margin_score + occupancy_score + expense_score
        return int(total_score)
    
    def _generate_health_message(
        self,
        status: str,
        margin_percent: Decimal,
        occupancy_rate: Decimal,
        expense_ratio: Decimal
    ) -> str:
        """Genera mensaje explicativo del estado"""
        
        if status == "green":
            return f"🎉 Excelente rentabilidad: Margen del {margin_percent:.1f}% con {occupancy_rate:.0f}% de ocupación. Gastos controlados al {expense_ratio:.0f}% de ingresos."
        
        elif status == "yellow":
            issues = []
            if margin_percent < 20:
                issues.append("margen ajustado")
            if occupancy_rate < 60:
                issues.append("ocupación mejorable")
            if expense_ratio > 70:
                issues.append("gastos elevados")
            
            return f"⚠️ Rentabilidad moderada: {', '.join(issues)}. Margen {margin_percent:.1f}%, ocupación {occupancy_rate:.0f}%."
        
        else:  # red
            critical = []
            if margin_percent < 10:
                critical.append("⚠️ margen crítico")
            if occupancy_rate < 40:
                critical.append("⚠️ ocupación baja")
            if expense_ratio > 85:
                critical.append("⚠️ gastos descontrolados")
            
            return f"🚨 Atención requerida: {', '.join(critical)}. Revisa estrategia de precios y costes."
    
    # ==================== COMPARATIVA AÑO ANTERIOR ====================
    
    def compare_year_over_year(
        self,
        account_id: str,
        current_start: date,
        current_end: date
    ) -> Dict:
        """
        Compara métricas del periodo actual con el mismo periodo del año anterior
        """
        # Calcular periodo anterior (mismo periodo año pasado)
        previous_start = current_start.replace(year=current_start.year - 1)
        previous_end = current_end.replace(year=current_end.year - 1)
        
        # Métricas actuales
        current_income = self._get_total_income(account_id, current_start, current_end)
        current_expenses = self._get_total_expenses(account_id, current_start, current_end)
        current_profit = current_income - current_expenses
        current_occupancy = self.calculate_occupancy_rate(
            account_id, None, current_start, current_end
        )
        current_adr = self.calculate_adr(account_id, None, current_start, current_end)
        
        # Métricas año anterior
        previous_income = self._get_total_income(account_id, previous_start, previous_end)
        previous_expenses = self._get_total_expenses(account_id, previous_start, previous_end)
        previous_profit = previous_income - previous_expenses
        previous_occupancy = self.calculate_occupancy_rate(
            account_id, None, previous_start, previous_end
        )
        previous_adr = self.calculate_adr(account_id, None, previous_start, previous_end)
        
        # Calcular variaciones
        def calc_variation(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return float(((current - previous) / previous) * 100)
        
        return {
            "current_period": {
                "start_date": current_start.isoformat(),
                "end_date": current_end.isoformat(),
                "income": float(current_income),
                "expenses": float(current_expenses),
                "profit": float(current_profit),
                "occupancy_rate": float(current_occupancy),
                "adr": float(current_adr)
            },
            "previous_period": {
                "start_date": previous_start.isoformat(),
                "end_date": previous_end.isoformat(),
                "income": float(previous_income),
                "expenses": float(previous_expenses),
                "profit": float(previous_profit),
                "occupancy_rate": float(previous_occupancy),
                "adr": float(previous_adr)
            },
            "variations": {
                "income_change_percent": calc_variation(current_income, previous_income),
                "expenses_change_percent": calc_variation(current_expenses, previous_expenses),
                "profit_change_percent": calc_variation(current_profit, previous_profit),
                "occupancy_change_percent": calc_variation(current_occupancy, previous_occupancy),
                "adr_change_percent": calc_variation(current_adr, previous_adr)
            }
        }
    
    def _get_total_income(self, account_id: str, start_date: date, end_date: date) -> Decimal:
        """Helper: Total ingresos en un periodo"""
        total = self.db.query(
            func.sum(Income.amount_gross)
        ).join(Reservation).join(Apartment).filter(
            Apartment.account_id == account_id,
            Income.date >= start_date,
            Income.date <= end_date
        ).scalar()
        
        return total or Decimal('0.00')
    
    def _get_total_expenses(self, account_id: str, start_date: date, end_date: date) -> Decimal:
        """Helper: Total gastos en un periodo"""
        total = self.db.query(
            func.sum(Expense.amount_gross)
        ).join(Apartment).filter(
            Apartment.account_id == account_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).scalar()
        
        return total or Decimal('0.00')
    
    # ==================== ANÁLISIS POR CATEGORÍA ====================
    
    def analyze_expense_categories(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict]:
        """
        Analiza gastos por categoría con % sobre ingresos y recomendaciones
        """
        if not start_date or not end_date:
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
        
        # Total ingresos del periodo
        total_income = self._get_total_income(account_id, start_date, end_date)
        
        if total_income == 0:
            return []
        
        # Gastos agrupados por categoría
        expenses_by_category = self.db.query(
            Expense.category,
            func.sum(Expense.amount_gross).label('total'),
            func.count(Expense.id).label('count')
        ).join(Apartment).filter(
            Apartment.account_id == account_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).group_by(Expense.category).all()
        
        # Benchmarks de la industria (% sobre ingresos)
        benchmarks = {
            "Limpieza": 12.0,
            "Suministros": 8.0,
            "Reparaciones": 5.0,
            "Comisiones": 15.0,
            "Marketing": 5.0,
            "Seguros": 3.0,
            "Mantenimiento": 6.0,
            "Otros": 10.0
        }
        
        results = []
        
        for category_data in expenses_by_category:
            category = category_data.category or "Sin categoría"
            total = Decimal(str(category_data.total))
            count = category_data.count
            
            # % sobre ingresos
            percent_of_income = float((total / total_income) * 100)
            
            # Comparar con benchmark
            benchmark = benchmarks.get(category, 10.0)
            status = self._get_category_status(percent_of_income, benchmark)
            recommendation = self._get_category_recommendation(
                category, percent_of_income, benchmark, status
            )
            
            results.append({
                "category": category,
                "total_amount": float(total),
                "transaction_count": count,
                "percent_of_income": round(percent_of_income, 2),
                "benchmark_percent": benchmark,
                "status": status,  # "optimal", "high", "very_high"
                "recommendation": recommendation
            })
        
        # Ordenar por monto (mayor a menor)
        results.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return results
    
    def _get_category_status(self, actual: float, benchmark: float) -> str:
        """Determina si el gasto en categoría es óptimo, alto o muy alto"""
        if actual <= benchmark * 1.1:  # Dentro del 110% del benchmark
            return "optimal"
        elif actual <= benchmark * 1.3:  # Dentro del 130%
            return "high"
        else:
            return "very_high"
    
    def _get_category_recommendation(
        self,
        category: str,
        actual: float,
        benchmark: float,
        status: str
    ) -> str:
        """Genera recomendación específica por categoría"""
        
        if status == "optimal":
            return f"✅ {category} está en niveles óptimos ({actual:.1f}% de ingresos)"
        
        diff = actual - benchmark
        
        if category == "Limpieza":
            return f"⚠️ Limpieza {diff:.1f}% por encima del benchmark. Considera reducir frecuencia o negociar con proveedor."
        elif category == "Comisiones":
            return f"💡 Comisiones altas ({actual:.1f}%). Promociona reserva directa para reducir dependencia de OTAs."
        elif category == "Suministros":
            return f"⚠️ Suministros elevados. Revisa consumos de luz/agua, considera upgrades eficientes."
        elif category == "Reparaciones":
            return f"⚠️ Reparaciones altas. Invierte en mantenimiento preventivo para reducir averías."
        else:
            return f"⚠️ {category} está {diff:.1f}% por encima del benchmark. Revisa gastos recurrentes."
