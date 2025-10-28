# 🚀 Instrucciones para Deploy en Render

## ✅ Estado Actual del Proyecto

Tu proyecto está **completamente preparado** para PostgreSQL. Los cambios están listos pero necesitan ser commiteados y pusheados.

---

## 📋 Pre-requisitos Verificados

✅ PostgreSQL configurado exclusivamente  
✅ Variables de entorno configuradas en Render:
- `DATABASE_URL` con sslmode=require
- `DATABASE_PRIVATE_URL` con sslmode=require
- `POSTGRES_URL` con sslmode=require

✅ render.yaml configurado correctamente  
✅ Todos los cambios de código completados  

---

## 🚀 PASO A PASO PARA DEPLOY

### **Paso 1: Commitear los Cambios**

Abre tu terminal en el proyecto y ejecuta:

```bash
# Ver los cambios pendientes
git status

# Añadir todos los archivos modificados y nuevos
git add .

# Crear el commit con un mensaje descriptivo
git commit -m "Migración completa a PostgreSQL

- Configuración exclusiva de PostgreSQL sin fallback a SQLite
- Añadido sslmode=require automático
- Verificación de conexión con SELECT 1 y 3 reintentos
- Pool de conexiones optimizado para producción
- Logs seguros con credenciales enmascaradas
- Documentación completa de migración
- Eliminados archivos SQLite de prueba

Cambios principales:
- app/db.py: PostgreSQL exclusivo
- app/main.py: Startup verificado
- setup_database.py: Validación estricta
- .gitignore: Ignora archivos SQLite
- Documentación: 6 nuevos archivos de guía"
```

### **Paso 2: Push al Repositorio**

```bash
# Push a la branch actual
git push origin cursor/migrar-base-de-datos-a-postgresql-4547
```

### **Paso 3: Deploy en Render**

Render detectará automáticamente el push y comenzará el deploy. Pero también puedes forzarlo manualmente:

#### Opción A: Deploy Automático (Recomendado)
1. Ve a tu dashboard de Render: https://dashboard.render.com/
2. Busca el servicio **ses-gastos**
3. Render detectará el nuevo commit automáticamente
4. Verás "Deploy in progress..."

#### Opción B: Deploy Manual
1. Ve a https://dashboard.render.com/
2. Selecciona el servicio **ses-gastos**
3. Click en **"Manual Deploy"** > **"Deploy latest commit"**

---

## 📊 Qué Esperar Durante el Deploy

### 1️⃣ **Build Phase** (2-5 minutos)
Verás estos pasos:
```
==> Installing dependencies from requirements.txt
==> Installing tesseract-ocr
==> Installing poppler-utils
✅ Build successful
```

