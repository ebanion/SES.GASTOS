# 🤖 Bot SES.GASTOS con OCR + IA - Funcionalidad Completa

## 🎉 **¡FUNCIONALIDAD OCR + IA RESTAURADA!**

He implementado la funcionalidad completa de **OCR + Inteligencia Artificial** que tenías originalmente. Ahora el bot puede procesar facturas automáticamente.

## 🚀 **Nuevas Capacidades**

### **📸 Procesamiento de Fotos**
- ✅ **OCR automático** con Tesseract
- ✅ **Extracción de texto** en español e inglés
- ✅ **Análisis con IA** (OpenAI GPT-4o-mini)
- ✅ **Creación automática** del gasto

### **📄 Procesamiento de PDFs**
- ✅ **Extracción de texto digital** con pdfplumber
- ✅ **OCR de PDFs escaneados** con Tesseract
- ✅ **Análisis completo con IA**
- ✅ **Soporte para facturas complejas**

### **🤖 Datos Extraídos Automáticamente**
- 📅 **Fecha** de la factura
- 💰 **Importe total** (amount_gross)
- 🏪 **Proveedor/Empresa** (vendor)
- 📂 **Categoría** del gasto (category)
- 📄 **Descripción** del servicio/producto
- 🧾 **Número de factura** (invoice_number)
- 💼 **Tasa de IVA** (vat_rate)
- 💱 **Moneda** (EUR por defecto)

## 📱 **Cómo Usar el Bot Mejorado**

### **Paso 1: Configurar Apartamento**
```
/usar SES01
```

### **Paso 2: Enviar Factura (3 opciones)**

#### **Opción A: Foto de Factura** 📸
```
1. Toma foto clara de la factura
2. Envía la foto al bot
3. El bot automáticamente:
   - Extrae texto con OCR
   - Analiza con IA
   - Crea el gasto
   - Te muestra los datos extraídos
```

#### **Opción B: PDF de Factura** 📄
```
1. Envía el PDF de la factura
2. El bot automáticamente:
   - Extrae texto del PDF
   - Si es escaneado, usa OCR
   - Analiza con IA
   - Crea el gasto completo
```

#### **Opción C: Datos Manuales** 📝
```
Si prefieres o si el OCR falla:
2025-01-22
45.50
Restaurante Ejemplo
Restauración
Cena de trabajo
```

## 🔧 **Flujo de Procesamiento Automático**

### **Para Fotos:**
```
📸 Foto recibida
    ↓
🔍 OCR con Tesseract
    ↓
📄 Texto extraído
    ↓
🤖 Análisis con OpenAI
    ↓
📊 Datos estructurados
    ↓
💾 Gasto creado automáticamente
    ↓
✅ Confirmación al usuario
```

### **Para PDFs:**
```
📄 PDF recibido
    ↓
📥 Descarga temporal
    ↓
🔍 Extracción con pdfplumber + OCR
    ↓
📄 Texto completo extraído
    ↓
🤖 Análisis con OpenAI
    ↓
📊 Datos estructurados (más completos)
    ↓
💾 Gasto creado automáticamente
    ↓
✅ Confirmación detallada
```

## 📋 **Ejemplo de Respuesta Automática**

### **Foto Procesada:**
```
✅ ¡Gasto procesado automáticamente!

🤖 Datos extraídos por IA:
📅 Fecha: 2025-01-22
💰 Importe: €45.50
🏪 Proveedor: Restaurante El Buen Comer
📂 Categoría: Restauración
📄 Descripción: Cena de negocios
🏠 Apartamento: SES01

🆔 ID: abc-123-def
🌐 Ver en: https://ses-gastos.onrender.com/api/v1/dashboard/

💡 Si algo es incorrecto, puedes editarlo en el dashboard.
```

### **PDF Procesado:**
```
✅ ¡PDF procesado automáticamente!

📄 Archivo: factura_enero_2025.pdf
🤖 Datos extraídos por IA:
📅 Fecha: 2025-01-22
💰 Importe: €125.75
🏪 Proveedor: Suministros Técnicos S.L.
📂 Categoría: Mantenimiento
📄 Descripción: Reparación sistema eléctrico
🧾 Factura: FAC-2025-001234
💼 IVA: 21%
🏠 Apartamento: SES01

🆔 ID: xyz-789-abc
🌐 Ver en: https://ses-gastos.onrender.com/api/v1/dashboard/
```

## 🛡️ **Manejo de Errores**

### **Si OCR Falla:**
```
❌ No se pudo extraer texto de la imagen

Posibles causas:
• Imagen muy borrosa
• Texto muy pequeño
• Idioma no reconocido

💡 Prueba con:
• Foto más clara y enfocada
• Mejor iluminación
• O introduce los datos manualmente
```

### **Si IA No Puede Extraer Datos:**
```
❌ No se pudo extraer información suficiente

📄 Texto extraído:
[Muestra el texto OCR]

💡 Introduce los datos manualmente:
2025-01-22
45.50
Proveedor
Categoría
Descripción
```

### **Si OCR No Está Disponible:**
```
❌ OCR no disponible en este entorno

💡 Introduce los datos manualmente:
[Formato manual]
```

## 🎯 **Ventajas de la Nueva Implementación**

### **Vs. Modo Manual Anterior:**
- ❌ **Antes**: Siempre pedía datos manuales
- ✅ **Ahora**: Procesamiento automático completo

### **Vs. Bot Original:**
- ✅ **Integrado en webhook** (mejor para producción)
- ✅ **Manejo de errores mejorado**
- ✅ **Fallback a modo manual**
- ✅ **Mensajes informativos durante procesamiento**
- ✅ **Soporte para PDFs y fotos**

## 🔮 **Funcionalidades Avanzadas**

### **Inteligencia Artificial:**
- 🧠 **Modelo**: GPT-4o-mini (rápido y preciso)
- 🌍 **Idiomas**: Español e inglés
- 📊 **Categorización automática** de gastos
- 💰 **Detección de importes** con decimales
- 📅 **Normalización de fechas** a formato ISO

### **OCR Avanzado:**
- 🔍 **Tesseract** para imágenes
- 📄 **pdfplumber** para PDFs digitales
- 🖼️ **pdf2image** para PDFs escaneados
- 🌍 **Soporte multiidioma** (spa+eng)

## 📊 **Comandos Disponibles**

```
/start    → Instrucciones completas
/usar     → Configurar apartamento (SES01, SES02, SES03)
/actual   → Ver apartamento configurado
/reset    → Cambiar apartamento
/status   → Estado del sistema

📸 Foto   → Procesamiento automático con OCR + IA
📄 PDF    → Procesamiento completo de facturas
📝 Texto  → Entrada manual (fallback)
```

## 🎉 **¡LISTO PARA USAR!**

El bot ahora tiene **toda la funcionalidad OCR + IA** que tenías originalmente, pero mejorada:

1. **Envía foto** → Procesamiento automático
2. **Envía PDF** → Extracción completa
3. **Datos manuales** → Si prefieres o como fallback

**¡Prueba enviando una foto o PDF de una factura real!** 🚀

El bot debería extraer automáticamente todos los datos y crear el gasto sin necesidad de entrada manual.