# app/services/reservation_scheduler.py
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.orm import Session
from ..db import get_db
from ..services.email_reservation_processor import EmailReservationProcessor
from .. import models


class ReservationScheduler:
    """
    Servicio para tareas programadas relacionadas con reservas:
    - Confirmar reservas pendientes cuyo período de cancelación ha expirado
    - Limpiar datos antiguos
    - Generar reportes automáticos
    """
    
    def __init__(self):
        self.db = next(get_db())
    
    async def run_daily_tasks(self):
        """Ejecuta tareas diarias"""
        
        tasks = [
            self.confirm_expired_pending_reservations(),
            self.cleanup_old_processed_emails(),
            self.generate_daily_report()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "tasks_completed": len([r for r in results if not isinstance(r, Exception)]),
            "tasks_failed": len([r for r in results if isinstance(r, Exception)]),
            "results": results
        }
    
    async def confirm_expired_pending_reservations(self) -> Dict:
        """Confirma reservas pendientes cuyo período de cancelación ha expirado"""
        
        try:
            processor = EmailReservationProcessor(self.db)
            results = processor.check_pending_reservations()
            
            return {
                "task": "confirm_expired_pending_reservations",
                "success": True,
                "confirmed_reservations": len(results),
                "details": results
            }
            
        except Exception as e:
            return {
                "task": "confirm_expired_pending_reservations",
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_old_processed_emails(self) -> Dict:
        """Limpia registros de emails procesados antiguos (más de 6 meses)"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=180)  # 6 meses
            
            # Mantener solo los últimos 6 meses de emails procesados
            old_incomes = self.db.query(models.Income).filter(
                models.Income.processed_from_email == True,
                models.Income.created_at < cutoff_date,
                models.Income.status == "CANCELLED"  # Solo limpiar cancelados antiguos
            ).all()
            
            deleted_count = len(old_incomes)
            
            for income in old_incomes:
                self.db.delete(income)
            
            self.db.commit()
            
            return {
                "task": "cleanup_old_processed_emails",
                "success": True,
                "deleted_records": deleted_count,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "task": "cleanup_old_processed_emails",
                "success": False,
                "error": str(e)
            }
    
    async def generate_daily_report(self) -> Dict:
        """Genera reporte diario de actividad de reservas"""
        
        try:
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Estadísticas del día anterior
            daily_incomes = self.db.query(models.Income).filter(
                models.Income.processed_from_email == True,
                models.Income.created_at >= yesterday,
                models.Income.created_at < today
            ).all()
            
            stats = {
                "total_reservations": len(daily_incomes),
                "confirmed_reservations": len([i for i in daily_incomes if i.status == "CONFIRMED"]),
                "pending_reservations": len([i for i in daily_incomes if i.status == "PENDING"]),
                "cancelled_reservations": len([i for i in daily_incomes if i.status == "CANCELLED"]),
                "total_amount": sum(float(i.amount_gross) for i in daily_incomes if i.status != "CANCELLED"),
                "by_source": {}
            }
            
            # Estadísticas por fuente
            for source in ["BOOKING", "AIRBNB", "WEB"]:
                source_incomes = [i for i in daily_incomes if i.source == source]
                stats["by_source"][source] = {
                    "count": len(source_incomes),
                    "amount": sum(float(i.amount_gross) for i in source_incomes if i.status != "CANCELLED")
                }
            
            return {
                "task": "generate_daily_report",
                "success": True,
                "date": yesterday.isoformat(),
                "statistics": stats
            }
            
        except Exception as e:
            return {
                "task": "generate_daily_report",
                "success": False,
                "error": str(e)
            }
    
    async def check_upcoming_checkins(self) -> Dict:
        """Verifica check-ins próximos (para notificaciones)"""
        
        try:
            tomorrow = datetime.now().date() + timedelta(days=1)
            next_week = datetime.now().date() + timedelta(days=7)
            
            upcoming_checkins = self.db.query(models.Income).filter(
                models.Income.check_in_date >= tomorrow,
                models.Income.check_in_date <= next_week,
                models.Income.status == "CONFIRMED"
            ).all()
            
            checkins_by_day = {}
            
            for income in upcoming_checkins:
                day_key = income.check_in_date.isoformat()
                if day_key not in checkins_by_day:
                    checkins_by_day[day_key] = []
                
                checkins_by_day[day_key].append({
                    "apartment_code": income.apartment.code if income.apartment else "N/A",
                    "guest_name": income.guest_name,
                    "booking_reference": income.booking_reference,
                    "guests_count": income.guests_count,
                    "source": income.source
                })
            
            return {
                "task": "check_upcoming_checkins",
                "success": True,
                "upcoming_checkins": checkins_by_day,
                "total_checkins": len(upcoming_checkins)
            }
            
        except Exception as e:
            return {
                "task": "check_upcoming_checkins",
                "success": False,
                "error": str(e)
            }


# Función para ejecutar desde cron job o scheduler
async def run_scheduled_tasks():
    """
    Función principal para ejecutar desde un scheduler externo
    """
    scheduler = ReservationScheduler()
    return await scheduler.run_daily_tasks()


# Para testing manual
if __name__ == "__main__":
    import asyncio
    
    async def test_scheduler():
        result = await run_scheduled_tasks()
        print("Scheduler result:", result)
    
    asyncio.run(test_scheduler())