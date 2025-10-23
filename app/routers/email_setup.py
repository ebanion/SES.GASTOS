# app/routers/email_setup.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from ..db import get_db
from ..auth import get_current_user, get_current_admin_user
from .. import models

router = APIRouter(prefix="/email-setup", tags=["email_setup"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@router.get("/", response_class=HTMLResponse)
def email_setup_page(
    request: Request,
    current_user: models.User = Depends(get_current_user)
):
    """
    Página de configuración de emails automáticos
    """
    # URL base de la aplicación
    base_url = str(request.base_url).rstrip('/')
    
    # URLs de webhooks
    webhook_urls = {
        "general": f"{base_url}/webhooks/email/reservation",
        "sendgrid": f"{base_url}/webhooks/email/sendgrid", 
        "mailgun": f"{base_url}/webhooks/email/mailgun",
        "manual": f"{base_url}/webhooks/email/manual"
    }
    
    # Apartamentos del usuario
    user_apartments = current_user.apartments if current_user.apartments else []
    
    return templates.TemplateResponse("email_setup.html", {
        "request": request,
        "user": current_user,
        "webhook_urls": webhook_urls,
        "user_apartments": user_apartments,
        "base_url": base_url
    })


@router.get("/instructions")
def get_setup_instructions():
    """
    Devuelve instrucciones detalladas para configurar el reenvío de emails
    """
    return {
        "booking_com": {
            "title": "Configuración para Booking.com",
            "steps": [
                "1. Inicia sesión en tu cuenta de Booking.com Partner Hub",
                "2. Ve a 'Configuración' > 'Notificaciones por email'", 
                "3. Busca 'Confirmaciones de reserva' y 'Cancelaciones'",
                "4. Añade como email adicional: reservas@tu-dominio.com",
                "5. Configura tu servidor de email para reenviar a nuestro webhook"
            ],
            "email_format": "Booking.com envía emails estructurados con confirmación, datos del huésped, fechas y precio total"
        },
        "airbnb": {
            "title": "Configuración para Airbnb",
            "steps": [
                "1. Inicia sesión en tu cuenta de Airbnb Host",
                "2. Ve a 'Configuración de la cuenta' > 'Notificaciones'",
                "3. En 'Reservas' activa 'Confirmación de reserva por email'",
                "4. En 'Cancelaciones' activa notificaciones por email", 
                "5. Configura reenvío desde tu email a nuestro webhook"
            ],
            "email_format": "Airbnb envía confirmaciones con código de reserva, datos del huésped y detalles de la estancia"
        },
        "web_propia": {
            "title": "Configuración para Web Propia",
            "steps": [
                "1. Configura tu sistema de reservas para enviar emails a nuestro webhook",
                "2. Usa el formato JSON estructurado que proporcionamos",
                "3. Incluye todos los campos requeridos: apartment_code, guest_name, fechas, precio",
                "4. Envía tanto confirmaciones como cancelaciones"
            ],
            "email_format": "JSON estructurado con todos los datos de la reserva"
        },
        "email_forwarding": {
            "title": "Configuración de Reenvío de Email",
            "options": [
                {
                    "service": "Gmail",
                    "steps": [
                        "1. Ve a Configuración > Reenvío y POP/IMAP",
                        "2. Añade dirección de reenvío",
                        "3. Crea filtros para emails de Booking/Airbnb",
                        "4. Configura reenvío automático a webhook"
                    ]
                },
                {
                    "service": "SendGrid Inbound Parse",
                    "steps": [
                        "1. Configura un subdominio (ej: reservas.tu-dominio.com)",
                        "2. Añade registros MX apuntando a SendGrid",
                        "3. Configura webhook URL en SendGrid",
                        "4. Usa nuestro endpoint /webhooks/email/sendgrid"
                    ]
                },
                {
                    "service": "Mailgun",
                    "steps": [
                        "1. Configura dominio en Mailgun",
                        "2. Añade registros DNS requeridos",
                        "3. Configura Routes para reenvío",
                        "4. Usa nuestro endpoint /webhooks/email/mailgun"
                    ]
                }
            ]
        }
    }


@router.get("/test-webhook")
def test_webhook_connectivity(
    current_user: models.User = Depends(get_current_user)
):
    """
    Prueba la conectividad del webhook
    """
    import requests
    from datetime import datetime
    
    # URL base de la aplicación
    base_url = os.getenv("BASE_URL", "https://ses-gastos.onrender.com")
    webhook_url = f"{base_url}/webhooks/email/manual"
    
    # Email de prueba
    test_email = {
        "sender": "test@booking.com",
        "subject": "Test Booking Confirmation",
        "content": f"""
        Dear Guest,
        
        Your booking is confirmed!
        
        Booking.com confirmation number: TEST123
        Guest name: Test User
        Property: Test Apartment
        Check-in: 25/01/2024
        Check-out: 28/01/2024
        2 guests
        Total price: €150.00
        
        This is a test email sent at {datetime.now().isoformat()}
        """,
        "message_id": f"test-{datetime.now().isoformat()}"
    }
    
    try:
        response = requests.post(webhook_url, json=test_email, timeout=10)
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "webhook_url": webhook_url,
            "test_email": test_email
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "webhook_url": webhook_url
        }


@router.post("/validate-apartment-mapping")
def validate_apartment_mapping(
    property_names: list[str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Valida que los nombres de propiedades de Booking/Airbnb 
    se puedan mapear a apartamentos existentes
    """
    results = []
    
    for property_name in property_names:
        # Buscar apartamento por nombre (coincidencia parcial)
        apartment = db.query(models.Apartment).filter(
            models.Apartment.user_id == current_user.id,
            models.Apartment.name.ilike(f"%{property_name}%")
        ).first()
        
        if apartment:
            results.append({
                "property_name": property_name,
                "matched": True,
                "apartment_code": apartment.code,
                "apartment_name": apartment.name,
                "confidence": "high" if property_name.lower() in apartment.name.lower() else "medium"
            })
        else:
            results.append({
                "property_name": property_name,
                "matched": False,
                "suggestion": "Crear apartamento o ajustar nombre para coincidencia automática",
                "confidence": "none"
            })
    
    return {
        "mappings": results,
        "total_properties": len(property_names),
        "matched_count": len([r for r in results if r["matched"]]),
        "unmatched_count": len([r for r in results if not r["matched"]])
    }


@router.get("/webhook-logs")
def get_webhook_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Obtiene logs de webhooks procesados para el usuario
    """
    # Obtener ingresos procesados por email del usuario
    user_apartment_ids = [apt.id for apt in current_user.apartments]
    
    if not user_apartment_ids:
        return {"logs": [], "total": 0}
    
    logs = db.query(models.Income).filter(
        models.Income.apartment_id.in_(user_apartment_ids),
        models.Income.processed_from_email == True
    ).order_by(models.Income.created_at.desc()).limit(limit).all()
    
    log_entries = []
    for log in logs:
        log_entries.append({
            "timestamp": log.created_at.isoformat(),
            "message_id": log.email_message_id,
            "source": log.source,
            "apartment_code": log.apartment.code if log.apartment else "N/A",
            "status": log.status,
            "amount": str(log.amount_gross),
            "guest_name": log.guest_name,
            "booking_reference": log.booking_reference,
            "success": True
        })
    
    return {
        "logs": log_entries,
        "total": len(log_entries),
        "user_apartments": len(user_apartment_ids)
    }