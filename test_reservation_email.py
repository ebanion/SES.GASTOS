#!/usr/bin/env python3
"""
Script para probar el sistema de emails de reservas en producción
"""

import requests
import json
from datetime import datetime, timedelta

# URL base de producción
BASE_URL = "https://ses-gastos.onrender.com"

def test_booking_email():
    """Prueba un email de Booking.com"""
    
    # Fecha de check-in en 5 días (para que esté en PENDING)
    check_in_date = (datetime.now() + timedelta(days=5)).strftime("%d/%m/%Y")
    check_out_date = (datetime.now() + timedelta(days=8)).strftime("%d/%m/%Y")
    
    email_data = {
        "sender": "noreply@booking.com",
        "subject": "Booking Confirmation - Your reservation is confirmed",
        "content": f"""
Dear Guest,

Your booking is confirmed!

Booking.com confirmation number: TEST{datetime.now().strftime('%Y%m%d%H%M')}
Guest name: Juan Pérez Test
Property: SES01
Check-in: {check_in_date}
Check-out: {check_out_date}
2 guests
Total price: €250.00

Thank you for choosing Booking.com

This is a test email sent at {datetime.now().isoformat()}
        """.strip(),
        "message_id": f"test-booking-{datetime.now().isoformat()}"
    }
    
    return email_data

def test_airbnb_email():
    """Prueba un email de Airbnb"""
    
    # Fecha de check-in en 10 días
    check_in_date = (datetime.now() + timedelta(days=10)).strftime("%B %d, %Y")
    check_out_date = (datetime.now() + timedelta(days=13)).strftime("%B %d, %Y")
    
    email_data = {
        "sender": "noreply@airbnb.com",
        "subject": "Reservation confirmed",
        "content": f"""
Hi there!

Your reservation is confirmed.

Confirmation code: TEST{datetime.now().strftime('%Y%m%d%H%M')}
Guest: María García Test
Listing: SES02
Check-in: {check_in_date}
Check-out: {check_out_date}
3 guests
Total: $320.00

Have a great stay!

This is a test email sent at {datetime.now().isoformat()}
        """.strip(),
        "message_id": f"test-airbnb-{datetime.now().isoformat()}"
    }
    
    return email_data

def test_web_email():
    """Prueba un email de web propia"""
    
    check_in_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    check_out_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    email_data = {
        "sender": "reservas@ses-gastos.com",
        "subject": "Nueva Reserva Confirmada",
        "content": json.dumps({
            "apartment_code": "SES03",
            "guest_name": "Carlos López Test",
            "guest_email": "carlos.test@email.com",
            "booking_reference": f"WEB-TEST-{datetime.now().strftime('%Y%m%d%H%M')}",
            "check_in": check_in_date,
            "check_out": check_out_date,
            "guests": 2,
            "amount": 180.00,
            "currency": "EUR",
            "status": "CONFIRMED"
        }, indent=2),
        "message_id": f"test-web-{datetime.now().isoformat()}"
    }
    
    return email_data

def send_test_email(email_data, test_name):
    """Envía un email de prueba al webhook"""
    
    url = f"{BASE_URL}/webhooks/email/manual"
    
    print(f"\n🧪 Probando {test_name}...")
    print(f"📧 Enviando a: {url}")
    print(f"📨 Email de: {email_data['sender']}")
    print(f"📋 Asunto: {email_data['subject']}")
    
    try:
        response = requests.post(url, json=email_data, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {test_name} - ÉXITO!")
            print(f"📝 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ {test_name} - ERROR!")
            print(f"📝 Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {test_name} - EXCEPCIÓN!")
        print(f"📝 Error: {str(e)}")
        return False

def check_processed_emails():
    """Verifica los emails procesados"""
    
    url = f"{BASE_URL}/webhooks/email/processed"
    
    print(f"\n📋 Verificando emails procesados...")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Emails procesados encontrados: {result.get('total', 0)}")
            
            if result.get('processed_emails'):
                print("\n📧 Últimos emails procesados:")
                for email in result['processed_emails'][:5]:  # Mostrar solo los últimos 5
                    print(f"  • {email.get('source', 'N/A')} | {email.get('apartment_code', 'N/A')} | €{email.get('amount', 'N/A')} | {email.get('status', 'N/A')}")
            
            return True
        else:
            print(f"❌ Error obteniendo emails procesados: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando emails: {str(e)}")
        return False

def main():
    """Función principal de testing"""
    
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE EMAILS DE RESERVAS")
    print("=" * 60)
    print(f"🌐 URL Base: {BASE_URL}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # Verificar estado inicial
    print("\n📋 Estado inicial...")
    check_processed_emails()
    
    # Ejecutar pruebas
    tests = [
        (test_booking_email(), "Booking.com"),
        (test_airbnb_email(), "Airbnb"),
        (test_web_email(), "Web Propia")
    ]
    
    results = []
    
    for email_data, test_name in tests:
        success = send_test_email(email_data, test_name)
        results.append((test_name, success))
        
        # Pausa entre pruebas
        import time
        time.sleep(2)
    
    # Verificar estado final
    print("\n📋 Estado final...")
    check_processed_emails()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    
    successful = 0
    for test_name, success in results:
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"  • {test_name}: {status}")
        if success:
            successful += 1
    
    print(f"\n🎯 Resultado: {successful}/{len(results)} pruebas exitosas")
    
    if successful == len(results):
        print("🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema funciona correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar logs arriba.")
    
    print("\n🔍 Para ver los resultados en el dashboard:")
    print(f"   👉 {BASE_URL}/dashboard/")
    print(f"   👉 {BASE_URL}/api/v1/incomes/reservations")

if __name__ == "__main__":
    main()