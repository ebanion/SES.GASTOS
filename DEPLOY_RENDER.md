# 🚀 GUÍA DE DESPLIEGUE EN RENDER - SES.GASTOS

Esta guía te ayudará a desplegar el proyecto SES.GASTOS corregido en Render con todas las mejoras implementadas.

## 📋 PREREQUISITOS

- [ ] Cuenta en [Render](https://render.com)
- [ ] Repositorio de GitHub con el código
- [ ] Token de Telegram Bot (opcional, de @BotFather)
- [ ] API Key de OpenAI (opcional)

## 🗄️ PASO 1: CREAR BASE DE DATOS POSTGRESQL

### 1.1 Crear PostgreSQL Database
1. Ve a [Render Dashboard](https://dashboard.render.com)
2. Clic en **"New +"** → **"PostgreSQL"**
3. Configurar:
   - **Name**: `ses-gastos-db`
   - **Database**: `ses_gastos`
   - **User**: `ses_gastos_user`
   - **Region**: Elige la más cercana
   - **PostgreSQL Version**: 15 (recomendado)
   - **Plan**: Free (para desarrollo) o Starter (para producción)

### 1.2 Obtener URL de Conexión
1. Una vez creada, ve a la página de la base de datos
2. Copia la **"Internal Database URL"** (empieza con `postgresql://`)
3. Guárdala para el siguiente paso

## 🌐 PASO 2: CREAR WEB SERVICE

### 2.1 Crear Web Service
1. En Render Dashboard, clic en **"New +"** → **"Web Service"**
2. Conectar repositorio:
   - **Connect a repository**: Selecciona tu repositorio de GitHub
   - **Branch**: `main` (o la rama que uses)

### 2.2 Configurar Web Service
```yaml
Name: ses-gastos
Environment: Python
Region: [Elige la misma que la base de datos]
Branch: main
Build Command: [Se usa el de render.yaml automáticamente]
Start Command: [Se usa el de render.yaml automáticamente]
```

## 🔧 PASO 3: CONFIGURAR VARIABLES DE ENTORNO

Ve a **"Environment"** en tu Web Service y añade estas variables:

### 3.1 Variables REQUERIDAS
```bash
# Base de datos (OBLIGATORIO)
DATABASE_URL=postgresql+psycopg://[tu_url_de_base_de_datos]
```

### 3.2 Variables RECOMENDADAS
```bash
# Bot de Telegram
TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ

# OpenAI para OCR
OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz

# Seguridad
ADMIN_KEY=tu_clave_admin_muy_segura
INTERNAL_KEY=tu_clave_interna_muy_segura

# Configuración
API_BASE_URL=https://tu-app.onrender.com
TZ=Europe/Madrid
```

### 3.3 Variables AUTOMÁTICAS (No añadir)
Estas se configuran automáticamente:
- `PORT` (Render)
- `PYTHON_VERSION` (render.yaml)
- `TESSDATA_PREFIX` (render.yaml)
- `SQLITE_DIR` (render.yaml)

## 🚀 PASO 4: DESPLEGAR

### 4.1 Iniciar Despliegue
1. Clic en **"Create Web Service"**
2. Render comenzará el build automáticamente
3. Monitorea los logs en tiempo real

### 4.2 Verificar Build
El build ejecutará automáticamente:
```bash
# 1. Instalar dependencias del sistema
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-spa poppler-utils

# 2. Instalar dependencias de Python
pip install -r requirements.txt

# 3. Ejecutar inicialización de producción
python3 init_production.py
```

### 4.3 Logs Esperados
Busca estos mensajes en los logs:
```
🚀 INICIALIZANDO ENTORNO DE PRODUCCIÓN - SES.GASTOS
✅ DATABASE_URL: ***[masked] (URL de base de datos PostgreSQL)
🐘 Usando PostgreSQL
✅ Conexión exitosa
✅ Tablas creadas/verificadas
✅ Creados 3 apartamentos
🎉 INICIALIZACIÓN COMPLETADA EXITOSAMENTE
```

## ✅ PASO 5: VERIFICAR DESPLIEGUE

### 5.1 Endpoints de Verificación
Una vez desplegado, verifica estos endpoints:

```bash
# Health check básico
GET https://tu-app.onrender.com/health
# Respuesta esperada: {"ok": true}

# Estado de base de datos
GET https://tu-app.onrender.com/db-status
# Respuesta esperada: {"database": "connected", "status": "ok"}

# Dashboard principal
GET https://tu-app.onrender.com/api/v1/dashboard/
# Debería mostrar el dashboard con datos

# Estado del bot (si configurado)
GET https://tu-app.onrender.com/bot/status
```

### 5.2 Verificar Base de Datos
```bash
# Diagnóstico completo
GET https://tu-app.onrender.com/bot/diagnose
```

## 🤖 PASO 6: CONFIGURAR BOT DE TELEGRAM (OPCIONAL)

Si configuraste `TELEGRAM_TOKEN`:

### 6.1 Configurar Webhook
```bash
POST https://tu-app.onrender.com/bot/setup-webhook
```

### 6.2 Verificar Webhook
```bash
GET https://tu-app.onrender.com/bot/webhook-status
```

### 6.3 Probar Bot
1. Busca tu bot en Telegram (el username que configuraste)
2. Envía `/start`
3. Envía `/usar SES01`
4. Envía una foto de factura o datos manuales

## 🔍 SOLUCIÓN DE PROBLEMAS

### Error: "No such table"
```bash
# Ejecutar migración manual
POST https://tu-app.onrender.com/migrate-postgres
```

### Error: "Database connection failed"
1. Verifica que `DATABASE_URL` esté configurada correctamente
2. Asegúrate de que la base de datos PostgreSQL esté activa
3. Verifica que la URL use `postgresql+psycopg://`

### Error: "Build failed"
1. Revisa los logs de build en Render
2. Verifica que `requirements.txt` esté actualizado
3. Asegúrate de que todos los archivos estén en el repositorio

### Bot no responde
1. Verifica `TELEGRAM_TOKEN` en variables de entorno
2. Configura el webhook: `POST /bot/setup-webhook`
3. Verifica estado: `GET /bot/webhook-status`

## 📊 MONITOREO Y MANTENIMIENTO

### Logs en Tiempo Real
- Ve a tu Web Service en Render
- Clic en "Logs" para ver logs en tiempo real

### Métricas
- Ve a "Metrics" para ver uso de CPU, memoria, etc.

### Redeploy
- Cada push a la rama principal redesplegará automáticamente
- Para redeploy manual: clic en "Manual Deploy"

## 🎯 ENDPOINTS PRINCIPALES

Una vez desplegado, tendrás acceso a:

```
🏠 Aplicación Principal:
https://tu-app.onrender.com/

📊 Dashboard:
https://tu-app.onrender.com/api/v1/dashboard/

🔧 API Endpoints:
https://tu-app.onrender.com/health
https://tu-app.onrender.com/db-status
https://tu-app.onrender.com/api/v1/apartments/
https://tu-app.onrender.com/api/v1/expenses/
https://tu-app.onrender.com/api/v1/incomes/

🤖 Bot Endpoints:
https://tu-app.onrender.com/bot/status
https://tu-app.onrender.com/bot/diagnose
https://tu-app.onrender.com/webhook/telegram
```

## 🎉 ¡LISTO!

Tu aplicación SES.GASTOS está ahora desplegada en Render con:

- ✅ Base de datos PostgreSQL configurada
- ✅ Migración automática en cada deploy
- ✅ Bot de Telegram funcional (si configurado)
- ✅ OCR automático (si OpenAI configurado)
- ✅ Dashboard web funcional
- ✅ API REST completa
- ✅ Manejo robusto de errores
- ✅ Logs detallados para debugging

## 📞 SOPORTE

Si tienes problemas:
1. Revisa los logs en Render Dashboard
2. Verifica las variables de entorno
3. Usa los endpoints de diagnóstico
4. Consulta esta guía paso a paso

---

**¡Felicidades! Tu sistema SES.GASTOS está en producción! 🎊**