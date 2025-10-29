# 🔐 Configuración de Credenciales en Render - ACTUALIZADO

## ⚠️ NUEVA BASE DE DATOS CONFIGURADA

Has cambiado a una nueva base de datos PostgreSQL. Aquí está la configuración correcta.

---

## 📍 Dónde Configurar

1. Ve a: **https://dashboard.render.com/**
2. Selecciona el servicio: **ses-gastos**
3. Ve a: **Environment** (en el menú lateral)
4. Añade o **ACTUALIZA** las siguientes variables:

---

## 🔑 Variables de Entorno Requeridas

### **DATABASE_URL** (OBLIGATORIA)

⚠️ **USA ESTA URL EXACTA** (con puerto `:5432` y `?sslmode=require`):

```
postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
```

### **DATABASE_PRIVATE_URL** (Recomendada)
```
postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
```

### **POSTGRES_URL** (Opcional)
```
postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
```

---

## 📊 Detalles de Conexión (Nueva Base de Datos)

| Parámetro | Valor |
|-----------|-------|
| **Host** | `dpg-d40htmumcj7s739b70b0-a` |
| **Puerto** | `5432` |
| **Base de datos** | `ses_gastos` |
| **Usuario** | `ses_gastos_user` |
| **Contraseña** | `vXI94nnE7wwwqcCpHYgnF4robJtC2g6m` |
| **SSL Mode** | `require` (OBLIGATORIO) |

---

## ⚠️ PROBLEMA DETECTADO EN TU URL DE RENDER

### ❌ **URL que te da Render (INCORRECTA para nuestra app):**
```
postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a/ses_gastos
                                                                                      ↑ FALTA :5432
                                                                                                      ↑ FALTA ?sslmode=require
```

### ✅ **URL que DEBES usar en Environment:**
```
postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
                                                                                      ↑ AÑADE :5432    ↑ AÑADE ?sslmode=require
```

---

## 🔍 Por Qué Falló Antes

### Error anterior:
```
FATAL: autenticación de contraseña fallida para el usuario "dbname_zoe8_user"
```

### Causa:
Estabas usando credenciales de la **base de datos VIEJA**:
- ❌ Usuario viejo: `dbname_zoe8_user`
- ❌ Base de datos vieja: `dbname_zoe8`
- ❌ Host viejo: `dpg-d33s6rruibrs73asgjp0-a`

### Nueva configuración:
- ✅ Usuario nuevo: `ses_gastos_user`
- ✅ Base de datos nueva: `ses_gastos`
- ✅ Host nuevo: `dpg-d40htmumcj7s739b70b0-a`

---

## 🚀 Pasos para Aplicar los Cambios

### **1. Actualizar DATABASE_URL en Render**

1. Ve a: **Render Dashboard → ses-gastos → Environment**
2. Busca la variable **`DATABASE_URL`**
3. **REEMPLÁZALA** con esta URL exacta:
   ```
   postgresql://ses_gastos_user:vXI94nnE7wwwqcCpHYgnF4robJtC2g6m@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
   ```
4. Haz click en **"Save Changes"**

### **2. Forzar Deploy**

Después de guardar:
1. En la página del servicio, click en **"Manual Deploy"**
2. Selecciona: **"Deploy latest commit"**

---

## ✅ Logs Esperados (Éxito)

Cuando funcione correctamente, verás:

```
[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...
[DB] ✅ DATABASE_URL encontrada desde: DATABASE_URL
[DB] 🔗 Conexión PostgreSQL: postgresql+psycopg://ses_gastos_user:***@dpg-d40htmumcj7s739b70b0-a:5432/ses_gastos?sslmode=require
[DB] 🔌 Puerto: 5432
[DB] 🔒 SSL Mode: require
[DB] 🗄️  Base de datos: ses_gastos
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: ses_gastos
[DB] 📊 Versión PostgreSQL: 16.x
[DB] 🚀 Sistema listo para operar
[startup] ✅ PostgreSQL conectado exitosamente
[startup] ✅ Tablas creadas/verificadas
Application startup complete
```

---

## 🎯 Checklist Final

Antes de desplegar, verifica:

- [ ] ✅ DATABASE_URL actualizada con las **NUEVAS** credenciales
- [ ] ✅ La URL incluye `:5432` después del host
- [ ] ✅ La URL termina con `?sslmode=require`
- [ ] ✅ Usuario es `ses_gastos_user` (no el viejo)
- [ ] ✅ Base de datos es `ses_gastos` (no la vieja)
- [ ] ✅ Has guardado los cambios en Environment
- [ ] ✅ La base de datos está "Available" (verde) en Render

---

## 📞 Verificación Rápida

Después del deploy, verifica:

```bash
curl https://ses-gastos.onrender.com/system-status
```

Debería mostrar:
```json
{
  "database": {
    "type": "postgresql",
    "status": "connected"
  }
}
```

---

## 🔒 Seguridad

⚠️ **NUNCA** pongas estas credenciales en el código fuente  
⚠️ **NUNCA** las subas a Git  
✅ **SIEMPRE** configúralas como variables de entorno en Render  

---

## 📝 Resumen de Cambios

### Base de Datos ANTERIOR (ya no usar):
- Host: `dpg-d33s6rruibrs73asgjp0-a`
- Usuario: `dbname_zoe8_user`
- BD: `dbname_zoe8`

### Base de Datos NUEVA (usar ahora):
- Host: `dpg-d40htmumcj7s739b70b0-a`
- Usuario: `ses_gastos_user`
- BD: `ses_gastos`

---

*Fecha actualización: 2025-10-28*  
*Base de datos: ses_gastos @ Render PostgreSQL*  
*Esta es la configuración CORRECTA y ACTUAL*
