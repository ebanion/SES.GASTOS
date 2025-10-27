# app/routers/fix_incomes.py
"""
Router para arreglar la tabla de ingresos agregando columnas faltantes
"""
from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import get_db

router = APIRouter(prefix="/fix-incomes", tags=["fix_incomes"])

@router.post("/migrate-columns")
def migrate_incomes_columns(db: Session = Depends(get_db)):
    """Agregar columnas faltantes a la tabla incomes"""
    
    try:
        # SQL para agregar columnas faltantes de manera segura
        migration_sql = """
        DO $$ 
        BEGIN
            -- guest_name
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'guest_name') THEN
                ALTER TABLE incomes ADD COLUMN guest_name VARCHAR(255);
            END IF;
            
            -- guest_email  
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'guest_email') THEN
                ALTER TABLE incomes ADD COLUMN guest_email VARCHAR(255);
            END IF;
            
            -- booking_reference
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'booking_reference') THEN
                ALTER TABLE incomes ADD COLUMN booking_reference VARCHAR(100);
            END IF;
            
            -- check_in_date
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'check_in_date') THEN
                ALTER TABLE incomes ADD COLUMN check_in_date DATE;
            END IF;
            
            -- check_out_date
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'check_out_date') THEN
                ALTER TABLE incomes ADD COLUMN check_out_date DATE;
            END IF;
            
            -- guests_count
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'guests_count') THEN
                ALTER TABLE incomes ADD COLUMN guests_count INTEGER;
            END IF;
            
            -- email_message_id
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'email_message_id') THEN
                ALTER TABLE incomes ADD COLUMN email_message_id VARCHAR(255);
            END IF;
            
            -- processed_from_email
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'incomes' AND column_name = 'processed_from_email') THEN
                ALTER TABLE incomes ADD COLUMN processed_from_email BOOLEAN DEFAULT FALSE;
            END IF;
            
        END $$;
        """
        
        # Ejecutar migración
        db.execute(text(migration_sql))
        db.commit()
        
        # Verificar columnas después de la migración
        verify_sql = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'incomes' 
        ORDER BY ordinal_position;
        """
        
        result = db.execute(text(verify_sql))
        columns = result.fetchall()
        
        column_info = []
        expected_columns = [
            'guest_name', 'guest_email', 'booking_reference', 
            'check_in_date', 'check_out_date', 'guests_count', 
            'email_message_id', 'processed_from_email'
        ]
        
        existing_columns = [col[0] for col in columns]
        
        for col_name, data_type, nullable in columns:
            column_info.append(f"✅ {col_name} ({data_type})")
        
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        
        return {
            "success": True,
            "message": "✅ Migración de columnas completada",
            "total_columns": len(columns),
            "columns_info": column_info,
            "missing_columns": missing_columns,
            "migration_needed": len(missing_columns) > 0
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error en migración de columnas"
        }

@router.get("/check-columns")
def check_incomes_columns(db: Session = Depends(get_db)):
    """Verificar qué columnas existen en la tabla incomes"""
    
    try:
        # Verificar columnas existentes
        check_sql = """
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'incomes' 
        ORDER BY ordinal_position;
        """
        
        result = db.execute(text(check_sql))
        columns = result.fetchall()
        
        # Columnas esperadas según el modelo
        expected_columns = [
            'id', 'reservation_id', 'apartment_id', 'date', 'amount_gross', 
            'currency', 'status', 'non_refundable_at', 'source', 'created_at', 
            'updated_at', 'guest_name', 'guest_email', 'booking_reference', 
            'check_in_date', 'check_out_date', 'guests_count', 
            'email_message_id', 'processed_from_email'
        ]
        
        existing_columns = [col[0] for col in columns]
        missing_columns = [col for col in expected_columns if col not in existing_columns]
        
        column_details = []
        for col_name, data_type, nullable in columns:
            status = "✅" if col_name in expected_columns else "⚠️"
            column_details.append(f"{status} {col_name} ({data_type})")
        
        return {
            "success": True,
            "table_exists": len(columns) > 0,
            "total_columns": len(columns),
            "existing_columns": existing_columns,
            "missing_columns": missing_columns,
            "column_details": column_details,
            "needs_migration": len(missing_columns) > 0
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error verificando columnas"
        }

@router.post("/test-incomes")
def test_incomes_after_migration(db: Session = Depends(get_db)):
    """Probar operaciones básicas de ingresos después de migración"""
    
    try:
        # Probar consulta básica
        from .. import models
        
        # Contar ingresos existentes
        count_query = db.query(models.Income).count()
        
        # Probar crear ingreso básico
        from datetime import date
        from decimal import Decimal
        import uuid
        
        test_income = models.Income(
            apartment_id="test-apt-id",
            date=date.today(),
            amount_gross=Decimal("100.00"),
            currency="EUR",
            status="PENDING",
            source="migration_test"
        )
        
        db.add(test_income)
        db.flush()  # No commit aún
        
        # Si llegamos aquí, la estructura está bien
        db.rollback()  # Deshacer el test
        
        return {
            "success": True,
            "message": "✅ Estructura de ingresos funcional",
            "existing_incomes": count_query,
            "test_result": "Operaciones básicas funcionan correctamente"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": "❌ Error en test de ingresos",
            "suggestion": "Ejecutar /fix-incomes/migrate-columns primero"
        }

@router.get("/health")
def fix_incomes_health():
    """Health check del módulo de reparación de ingresos"""
    return {
        "status": "ok",
        "module": "fix_incomes",
        "endpoints": [
            "/fix-incomes/check-columns - Verificar columnas existentes",
            "/fix-incomes/migrate-columns - Agregar columnas faltantes", 
            "/fix-incomes/test-incomes - Probar después de migración"
        ]
    }