# app/routers/chat.py
"""
Chat integrado con IA para gestión de gastos
"""
from __future__ import annotations

import os
import tempfile
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..db import get_db
from .. import models
from ..auth_multiuser import get_current_account, require_member_or_above

# Importar utilidades del bot
try:
    from ..bot.Llm_Untils import extract_expense_json
    from ..bot.Ocr_untils import extract_text_from_image
    from ..bot.Multiuser_Utils import get_apartment_by_code
except ImportError:
    # Fallbacks si no están disponibles
    def extract_expense_json(text: str, apartment_code: str) -> dict:
        return {}
    
    def extract_text_from_image(image_path: str) -> str:
        return ""
    
    def get_apartment_by_code(user_id: int, apartment_code: str) -> Optional[dict]:
        return None

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/message")
async def chat_message(
    request_data: dict,
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Procesar mensaje de chat con IA"""
    
    message = request_data.get("message", "").strip()
    context = request_data.get("context", "dashboard")
    apartment_code = request_data.get("apartment_code")  # Apartamento seleccionado
    
    if not message:
        raise HTTPException(status_code=400, detail="Mensaje vacío")
    
    try:
        # Obtener apartamentos de la cuenta
        apartments = db.query(models.Apartment).filter(
            and_(
                models.Apartment.account_id == current_account.id,
                models.Apartment.is_active == True
            )
        ).all()
        
        if not apartments:
            return {
                "response": "❌ No tienes apartamentos registrados. Crea uno primero para poder registrar gastos.",
                "action": "no_apartments"
            }
        
        # Buscar apartamento específico si se proporciona
        selected_apartment = None
        if apartment_code:
            selected_apartment = next((apt for apt in apartments if apt.code == apartment_code), None)
        
        # Usar apartamento seleccionado o el primero como predeterminado
        default_apartment = selected_apartment or apartments[0]
        
        # Detectar tipo de mensaje
        response_data = await process_chat_message(
            message, 
            current_account, 
            default_apartment, 
            apartments, 
            db
        )
        
        return response_data
        
    except Exception as e:
        return {
            "response": f"❌ Error procesando tu mensaje: {str(e)}",
            "action": "error"
        }

@router.post("/file")
async def chat_file(
    file: UploadFile = File(...),
    apartment_code: str = Form(...),
    context: str = Form("dashboard"),
    current_account: models.Account = Depends(get_current_account),
    membership: models.AccountUser = Depends(require_member_or_above),
    db: Session = Depends(get_db)
):
    """Procesar archivo (imagen o PDF) con OCR + IA"""
    
    try:
        # Validar tipo de archivo
        is_image = file.content_type.startswith('image/')
        is_pdf = file.content_type == 'application/pdf'
        
        if not is_image and not is_pdf:
            raise HTTPException(status_code=400, detail="Solo se permiten imágenes y archivos PDF")
        
        # Buscar apartamento específico por código
        apartment = db.query(models.Apartment).filter(
            and_(
                models.Apartment.code == apartment_code,
                models.Apartment.account_id == current_account.id,
                models.Apartment.is_active == True
            )
        ).first()
        
        if not apartment:
            return {
                "response": f"❌ Apartamento '{apartment_code}' no encontrado en tu cuenta.",
                "action": "apartment_not_found"
            }
        
        # Guardar archivo temporalmente
        file_suffix = ".pdf" if is_pdf else ".jpg"
        with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file.flush()
            
            # Extraer texto con OCR (funciona para imágenes y PDFs)
            if is_pdf:
                try:
                    from ..bot.Ocr_untils import extract_text_from_pdf
                    ocr_text = extract_text_from_pdf(tmp_file.name)
                except ImportError:
                    ocr_text = extract_text_from_image(tmp_file.name)  # Fallback
            else:
                ocr_text = extract_text_from_image(tmp_file.name)
            
            if not ocr_text:
                file_type = "PDF" if is_pdf else "imagen"
                return {
                    "response": f"❌ No pude extraer texto del {file_type}. Asegúrate de que sea claro y legible.",
                    "action": "ocr_failed"
                }
            
            # Procesar con IA
            expense_data = extract_expense_json(ocr_text, apartment.code)
            
            if not expense_data or not expense_data.get("amount_gross"):
                file_type = "PDF" if is_pdf else "imagen"
                return {
                    "response": f"❌ No pude extraer datos de gasto del {file_type}.\n\n📝 **Texto extraído:**\n{ocr_text[:300]}...\n\n💡 Puedes escribir el gasto manualmente.",
                    "action": "extraction_failed"
                }
            
            # Crear gasto
            success, response_message = await create_expense_from_data(
                expense_data, 
                apartment, 
                current_account, 
                db
            )
            
            if success:
                file_type = "PDF" if is_pdf else "factura"
                return {
                    "response": f"✅ **¡{file_type.title()} procesado exitosamente!**\n\n🏠 **Apartamento:** {apartment.code} - {apartment.name}\n💰 **Importe:** €{expense_data.get('amount_gross', 0)}\n📅 **Fecha:** {expense_data.get('date', 'Hoy')}\n🏪 **Proveedor:** {expense_data.get('vendor', 'Sin proveedor')}\n📂 **Categoría:** {expense_data.get('category', 'Sin categoría')}\n🧾 **Factura:** {expense_data.get('invoice_number', 'Sin número')}\n\n🤖 **Procesado automáticamente con IA + OCR**",
                    "action": "expense_created",
                    "expense_data": expense_data
                }
            else:
                return {
                    "response": f"❌ **Error registrando gasto:** {response_message}",
                    "action": "creation_failed"
                }
        
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_file.name)
        except:
            pass
            
    except Exception as e:
        return {
            "response": f"❌ Error procesando imagen: {str(e)}",
            "action": "error"
        }

async def process_chat_message(
    message: str, 
    current_account: models.Account, 
    default_apartment: models.Apartment, 
    apartments: list, 
    db: Session
) -> dict:
    """Procesar mensaje de chat y determinar acción"""
    
    message_lower = message.lower()
    
    # Comandos de consulta
    if any(word in message_lower for word in ["cuánto", "gasté", "gastado", "total", "resumen"]):
        return await handle_query_command(message, current_account, db)
    
    # Comandos de apartamentos
    if any(word in message_lower for word in ["apartamento", "apartamentos", "crear apartamento"]):
        return await handle_apartment_command(message, current_account, apartments, db)
    
    # Comandos de ayuda
    if any(word in message_lower for word in ["ayuda", "help", "qué puedes hacer", "funciones"]):
        return {
            "response": """🤖 **¡Hola! Soy tu asistente virtual**

**📸 SUBIR FACTURAS**
• Haz clic en "📸 Foto" y sube tickets/facturas
• Procesamiento automático con OCR + IA

**✍️ ESCRIBIR GASTOS**
• "Restaurante La Marina, 35€, cena"
• "Taxi aeropuerto, 25€"
• "Supermercado, 67.45€, compra semanal"

**📊 CONSULTAS**
• "¿Cuánto gasté este mes?"
• "Mostrar gastos de limpieza"
• "Resumen de gastos"

**🏠 APARTAMENTOS**
• "Mis apartamentos"
• "Crear apartamento nuevo"

¡Escribe un gasto o haz una pregunta!""",
            "action": "help"
        }
    
    # Detectar si es un gasto (contiene precio)
    if any(symbol in message for symbol in ["€", "$", "eur", "euro"]) or any(word in message_lower for word in ["gasto", "pagué", "compré", "factura"]):
        return await handle_expense_creation(message, default_apartment, current_account, db)
    
    # Respuesta por defecto
    return {
        "response": f"""💡 **No estoy seguro de qué quieres hacer**

**¿Querías registrar un gasto?** Escribe algo como:
• "Restaurante La Marina, 35€, cena"
• "Taxi, 25€"

**¿Querías hacer una consulta?** Pregunta:
• "¿Cuánto gasté este mes?"
• "Mostrar gastos de limpieza"

**¿Necesitas ayuda?** Escribe "ayuda"

Tu mensaje: "{message}" """,
        "action": "unclear"
    }

async def handle_expense_creation(
    message: str, 
    apartment: models.Apartment, 
    current_account: models.Account, 
    db: Session
) -> dict:
    """Crear gasto desde mensaje de texto"""
    
    try:
        # Usar IA para extraer datos del mensaje
        expense_data = extract_expense_json(message, apartment.code)
        
        if not expense_data or not expense_data.get("amount_gross"):
            return {
                "response": f"""❌ No pude extraer información del gasto.

**💡 Formato sugerido:**
• "Proveedor, importe€, descripción"

**✅ Ejemplos:**
• "Restaurante La Playa, 45.50€, cena de negocios"
• "Taxi Express, 25€, traslado aeropuerto"
• "Supermercado Dia, 67.45€, compra semanal"

**Tu mensaje:** "{message}" """,
                "action": "format_error"
            }
        
        # Crear gasto
        success, response_message = await create_expense_from_data(
            expense_data, 
            apartment, 
            current_account, 
            db
        )
        
        if success:
            return {
                "response": f"""✅ **¡Gasto registrado exitosamente!**

🏠 **Apartamento:** {apartment.code}
💰 **Importe:** €{expense_data.get('amount_gross', 0)}
🏪 **Proveedor:** {expense_data.get('vendor', 'Sin proveedor')}
📂 **Categoría:** {expense_data.get('category', 'Sin categoría')}
📅 **Fecha:** {expense_data.get('date', 'Hoy')}

El gasto ya aparece en tu dashboard 📊""",
                "action": "expense_created",
                "expense_data": expense_data
            }
        else:
            return {
                "response": f"❌ **Error registrando gasto:** {response_message}",
                "action": "creation_failed"
            }
            
    except Exception as e:
        return {
            "response": f"❌ Error procesando el gasto: {str(e)}",
            "action": "error"
        }

async def handle_query_command(message: str, current_account: models.Account, db: Session) -> dict:
    """Manejar consultas sobre gastos"""
    
    try:
        # Obtener estadísticas básicas del mes actual
        from datetime import date
        current_month = date.today().month
        current_year = date.today().year
        
        # Gastos del mes actual
        monthly_expenses = db.query(models.Expense).join(models.Apartment).filter(
            and_(
                models.Apartment.account_id == current_account.id,
                models.Expense.date >= date(current_year, current_month, 1)
            )
        ).all()
        
        if not monthly_expenses:
            return {
                "response": "📊 **Resumen del mes actual:**\n\n💸 **Gastos:** €0.00\n📝 **Transacciones:** 0\n\n¡Aún no hay gastos registrados este mes!",
                "action": "query_result"
            }
        
        total_amount = sum(exp.amount_gross for exp in monthly_expenses)
        
        # Agrupar por categoría
        categories = {}
        for expense in monthly_expenses:
            category = expense.category or "Sin categoría"
            categories[category] = categories.get(category, 0) + expense.amount_gross
        
        # Top 3 categorías
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        response = f"""📊 **Resumen del mes actual:**

💸 **Total gastado:** €{total_amount:.2f}
📝 **Transacciones:** {len(monthly_expenses)}

🏷️ **Top categorías:**"""
        
        for i, (category, amount) in enumerate(top_categories, 1):
            response += f"\n{i}. {category}: €{amount:.2f}"
        
        return {
            "response": response,
            "action": "query_result"
        }
        
    except Exception as e:
        return {
            "response": f"❌ Error consultando datos: {str(e)}",
            "action": "error"
        }

async def handle_apartment_command(message: str, current_account: models.Account, apartments: list, db: Session) -> dict:
    """Manejar comandos relacionados con apartamentos"""
    
    message_lower = message.lower()
    
    if "crear" in message_lower or "nuevo" in message_lower:
        return {
            "response": """🏠 **Crear nuevo apartamento**

Para crear un apartamento, necesito:
• **Código:** (ej: APT01, PLAYA01)
• **Nombre:** (ej: Apartamento Centro)

**Formato:** "Crear apartamento APT01, Apartamento Centro"

O puedes crearlo desde el dashboard usando el botón "➕ Agregar apartamento" """,
            "action": "apartment_creation_help"
        }
    
    # Listar apartamentos
    if not apartments:
        return {
            "response": "🏠 **Mis apartamentos:** \n\n❌ No tienes apartamentos registrados aún.\n\n💡 Crea uno usando el botón \"➕ Agregar apartamento\" en el dashboard.",
            "action": "no_apartments"
        }
    
    response = f"🏠 **Mis apartamentos ({len(apartments)}):**\n\n"
    
    for apt in apartments:
        status_icon = "✅" if apt.is_active else "⏸️"
        response += f"{status_icon} **{apt.code}** - {apt.name or 'Sin nombre'}\n"
        if apt.description:
            response += f"   📝 {apt.description}\n"
        response += "\n"
    
    return {
        "response": response,
        "action": "apartment_list"
    }

async def create_expense_from_data(
    expense_data: dict, 
    apartment: models.Apartment, 
    current_account: models.Account, 
    db: Session
) -> tuple[bool, str]:
    """Crear gasto en la base de datos"""
    
    try:
        # Crear objeto de gasto
        expense = models.Expense(
            apartment_id=apartment.id,
            date=expense_data.get("date"),
            amount_gross=expense_data.get("amount_gross", 0),
            currency=expense_data.get("currency", "EUR"),
            category=expense_data.get("category"),
            description=expense_data.get("description"),
            vendor=expense_data.get("vendor"),
            invoice_number=expense_data.get("invoice_number"),
            source=expense_data.get("source", "chat_integrated"),
            vat_rate=expense_data.get("vat_rate"),
            file_url=expense_data.get("file_url"),
            status=expense_data.get("status", "PENDING")
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        return True, "Gasto creado exitosamente"
        
    except Exception as e:
        db.rollback()
        return False, str(e)