### 2️⃣ **Deploy Phase** (1-2 minutos)
```
==> Starting service
==> Running: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3️⃣ **Logs Esperados** ✅
Si todo va bien, verás en los logs:

```
[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...
[DB] ✅ DATABASE_URL encontrada desde: DATABASE_URL
[DB] 🔗 Conexión PostgreSQL: postgresql+psycopg://dbname_zoe8_user:***@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
[DB] 🔌 Puerto: 5432
[DB] 🔒 SSL Mode: require
[DB] 🗄️  Base de datos: dbname_zoe8
[DB] 📦 SQLAlchemy version: 2.0.36
[DB] 📦 psycopg version: 3.2.10
[DB] 🔧 Creando engine de PostgreSQL...
[DB] 🔍 Verificando conexión con PostgreSQL...
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: dbname_zoe8
[DB] 📊 Versión PostgreSQL: 16.4
[DB] 🚀 Sistema listo para operar
[DB] 🎉 Configuración de base de datos completada
[DB] 📌 Sistema configurado EXCLUSIVAMENTE con PostgreSQL
[DB] 🚫 SQLite no está disponible ni como fallback

[startup] 🔍 Verificando conexión PostgreSQL...
[startup] ✅ PostgreSQL conectado exitosamente
[startup] 🎯 Base de datos: dbname_zoe8
[startup] 📊 Versión PostgreSQL: 16.4
[startup] ✅ Tablas creadas/verificadas

INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## ✅ Verificación Post-Deploy

### 1. Verificar que el servicio está corriendo

Visita tu URL de Render:
```
https://ses-gastos.onrender.com/
```

### 2. Verificar el estado de la base de datos

```bash
curl https://ses-gastos.onrender.com/debug/database-status
```

**Respuesta esperada:**
```json
{
  "success": true,
  "database_type": "PostgreSQL",
  "persistence": "✅ PERSISTENTE (PostgreSQL)"
}
```

### 3. Verificar los logs en Render

1. Ve a tu dashboard de Render
2. Selecciona el servicio **ses-gastos**
3. Click en **"Logs"**
4. Busca los mensajes de éxito:
   - ✅ PostgreSQL CONECTADO exitosamente
   - ✅ Tablas creadas/verificadas

---

## 🐛 Solución de Problemas

### ❌ Error: "DATABASE_URL no está configurada"

**Causa:** Variable de entorno no visible para el servicio

**Solución:**
1. Ve a Render Dashboard > ses-gastos > Environment
2. Verifica que `DATABASE_URL` esté configurada
3. Debe contener: `postgresql://...?sslmode=require`
4. Guarda y redeploya

### ❌ Error: "No se pudo conectar a PostgreSQL"

**Causa:** Base de datos PostgreSQL no accesible

**Solución:**
1. Ve a Render Dashboard > Databases
2. Verifica que la base de datos esté **Active**
3. Verifica que `DATABASE_URL` sea correcta
4. Verifica que incluya `?sslmode=require`

### ❌ Error: "ModuleNotFoundError: No module named 'psycopg'"

**Causa:** Dependencia no instalada

**Solución:**
1. Verifica que `requirements.txt` incluya: `psycopg[binary]==3.2.10`
2. Fuerza un rebuild: Manual Deploy > Clear build cache

### ❌ El deploy se completa pero la app no arranca

**Causa:** Error en el código de inicio

**Solución:**
1. Revisa los logs completos en Render
2. Busca mensajes de error después de "Starting service"
3. Verifica que no haya errores de sintaxis

---

## 📱 Verificar que Todo Funciona

### Test Completo:

1. **Health Check:**
   ```bash
   curl https://ses-gastos.onrender.com/health
   ```

2. **Database Status:**
   ```bash
   curl https://ses-gastos.onrender.com/debug/database-status
   ```

3. **System Status:**
   ```bash
   curl https://ses-gastos.onrender.com/system-status
   ```

4. **Apartamentos (requiere autenticación):**
   ```bash
   curl https://ses-gastos.onrender.com/api/v1/apartments/
   ```

---

## 🔄 Si Necesitas Rollback

Si algo sale mal, puedes hacer rollback:

1. Ve a Render Dashboard > ses-gastos
2. Click en **"Events"**
3. Busca el último deploy exitoso anterior
4. Click en **"Rollback to this version"**

---

## 📊 Monitoreo Post-Deploy

### Cosas a Verificar:

- ✅ El servicio está "Active" (verde) en Render
- ✅ Los logs muestran "PostgreSQL CONECTADO exitosamente"
- ✅ No hay errores en los últimos logs
- ✅ La URL responde correctamente
- ✅ Los endpoints de API funcionan

### Logs a Buscar:

```bash
# Logs buenos ✅
[DB] ✅ PostgreSQL CONECTADO exitosamente
[startup] ✅ PostgreSQL conectado exitosamente
Application startup complete

# Logs malos ❌
[DB] ❌ ERROR CRÍTICO
OperationalError: could not connect
ModuleNotFoundError
```

---

## 🎯 Resumen del Proceso

```
1. git add .
2. git commit -m "Migración a PostgreSQL"
3. git push origin cursor/migrar-base-de-datos-a-postgresql-4547
4. Render detecta el push automáticamente
5. Build + Deploy (3-7 minutos)
6. Verificar logs: ✅ PostgreSQL CONECTADO
7. Probar endpoints
8. ¡Listo! 🎉
```

---

## 📞 Si Necesitas Ayuda

### Logs Importantes:

```bash
# Ver logs en tiempo real desde terminal (si tienes CLI de Render)
render logs -f ses-gastos

# O desde el dashboard:
# https://dashboard.render.com > ses-gastos > Logs
```

### Archivos de Referencia:

- `README_POSTGRESQL.md` - Comandos básicos
- `RESUMEN_MIGRACION.md` - Qué cambió
- `CAMBIOS_MIGRACION_POSTGRESQL.md` - Detalles técnicos
- `COMANDOS_RAPIDOS.md` - Verificaciones útiles

---

## ✨ Después del Deploy

Una vez que el deploy sea exitoso:

1. ✅ Tu app estará usando PostgreSQL exclusivamente
2. ✅ Los datos serán persistentes entre deploys
3. ✅ No habrá fallbacks a SQLite
4. ✅ Logs claros mostrando el estado de PostgreSQL
5. ✅ SSL/TLS habilitado automáticamente
6. ✅ Pool de conexiones optimizado

---

## 🎉 ¡Listo!

Ejecuta estos comandos y en 5-10 minutos tu app estará desplegada con PostgreSQL:

```bash
git add .
git commit -m "Migración completa a PostgreSQL"
git push origin cursor/migrar-base-de-datos-a-postgresql-4547
```

Luego solo espera y observa los logs en Render Dashboard.

---

*¿Dudas? Revisa los logs en Render y busca mensajes con ✅ o ❌*
