# 📧 Sistema de Procesamiento Automático de Emails de Reservas

## 🎯 Resumen del Sistema

He implementado un **sistema completo de procesamiento automático de emails de reservas** que permite:

- ✅ **Procesamiento automático** de emails de Booking.com, Airbnb y web propia
- ✅ **Gestión inteligente** de períodos de cancelación gratuita
- ✅ **Reversión automática** de ingresos cuando se cancelan reservas
- ✅ **Integración completa** con el dashboard financiero existente
- ✅ **Configuración fácil** mediante interfaz web

## 🚀 Funcionalidades Implementadas

### 📨 Procesamiento de Emails
- **Parser inteligente** que detecta automáticamente la plataforma (Booking, Airbnb, Web)
- **Extracción de datos** con regex optimizado para cada plataforma
- **Prevención de duplicados** mediante message_id único
- **Mapeo automático** a apartamentos por código o nombre

### ⏰ Gestión de Estados de Reserva
- **PENDING**: Reserva confirmada pero aún en período de cancelación gratuita
- **CONFIRMED**: Reserva confirmada y no reembolsable
- **CANCELLED**: Reserva cancelada (revierte el ingreso)

### 🔄 Automatización Completa
- **Confirmación automática** cuando expira el período de cancelación
- **Reversión automática** de ingresos cancelados
- **Tareas programadas** para verificar estados pendientes

## 🛠️ Componentes Técnicos

### 1. Modelo de Datos Extendido (`models.py`)
```python
class Income(Base):
    # Campos originales...
    
    # Nuevos campos para reservas por email
    guest_name = Column(String(255))
    guest_email = Column(String(255))
    booking_reference = Column(String(100))
    check_in_date = Column(Date)
    check_out_date = Column(Date)
    guests_count = Column(Integer)
    email_message_id = Column(String(255), unique=True)
    processed_from_email = Column(Boolean, default=False)
```

### 2. Procesador de Emails (`email_reservation_processor.py`)
- **Detección automática** de plataforma por remitente y contenido
- **Parsers específicos** para Booking.com, Airbnb y web propia
- **Gestión de cancelaciones** con búsqueda por referencia de booking
- **Cálculo automático** de fechas de no reembolso

### 3. Endpoints de Webhooks (`email_webhooks.py`)
- `/webhooks/email/reservation` - Webhook general
- `/webhooks/email/sendgrid` - Específico para SendGrid
- `/webhooks/email/mailgun` - Específico para Mailgun
- `/webhooks/email/manual` - Para testing y casos especiales

### 4. Configuración Web (`email_setup.py` + `email_setup.html`)
- **Interfaz completa** para configurar reenvío de emails
- **Instrucciones paso a paso** para cada plataforma
- **Testing integrado** con pruebas de conectividad
- **Monitoreo** de emails procesados

## 📊 URLs del Sistema

### 🌐 Configuración (Requiere Login)
```
https://ses-gastos.onrender.com/email-setup/
```

### 🔗 Webhooks Públicos
```
https://ses-gastos.onrender.com/webhooks/email/reservation
https://ses-gastos.onrender.com/webhooks/email/sendgrid  
https://ses-gastos.onrender.com/webhooks/email/mailgun
https://ses-gastos.onrender.com/webhooks/email/manual
```

### 📈 APIs de Datos
```
https://ses-gastos.onrender.com/api/v1/incomes/reservations
https://ses-gastos.onrender.com/api/v1/incomes/stats
https://ses-gastos.onrender.com/api/v1/incomes/upcoming-checkins
```

## 🎯 Flujo Completo de Uso

### Para Cliente con 4 Apartamentos:

#### 1. **Configuración Inicial** (Una sola vez)
```
1. Login en https://ses-gastos.onrender.com/
2. Ir a "Configurar Emails" desde el dashboard
3. Seguir instrucciones para Booking.com:
   - Partner Hub → Notificaciones → Email adicional
   - Configurar reenvío a webhook
4. Seguir instrucciones para Airbnb:
   - Configuración → Notificaciones → Activar emails
   - Configurar reenvío desde email principal
```

#### 2. **Funcionamiento Automático**
```
📧 Email de Booking llega → Webhook procesa → Ingreso creado automáticamente
📧 Email de Airbnb llega → Webhook procesa → Ingreso creado automáticamente  
📧 Email de cancelación → Webhook procesa → Ingreso marcado como CANCELLED
⏰ Período de cancelación expira → Sistema confirma automáticamente
```

#### 3. **Monitoreo y Control**
```
📊 Dashboard muestra ingresos de reservas en tiempo real
📈 Estadísticas por plataforma (Booking vs Airbnb vs Web)
📅 Próximos check-ins automáticamente detectados
🔍 Log completo de emails procesados
```

## 🔧 Configuración Técnica

### Opción 1: SendGrid Inbound Parse (Recomendado)
```bash
1. Configurar subdominio: reservas.tu-dominio.com
2. Añadir registros MX apuntando a SendGrid
3. Configurar webhook URL: /webhooks/email/sendgrid
4. Booking/Airbnb → reservas@tu-dominio.com → SendGrid → Webhook
```

### Opción 2: Reenvío de Gmail/Outlook
```bash
1. Configurar filtros para emails de Booking/Airbnb
2. Reenvío automático a email intermedio
3. Script/servicio que envía a webhook
4. Menos confiable pero más simple
```

### Opción 3: Mailgun Routes
```bash
1. Configurar dominio en Mailgun
2. Añadir registros DNS requeridos  
3. Configurar Routes para reenvío automático
4. Webhook URL: /webhooks/email/mailgun
```

## 📋 Formatos de Email Soportados

### Booking.com
```
Booking.com confirmation number: 12345ABC
Guest name: Juan Pérez
Property: Apartamento Centro Madrid
Check-in: 15/01/2024
Check-out: 18/01/2024
2 guests
Total price: €450.00
```

### Airbnb
```
Confirmation code: HMABCD123
Guest: María García
Listing: Beautiful Apartment Downtown
Check-in: January 20, 2024
Check-out: January 23, 2024
3 guests
Total: $380.00
```

### Web Propia (JSON)
```json
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
```

## 🎉 Beneficios del Sistema

### ⚡ Automatización Total
- **0 intervención manual** para registrar reservas
- **Procesamiento en tiempo real** 24/7
- **Gestión automática** de cancelaciones

### 📊 Contabilidad Precisa  
- **Estados correctos** (pendiente vs confirmado)
- **Reversión automática** de cancelaciones
- **Integración completa** con dashboard existente

### 🔍 Visibilidad Completa
- **Próximos check-ins** automáticamente detectados
- **Estadísticas por plataforma** en tiempo real
- **Log completo** de actividad de emails

### 🛡️ Robustez y Seguridad
- **Prevención de duplicados** por message_id
- **Manejo de errores** robusto
- **Validación de datos** completa

## 🚀 ¡Listo para Usar!

El sistema está **completamente implementado y desplegado**. Los usuarios pueden:

1. **Acceder a configuración**: `/email-setup/`
2. **Configurar sus plataformas** siguiendo las instrucciones
3. **Probar el sistema** con el testing integrado
4. **Ver resultados** en tiempo real en su dashboard

**¡La automatización de ingresos por reservas está lista y funcionando!** 🎉