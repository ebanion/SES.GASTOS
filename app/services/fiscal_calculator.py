"""
Calculadora fiscal para España
Estimación de IVA, IRPF, IS y alertas fiscales automáticas
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models import Expense, Income, Reservation, Apartment


class FiscalCalculator:
    """Calculadora de impuestos española para alquileres turísticos"""
    
    # Tipos impositivos estándar (pueden configurarse por cuenta)
    IVA_RATE = Decimal('0.10')  # 10% para alojamiento turístico
    IRPF_RATE = Decimal('0.20')  # Estimación general 20% (varía por tramo)
    IS_RATE = Decimal('0.25')  # 25% Impuesto sobre Sociedades
    
    # Umbrales importantes
    AUTONOMO_THRESHOLD = Decimal('1000.00')  # €1000/mes recomendado darse de alta
    IVA_EXEMPTION_THRESHOLD = Decimal('12450.00')  # Límite anual para estar exento
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CALCULADORA IVA ====================
    
    def calculate_quarterly_iva(
        self,
        account_id: str,
        year: int,
        quarter: int
    ) -> Dict:
        """
        Calcula IVA trimestral (Modelo 303)
        Quarter: 1 (ene-mar), 2 (abr-jun), 3 (jul-sep), 4 (oct-dic)
        """
        start_date, end_date = self._get_quarter_dates(year, quarter)
        
        # IVA repercutido (cobrado a clientes)
        total_income = self._get_total_income(account_id, start_date, end_date)
        iva_repercutido = total_income * self.IVA_RATE
        
        # IVA soportado (pagado en gastos deducibles)
        total_expenses_with_iva = self._get_deductible_expenses(account_id, start_date, end_date)
        iva_soportado = total_expenses_with_iva * (self.IVA_RATE / Decimal('1.10'))  # Extraer IVA incluido
        
        # IVA a ingresar (o devolver si es negativo)
        iva_to_pay = iva_repercutido - iva_soportado
        
        # Vencimiento del trimestre
        due_date = self._get_iva_due_date(year, quarter)
        days_until_due = (due_date - date.today()).days
        
        return {
            "year": year,
            "quarter": quarter,
            "quarter_label": f"Q{quarter} {year}",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_income": float(total_income),
            "total_expenses": float(total_expenses_with_iva),
            "iva_repercutido": float(iva_repercutido),
            "iva_soportado": float(iva_soportado),
            "iva_to_pay": float(iva_to_pay),
            "iva_rate_percent": float(self.IVA_RATE * 100),
            "due_date": due_date.isoformat(),
            "days_until_due": days_until_due,
            "is_overdue": days_until_due < 0,
            "status": "pending" if days_until_due > 0 else "overdue"
        }
    
    def _get_quarter_dates(self, year: int, quarter: int) -> tuple:
        """Obtiene fechas inicio/fin de un trimestre"""
        quarters = {
            1: (date(year, 1, 1), date(year, 3, 31)),
            2: (date(year, 4, 1), date(year, 6, 30)),
            3: (date(year, 7, 1), date(year, 9, 30)),
            4: (date(year, 10, 1), date(year, 12, 31))
        }
        return quarters[quarter]
    
    def _get_iva_due_date(self, year: int, quarter: int) -> date:
        """Fecha límite presentación Modelo 303"""
        # 20 del mes siguiente al trimestre
        due_dates = {
            1: date(year, 4, 20),
            2: date(year, 7, 20),
            3: date(year, 10, 20),
            4: date(year + 1, 1, 20)
        }
        return due_dates[quarter]
    
    # ==================== CALCULADORA IRPF ====================
    
    def calculate_quarterly_irpf(
        self,
        account_id: str,
        year: int,
        quarter: int,
        regime: Literal["general", "modules"] = "general"
    ) -> Dict:
        """
        Calcula IRPF trimestral (Modelo 130 para autónomos)
        Régimen general o estimación directa simplificada
        """
        start_date, end_date = self._get_quarter_dates(year, quarter)
        
        # Ingresos y gastos del trimestre
        total_income = self._get_total_income(account_id, start_date, end_date)
        total_expenses = self._get_deductible_expenses(account_id, start_date, end_date)
        
        # Rendimiento neto
        net_income = total_income - total_expenses
        
        if regime == "general":
            # Régimen general: 20% del rendimiento neto
            irpf_base = net_income
            irpf_to_pay = irpf_base * self.IRPF_RATE
            
        else:  # modules
            # Módulos: Aplica coeficientes (simplificado)
            # Real sería más complejo con signos, índices, etc.
            irpf_base = total_income * Decimal('0.30')  # 30% rendimiento neto estimado
            irpf_to_pay = irpf_base * self.IRPF_RATE
        
        # Pagos a cuenta previos (acumulado del año)
        previous_payments = self._get_previous_irpf_payments(account_id, year, quarter)
        
        # Pago fraccionado del trimestre
        quarterly_payment = irpf_to_pay - previous_payments
        
        # Vencimiento
        due_date = self._get_irpf_due_date(year, quarter)
        days_until_due = (due_date - date.today()).days
        
        return {
            "year": year,
            "quarter": quarter,
            "quarter_label": f"Q{quarter} {year}",
            "regime": regime,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_income": float(net_income),
            "irpf_base": float(irpf_base),
            "irpf_rate_percent": float(self.IRPF_RATE * 100),
            "irpf_calculated": float(irpf_to_pay),
            "previous_payments": float(previous_payments),
            "quarterly_payment": float(quarterly_payment),
            "due_date": due_date.isoformat(),
            "days_until_due": days_until_due,
            "is_overdue": days_until_due < 0
        }
    
    def _get_irpf_due_date(self, year: int, quarter: int) -> date:
        """Fecha límite presentación Modelo 130"""
        # 20 del mes siguiente al trimestre
        due_dates = {
            1: date(year, 4, 20),
            2: date(year, 7, 20),
            3: date(year, 10, 20),
            4: date(year + 1, 1, 20)
        }
        return due_dates[quarter]
    
    def _get_previous_irpf_payments(
        self,
        account_id: str,
        year: int,
        current_quarter: int
    ) -> Decimal:
        """Suma de pagos fraccionados previos en el año"""
        # En producción, esto debería consultar una tabla de pagos realizados
        # Por ahora devuelve 0
        return Decimal('0.00')
    
    # ==================== ALERTAS FISCALES ====================
    
    def get_fiscal_alerts(
        self,
        account_id: str
    ) -> List[Dict]:
        """
        Genera lista de alertas fiscales proactivas
        """
        alerts = []
        today = date.today()
        current_quarter = (today.month - 1) // 3 + 1
        current_year = today.year
        
        # 1. Alerta de vencimientos próximos (próximos 15 días)
        iva_due = self._get_iva_due_date(current_year, current_quarter)
        irpf_due = self._get_irpf_due_date(current_year, current_quarter)
        
        if 0 <= (iva_due - today).days <= 15:
            alerts.append({
                "type": "deadline",
                "severity": "warning",
                "title": f"Vence declaración IVA Q{current_quarter}",
                "message": f"En {(iva_due - today).days} días vence el Modelo 303 (IVA trimestral)",
                "due_date": iva_due.isoformat(),
                "action_url": "/fiscal/iva-calculator",
                "icon": "📊"
            })
        
        if 0 <= (irpf_due - today).days <= 15:
            alerts.append({
                "type": "deadline",
                "severity": "warning",
                "title": f"Vence pago fraccionado IRPF Q{current_quarter}",
                "message": f"En {(irpf_due - today).days} días vence el Modelo 130",
                "due_date": irpf_due.isoformat(),
                "action_url": "/fiscal/irpf-calculator",
                "icon": "💰"
            })
        
        # 2. Alerta si se supera umbral de facturación
        year_to_date_income = self._get_total_income(
            account_id,
            date(current_year, 1, 1),
            today
        )
        
        if year_to_date_income > self.IVA_EXEMPTION_THRESHOLD:
            alerts.append({
                "type": "threshold",
                "severity": "info",
                "title": "Umbral IVA superado",
                "message": f"Has superado €{float(self.IVA_EXEMPTION_THRESHOLD):,.0f} de facturación anual. Verifica si debes declarar IVA.",
                "amount": float(year_to_date_income),
                "threshold": float(self.IVA_EXEMPTION_THRESHOLD),
                "icon": "🚨"
            })
        
        # 3. Alerta de gastos sin categorizar (afectan deducciones)
        uncategorized_expenses = self.db.query(func.count(Expense.id)).join(Apartment).filter(
            Apartment.account_id == account_id,
            Expense.category.is_(None),
            Expense.date >= date(current_year, 1, 1)
        ).scalar()
        
        if uncategorized_expenses > 5:
            alerts.append({
                "type": "data_quality",
                "severity": "warning",
                "title": "Gastos sin categorizar",
                "message": f"Tienes {uncategorized_expenses} gastos sin categoría. Esto afecta tus deducciones fiscales.",
                "count": uncategorized_expenses,
                "action_url": "/expenses?filter=uncategorized",
                "icon": "📝"
            })
        
        # 4. Recordatorio cierre fiscal anual (noviembre-diciembre)
        if today.month >= 11:
            days_to_year_end = (date(current_year, 12, 31) - today).days
            alerts.append({
                "type": "planning",
                "severity": "info",
                "title": "Preparación cierre fiscal",
                "message": f"Quedan {days_to_year_end} días para el cierre fiscal. Revisa deducciones pendientes.",
                "icon": "📅"
            })
        
        # 5. Sugerencia de optimización fiscal
        quarter_income = self._get_total_income(
            account_id,
            *self._get_quarter_dates(current_year, current_quarter)
        )
        
        if quarter_income > Decimal('3000.00'):  # Si factura >3k/trimestre
            alerts.append({
                "type": "optimization",
                "severity": "success",
                "title": "Oportunidad: Revisa régimen fiscal",
                "message": "Con tu volumen de facturación, podría convenir optimizar tu régimen fiscal. Consulta con un asesor.",
                "icon": "💡"
            })
        
        return alerts
    
    # ==================== SIMULADOR FISCAL ====================
    
    def simulate_tax_scenarios(
        self,
        account_id: str,
        projected_annual_income: Decimal,
        projected_annual_expenses: Decimal
    ) -> Dict:
        """
        Simula cuánto se pagaría en impuestos bajo diferentes escenarios
        """
        net_income = projected_annual_income - projected_annual_expenses
        
        # Escenario 1: Autónomo en régimen general
        autonomo_irpf = net_income * self.IRPF_RATE
        autonomo_iva = projected_annual_income * self.IVA_RATE - projected_annual_expenses * (self.IVA_RATE / Decimal('1.10'))
        autonomo_ss = Decimal('3600.00')  # Cuota autónomo estimada anual (~€300/mes)
        autonomo_total = autonomo_irpf + autonomo_iva + autonomo_ss
        
        # Escenario 2: Sociedad (SL)
        sl_is = net_income * self.IS_RATE  # Impuesto sociedades 25%
        sl_iva = projected_annual_income * self.IVA_RATE - projected_annual_expenses * (self.IVA_RATE / Decimal('1.10'))
        sl_admin_costs = Decimal('2000.00')  # Gestoría, contabilidad
        sl_total = sl_is + sl_iva + sl_admin_costs
        
        # Escenario 3: Módulos (estimación objetiva)
        modules_base = projected_annual_income * Decimal('0.30')  # 30% rendimiento neto estimado
        modules_irpf = modules_base * self.IRPF_RATE
        modules_iva = projected_annual_income * Decimal('0.01')  # IVA simplificado
        modules_ss = Decimal('3600.00')
        modules_total = modules_irpf + modules_iva + modules_ss
        
        return {
            "projected_annual_income": float(projected_annual_income),
            "projected_annual_expenses": float(projected_annual_expenses),
            "projected_net_income": float(net_income),
            "scenarios": {
                "autonomo_general": {
                    "name": "Autónomo Régimen General",
                    "irpf": float(autonomo_irpf),
                    "iva": float(autonomo_iva),
                    "social_security": float(autonomo_ss),
                    "total_tax": float(autonomo_total),
                    "net_after_tax": float(net_income - autonomo_total),
                    "effective_rate": float((autonomo_total / projected_annual_income) * 100) if projected_annual_income > 0 else 0,
                    "recommended": net_income < Decimal('40000.00')  # Recomendado hasta 40k
                },
                "sociedad_limitada": {
                    "name": "Sociedad Limitada (SL)",
                    "is": float(sl_is),
                    "iva": float(sl_iva),
                    "admin_costs": float(sl_admin_costs),
                    "total_tax": float(sl_total),
                    "net_after_tax": float(net_income - sl_total),
                    "effective_rate": float((sl_total / projected_annual_income) * 100) if projected_annual_income > 0 else 0,
                    "recommended": net_income > Decimal('40000.00')  # Recomendado desde 40k
                },
                "modulos": {
                    "name": "Módulos (Estimación Objetiva)",
                    "irpf": float(modules_irpf),
                    "iva": float(modules_iva),
                    "social_security": float(modules_ss),
                    "total_tax": float(modules_total),
                    "net_after_tax": float(net_income - modules_total),
                    "effective_rate": float((modules_total / projected_annual_income) * 100) if projected_annual_income > 0 else 0,
                    "recommended": False,  # Rara vez recomendado para alquileres turísticos
                    "note": "Requisitos específicos, no siempre aplicable"
                }
            },
            "recommendation": self._get_regime_recommendation(net_income)
        }
    
    def _get_regime_recommendation(self, net_income: Decimal) -> str:
        """Recomienda régimen fiscal según beneficio neto"""
        if net_income < Decimal('15000.00'):
            return "Régimen general de autónomo es suficiente. Mantén gastos documentados."
        elif net_income < Decimal('40000.00'):
            return "Régimen general óptimo. Considera SL si planeas crecer significativamente."
        else:
            return "Sociedad Limitada (SL) podría ser más ventajosa. Consulta con asesor fiscal."
    
    # ==================== HELPERS ====================
    
    def _get_total_income(self, account_id: str, start_date: date, end_date: date) -> Decimal:
        """Total ingresos en un periodo"""
        total = self.db.query(
            func.sum(Income.amount_gross)
        ).join(Reservation).join(Apartment).filter(
            Apartment.account_id == account_id,
            Income.date >= start_date,
            Income.date <= end_date
        ).scalar()
        
        return total or Decimal('0.00')
    
    def _get_deductible_expenses(self, account_id: str, start_date: date, end_date: date) -> Decimal:
        """Total gastos deducibles en un periodo"""
        # En producción, filtrar por gastos marcados como deducibles
        total = self.db.query(
            func.sum(Expense.amount_gross)
        ).join(Apartment).filter(
            Apartment.account_id == account_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).scalar()
        
        return total or Decimal('0.00')
