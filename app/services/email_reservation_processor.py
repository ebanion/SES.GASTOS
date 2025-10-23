# app/services/email_reservation_processor.py
from __future__ import annotations

import re
import json
import email
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Optional, List, Tuple
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .. import models
from ..db import get_db


class EmailReservationProcessor:
    """Procesa emails de reservas de Booking.com, Airbnb y web propia"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def process_email(self, email_content: str, sender: str, subject: str, message_id: str) -> Dict:
        """
        Procesa un email de reserva y extrae la información relevante
        
        Args:
            email_content: Contenido del email (texto plano o HTML)
            sender: Email del remitente
            subject: Asunto del email
            message_id: ID único del mensaje de email
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            # Verificar si ya procesamos este email
            existing = self.db.query(models.Income).filter(
                models.Income.email_message_id == message_id
            ).first()
            
            if existing:
                return {
                    "success": False,
                    "message": f"Email ya procesado anteriormente: {message_id}",
                    "income_id": str(existing.id)
                }
            
            # Detectar el tipo de plataforma
            platform = self._detect_platform(sender, subject, email_content)
            
            # Procesar según la plataforma
            if platform == "BOOKING":
                return self._process_booking_email(email_content, subject, message_id)
            elif platform == "AIRBNB":
                return self._process_airbnb_email(email_content, subject, message_id)
            elif platform == "WEB":
                return self._process_web_email(email_content, subject, message_id)
            else:
                return {
                    "success": False,
                    "message": f"Plataforma no reconocida: {sender}",
                    "platform": platform
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando email: {str(e)}",
                "error": str(e)
            }
    
    def _detect_platform(self, sender: str, subject: str, content: str) -> str:
        """Detecta la plataforma de reserva basándose en el remitente y contenido"""
        
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        content_lower = content.lower()
        
        # Booking.com
        if any(domain in sender_lower for domain in ['booking.com', 'noreply@booking.com']):
            return "BOOKING"
        
        # Airbnb
        if any(domain in sender_lower for domain in ['airbnb.com', 'noreply@airbnb.com']):
            return "AIRBNB"
        
        # Web propia (configurar según tu dominio)
        if any(domain in sender_lower for domain in ['ses-gastos.com', 'tu-web.com']):
            return "WEB"
        
        # Detectar por contenido si el remitente no es claro
        if any(keyword in content_lower for keyword in ['booking.com', 'booking confirmation']):
            return "BOOKING"
        
        if any(keyword in content_lower for keyword in ['airbnb', 'reservation confirmed']):
            return "AIRBNB"
        
        return "UNKNOWN"
    
    def _process_booking_email(self, content: str, subject: str, message_id: str) -> Dict:
        """Procesa emails de Booking.com"""
        
        try:
            # Detectar tipo de email (confirmación o cancelación)
            is_cancellation = any(keyword in content.lower() for keyword in [
                'cancellation', 'cancelled', 'canceled', 'cancelación', 'cancelada'
            ])
            
            # Extraer datos de la reserva
            reservation_data = self._extract_booking_data(content)
            
            if not reservation_data:
                return {
                    "success": False,
                    "message": "No se pudieron extraer datos de la reserva de Booking.com"
                }
            
            # Buscar apartamento por código o nombre
            apartment = self._find_apartment_by_reference(
                reservation_data.get('property_name', ''),
                reservation_data.get('apartment_code', '')
            )
            
            if not apartment:
                return {
                    "success": False,
                    "message": f"No se encontró apartamento para: {reservation_data.get('property_name', 'N/A')}",
                    "reservation_data": reservation_data
                }
            
            if is_cancellation:
                return self._process_cancellation(reservation_data, apartment, message_id, "BOOKING")
            else:
                return self._create_income_from_booking(reservation_data, apartment, message_id)
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando email de Booking: {str(e)}"
            }
    
    def _process_airbnb_email(self, content: str, subject: str, message_id: str) -> Dict:
        """Procesa emails de Airbnb"""
        
        try:
            # Detectar tipo de email
            is_cancellation = any(keyword in content.lower() for keyword in [
                'cancellation', 'cancelled', 'canceled', 'cancelación', 'cancelada'
            ])
            
            # Extraer datos de la reserva
            reservation_data = self._extract_airbnb_data(content)
            
            if not reservation_data:
                return {
                    "success": False,
                    "message": "No se pudieron extraer datos de la reserva de Airbnb"
                }
            
            # Buscar apartamento
            apartment = self._find_apartment_by_reference(
                reservation_data.get('property_name', ''),
                reservation_data.get('apartment_code', '')
            )
            
            if not apartment:
                return {
                    "success": False,
                    "message": f"No se encontró apartamento para: {reservation_data.get('property_name', 'N/A')}",
                    "reservation_data": reservation_data
                }
            
            if is_cancellation:
                return self._process_cancellation(reservation_data, apartment, message_id, "AIRBNB")
            else:
                return self._create_income_from_airbnb(reservation_data, apartment, message_id)
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando email de Airbnb: {str(e)}"
            }
    
    def _process_web_email(self, content: str, subject: str, message_id: str) -> Dict:
        """Procesa emails de reservas de web propia"""
        
        try:
            # Extraer datos JSON del email (formato estructurado)
            reservation_data = self._extract_web_data(content)
            
            if not reservation_data:
                return {
                    "success": False,
                    "message": "No se pudieron extraer datos de la reserva web"
                }
            
            # Buscar apartamento por código
            apartment = self.db.query(models.Apartment).filter(
                models.Apartment.code == reservation_data.get('apartment_code')
            ).first()
            
            if not apartment:
                return {
                    "success": False,
                    "message": f"No se encontró apartamento con código: {reservation_data.get('apartment_code')}",
                    "reservation_data": reservation_data
                }
            
            return self._create_income_from_web(reservation_data, apartment, message_id)
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error procesando email web: {str(e)}"
            }
    
    def _extract_booking_data(self, content: str) -> Optional[Dict]:
        """Extrae datos específicos de emails de Booking.com"""
        
        data = {}
        
        # Patrones de regex para Booking.com
        patterns = {
            'booking_reference': r'Booking\.com confirmation number[:\s]*([A-Z0-9]+)',
            'guest_name': r'Guest name[:\s]*([^\n\r]+)',
            'property_name': r'Property[:\s]*([^\n\r]+)',
            'check_in': r'Check-in[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})',
            'check_out': r'Check-out[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})',
            'total_price': r'Total price[:\s]*€?\s*([0-9,]+\.?[0-9]*)',
            'guests': r'([0-9]+)\s+guest[s]?'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        
        # Convertir fechas
        if 'check_in' in data:
            data['check_in_date'] = self._parse_date(data['check_in'])
        if 'check_out' in data:
            data['check_out_date'] = self._parse_date(data['check_out'])
        
        # Convertir precio
        if 'total_price' in data:
            data['amount'] = self._parse_amount(data['total_price'])
        
        return data if data else None
    
    def _extract_airbnb_data(self, content: str) -> Optional[Dict]:
        """Extrae datos específicos de emails de Airbnb"""
        
        data = {}
        
        # Patrones de regex para Airbnb
        patterns = {
            'booking_reference': r'Confirmation code[:\s]*([A-Z0-9]+)',
            'guest_name': r'Guest[:\s]*([^\n\r]+)',
            'property_name': r'Listing[:\s]*([^\n\r]+)',
            'check_in': r'Check-in[:\s]*([A-Za-z]+\s+[0-9]{1,2},\s+[0-9]{4})',
            'check_out': r'Check-out[:\s]*([A-Za-z]+\s+[0-9]{1,2},\s+[0-9]{4})',
            'total_price': r'Total[:\s]*\$([0-9,]+\.?[0-9]*)',
            'guests': r'([0-9]+)\s+guest[s]?'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
        
        # Convertir fechas (formato Airbnb: "January 15, 2024")
        if 'check_in' in data:
            data['check_in_date'] = self._parse_date_airbnb(data['check_in'])
        if 'check_out' in data:
            data['check_out_date'] = self._parse_date_airbnb(data['check_out'])
        
        # Convertir precio
        if 'total_price' in data:
            data['amount'] = self._parse_amount(data['total_price'])
        
        return data if data else None
    
    def _extract_web_data(self, content: str) -> Optional[Dict]:
        """Extrae datos de emails de web propia (formato JSON estructurado)"""
        
        try:
            # Buscar JSON en el contenido
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Si no hay JSON, usar patrones similares a Booking
            return self._extract_booking_data(content)
            
        except json.JSONDecodeError:
            return None
    
    def _find_apartment_by_reference(self, property_name: str, apartment_code: str = "") -> Optional[models.Apartment]:
        """Busca apartamento por nombre de propiedad o código"""
        
        # Primero intentar por código exacto
        if apartment_code:
            apartment = self.db.query(models.Apartment).filter(
                models.Apartment.code == apartment_code.upper()
            ).first()
            if apartment:
                return apartment
        
        # Buscar por nombre (coincidencia parcial)
        if property_name:
            apartment = self.db.query(models.Apartment).filter(
                models.Apartment.name.ilike(f"%{property_name}%")
            ).first()
            if apartment:
                return apartment
        
        return None
    
    def _create_income_from_booking(self, data: Dict, apartment: models.Apartment, message_id: str) -> Dict:
        """Crea un ingreso desde datos de Booking.com"""
        
        try:
            # Calcular fecha de no reembolso (normalmente 24-48h antes del check-in)
            check_in_date = data.get('check_in_date')
            non_refundable_date = None
            if check_in_date:
                # Booking normalmente permite cancelación hasta 24h antes
                non_refundable_date = check_in_date - timedelta(days=1)
            
            income = models.Income(
                apartment_id=apartment.id,
                date=datetime.now().date(),
                amount_gross=Decimal(str(data.get('amount', 0))),
                currency="EUR",
                status="PENDING" if non_refundable_date and non_refundable_date > datetime.now().date() else "CONFIRMED",
                non_refundable_at=non_refundable_date,
                source="BOOKING",
                guest_name=data.get('guest_name'),
                booking_reference=data.get('booking_reference'),
                check_in_date=data.get('check_in_date'),
                check_out_date=data.get('check_out_date'),
                guests_count=int(data.get('guests', 1)),
                email_message_id=message_id,
                processed_from_email=True
            )
            
            self.db.add(income)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Ingreso creado desde Booking.com: €{income.amount_gross}",
                "income_id": str(income.id),
                "apartment_code": apartment.code,
                "status": income.status,
                "non_refundable_at": non_refundable_date.isoformat() if non_refundable_date else None
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error creando ingreso de Booking: {str(e)}"
            }
    
    def _create_income_from_airbnb(self, data: Dict, apartment: models.Apartment, message_id: str) -> Dict:
        """Crea un ingreso desde datos de Airbnb"""
        
        try:
            # Airbnb tiene políticas de cancelación más estrictas
            check_in_date = data.get('check_in_date')
            non_refundable_date = None
            if check_in_date:
                # Airbnb normalmente permite cancelación hasta 5-7 días antes
                non_refundable_date = check_in_date - timedelta(days=5)
            
            income = models.Income(
                apartment_id=apartment.id,
                date=datetime.now().date(),
                amount_gross=Decimal(str(data.get('amount', 0))),
                currency="EUR",
                status="PENDING" if non_refundable_date and non_refundable_date > datetime.now().date() else "CONFIRMED",
                non_refundable_at=non_refundable_date,
                source="AIRBNB",
                guest_name=data.get('guest_name'),
                booking_reference=data.get('booking_reference'),
                check_in_date=data.get('check_in_date'),
                check_out_date=data.get('check_out_date'),
                guests_count=int(data.get('guests', 1)),
                email_message_id=message_id,
                processed_from_email=True
            )
            
            self.db.add(income)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Ingreso creado desde Airbnb: €{income.amount_gross}",
                "income_id": str(income.id),
                "apartment_code": apartment.code,
                "status": income.status,
                "non_refundable_at": non_refundable_date.isoformat() if non_refundable_date else None
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error creando ingreso de Airbnb: {str(e)}"
            }
    
    def _create_income_from_web(self, data: Dict, apartment: models.Apartment, message_id: str) -> Dict:
        """Crea un ingreso desde datos de web propia"""
        
        try:
            income = models.Income(
                apartment_id=apartment.id,
                date=datetime.now().date(),
                amount_gross=Decimal(str(data.get('amount', 0))),
                currency=data.get('currency', 'EUR'),
                status=data.get('status', 'CONFIRMED'),
                source="WEB",
                guest_name=data.get('guest_name'),
                guest_email=data.get('guest_email'),
                booking_reference=data.get('booking_reference'),
                check_in_date=self._parse_date(data.get('check_in')) if data.get('check_in') else None,
                check_out_date=self._parse_date(data.get('check_out')) if data.get('check_out') else None,
                guests_count=int(data.get('guests', 1)),
                email_message_id=message_id,
                processed_from_email=True
            )
            
            self.db.add(income)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Ingreso creado desde web propia: €{income.amount_gross}",
                "income_id": str(income.id),
                "apartment_code": apartment.code,
                "status": income.status
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error creando ingreso web: {str(e)}"
            }
    
    def _process_cancellation(self, data: Dict, apartment: models.Apartment, message_id: str, source: str) -> Dict:
        """Procesa una cancelación de reserva"""
        
        try:
            # Buscar ingreso existente por referencia de booking
            booking_ref = data.get('booking_reference')
            if not booking_ref:
                return {
                    "success": False,
                    "message": "No se encontró referencia de booking para cancelar"
                }
            
            income = self.db.query(models.Income).filter(
                models.Income.booking_reference == booking_ref,
                models.Income.apartment_id == apartment.id,
                models.Income.source == source
            ).first()
            
            if not income:
                return {
                    "success": False,
                    "message": f"No se encontró ingreso para cancelar con referencia: {booking_ref}"
                }
            
            # Actualizar estado a cancelado
            income.status = "CANCELLED"
            income.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Reserva cancelada: {booking_ref} - €{income.amount_gross}",
                "income_id": str(income.id),
                "cancelled_amount": str(income.amount_gross)
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"Error procesando cancelación: {str(e)}"
            }
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Convierte string de fecha a objeto date"""
        
        if not date_str:
            return None
        
        # Formatos comunes: DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%m/%d/%Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_date_airbnb(self, date_str: str) -> Optional[date]:
        """Convierte fecha de Airbnb (January 15, 2024) a objeto date"""
        
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str.strip(), '%B %d, %Y').date()
        except ValueError:
            # Fallback a parser genérico
            return self._parse_date(date_str)
    
    def _parse_amount(self, amount_str: str) -> float:
        """Convierte string de cantidad a float"""
        
        if not amount_str:
            return 0.0
        
        # Remover símbolos de moneda y comas
        clean_amount = re.sub(r'[€$£,]', '', amount_str.strip())
        
        try:
            return float(clean_amount)
        except ValueError:
            return 0.0
    
    def check_pending_reservations(self) -> List[Dict]:
        """Verifica reservas pendientes que ya no son reembolsables"""
        
        today = datetime.now().date()
        
        # Buscar ingresos pendientes cuya fecha de no reembolso ya pasó
        pending_incomes = self.db.query(models.Income).filter(
            models.Income.status == "PENDING",
            models.Income.non_refundable_at <= today
        ).all()
        
        results = []
        
        for income in pending_incomes:
            try:
                income.status = "CONFIRMED"
                income.updated_at = datetime.now()
                
                results.append({
                    "income_id": str(income.id),
                    "apartment_code": income.apartment.code if income.apartment else "N/A",
                    "amount": str(income.amount_gross),
                    "booking_reference": income.booking_reference,
                    "message": "Reserva confirmada automáticamente (período de cancelación expirado)"
                })
                
            except Exception as e:
                results.append({
                    "income_id": str(income.id),
                    "error": f"Error confirmando reserva: {str(e)}"
                })
        
        if results:
            self.db.commit()
        
        return results