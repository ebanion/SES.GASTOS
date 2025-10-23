# app/routers/email_webhooks.py
from __future__ import annotations

import json
import base64
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.email_reservation_processor import EmailReservationProcessor
from ..auth import get_current_admin_user, get_current_user_optional
from .. import models, schemas

router = APIRouter(prefix="/webhooks/email", tags=["email_webhooks"])


@router.post("/reservation")
async def receive_reservation_email(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir emails de reservas desde servicios como SendGrid, Mailgun, etc.
    
    Formato esperado del webhook:
    {
        "sender": "noreply@booking.com",
        "subject": "Booking Confirmation",
        "text": "contenido del email...",
        "html": "<html>contenido html...</html>",
        "message_id": "unique-message-id",
        "timestamp": "2024-01-15T10:30:00Z"
    }
    """
    try:
        # Obtener datos del webhook
        webhook_data = await request.json()
        
        # Extraer información del email
        sender = webhook_data.get('sender', '')
        subject = webhook_data.get('subject', '')
        text_content = webhook_data.get('text', '')
        html_content = webhook_data.get('html', '')
        message_id = webhook_data.get('message_id', f"manual-{datetime.now().isoformat()}")
        
        # Usar contenido de texto preferentemente, HTML como fallback
        email_content = text_content if text_content else html_content
        
        if not email_content:
            return JSONResponse(
                status_code=400,
                content={"error": "No email content provided"}
            )
        
        # Procesar email en background
        background_tasks.add_task(
            process_reservation_email_task,
            email_content,
            sender,
            subject,
            message_id,
            db
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Email received and queued for processing",
                "message_id": message_id
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error processing webhook: {str(e)}"}
        )


@router.post("/manual")
async def process_manual_email(
    email_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Endpoint para procesar emails manualmente (para testing o casos especiales)
    
    Body:
    {
        "sender": "noreply@booking.com",
        "subject": "Booking Confirmation", 
        "content": "contenido del email...",
        "message_id": "optional-custom-id"
    }
    """
    try:
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        content = email_data.get('content', '')
        message_id = email_data.get('message_id', f"manual-{datetime.now().isoformat()}")
        
        if not content:
            raise HTTPException(status_code=400, detail="Email content is required")
        
        # Procesar email
        processor = EmailReservationProcessor(db)
        result = processor.process_email(content, sender, subject, message_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")


@router.get("/test-formats")
async def get_test_email_formats():
    """
    Devuelve ejemplos de formatos de email para testing
    """
    return {
        "booking_example": {
            "sender": "noreply@booking.com",
            "subject": "Booking Confirmation - Your reservation is confirmed",
            "content": """
            Dear Guest,
            
            Your booking is confirmed!
            
            Booking.com confirmation number: 12345ABC
            Guest name: Juan Pérez
            Property: Apartamento Centro Madrid
            Check-in: 15/01/2024
            Check-out: 18/01/2024
            2 guests
            Total price: €450.00
            
            Thank you for choosing Booking.com
            """
        },
        "airbnb_example": {
            "sender": "noreply@airbnb.com", 
            "subject": "Reservation confirmed",
            "content": """
            Hi there!
            
            Your reservation is confirmed.
            
            Confirmation code: HMABCD123
            Guest: María García
            Listing: Beautiful Apartment Downtown
            Check-in: January 20, 2024
            Check-out: January 23, 2024
            3 guests
            Total: $380.00
            
            Have a great stay!
            """
        },
        "web_example": {
            "sender": "reservas@tu-web.com",
            "subject": "Nueva Reserva Confirmada",
            "content": """
            {
                "apartment_code": "APT001",
                "guest_name": "Carlos López",
                "guest_email": "carlos@email.com",
                "booking_reference": "WEB-2024-001",
                "check_in": "2024-01-25",
                "check_out": "2024-01-28",
                "guests": 2,
                "amount": 320.00,
                "currency": "EUR",
                "status": "CONFIRMED"
            }
            """
        },
        "cancellation_example": {
            "sender": "noreply@booking.com",
            "subject": "Booking Cancellation - Reservation cancelled",
            "content": """
            Dear Guest,
            
            Your booking has been cancelled.
            
            Booking.com confirmation number: 12345ABC
            Property: Apartamento Centro Madrid
            Cancellation date: 14/01/2024
            
            Any applicable refund will be processed according to the cancellation policy.
            """
        }
    }


@router.post("/sendgrid")
async def sendgrid_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook específico para SendGrid Inbound Parse
    """
    try:
        form_data = await request.form()
        
        # SendGrid envía los datos como form data
        sender = form_data.get('from', '')
        subject = form_data.get('subject', '')
        text_content = form_data.get('text', '')
        html_content = form_data.get('html', '')
        
        # SendGrid puede enviar attachments también
        message_id = f"sendgrid-{datetime.now().isoformat()}"
        
        email_content = text_content if text_content else html_content
        
        if not email_content:
            return JSONResponse(status_code=400, content={"error": "No content"})
        
        # Procesar en background
        background_tasks.add_task(
            process_reservation_email_task,
            email_content,
            sender,
            subject,
            message_id,
            db
        )
        
        return JSONResponse(status_code=200, content={"message": "Email processed"})
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"SendGrid webhook error: {str(e)}"}
        )


@router.post("/mailgun")
async def mailgun_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook específico para Mailgun
    """
    try:
        form_data = await request.form()
        
        # Mailgun envía los datos como form data
        sender = form_data.get('sender', '')
        subject = form_data.get('subject', '')
        body_plain = form_data.get('body-plain', '')
        body_html = form_data.get('body-html', '')
        message_id = form_data.get('Message-Id', f"mailgun-{datetime.now().isoformat()}")
        
        email_content = body_plain if body_plain else body_html
        
        if not email_content:
            return JSONResponse(status_code=400, content={"error": "No content"})
        
        # Procesar en background
        background_tasks.add_task(
            process_reservation_email_task,
            email_content,
            sender,
            subject,
            message_id,
            db
        )
        
        return JSONResponse(status_code=200, content={"message": "Email processed"})
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Mailgun webhook error: {str(e)}"}
        )


@router.get("/processed")
async def get_processed_emails(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional)
):
    """
    Obtiene lista de emails procesados (ingresos creados desde email)
    """
    try:
        query = db.query(models.Income).filter(
            models.Income.processed_from_email == True
        )
        
        # Si no es admin, filtrar por apartamentos del usuario
        if current_user and not current_user.is_admin:
            user_apartment_ids = [apt.id for apt in current_user.apartments]
            query = query.filter(models.Income.apartment_id.in_(user_apartment_ids))
        
        incomes = query.order_by(models.Income.created_at.desc()).limit(limit).all()
        
        results = []
        for income in incomes:
            results.append({
                "id": str(income.id),
                "apartment_code": income.apartment.code if income.apartment else "N/A",
                "amount": str(income.amount_gross),
                "currency": income.currency,
                "status": income.status,
                "source": income.source,
                "guest_name": income.guest_name,
                "booking_reference": income.booking_reference,
                "check_in": income.check_in_date.isoformat() if income.check_in_date else None,
                "check_out": income.check_out_date.isoformat() if income.check_out_date else None,
                "non_refundable_at": income.non_refundable_at.isoformat() if income.non_refundable_at else None,
                "created_at": income.created_at.isoformat(),
                "email_message_id": income.email_message_id
            })
        
        return {
            "processed_emails": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching processed emails: {str(e)}")


@router.post("/check-pending")
async def check_pending_reservations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Verifica y confirma reservas pendientes cuyo período de cancelación ha expirado
    (Solo para administradores)
    """
    try:
        processor = EmailReservationProcessor(db)
        results = processor.check_pending_reservations()
        
        return {
            "message": f"Verificación completada. {len(results)} reservas procesadas.",
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking pending reservations: {str(e)}")


async def process_reservation_email_task(
    email_content: str,
    sender: str,
    subject: str,
    message_id: str,
    db: Session
):
    """
    Tarea en background para procesar emails de reservas
    """
    try:
        processor = EmailReservationProcessor(db)
        result = processor.process_email(email_content, sender, subject, message_id)
        
        # Log del resultado (en producción usar logging apropiado)
        print(f"Email processed: {message_id} - {result}")
        
    except Exception as e:
        print(f"Error processing email {message_id}: {str(e)}")