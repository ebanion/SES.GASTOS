# 🔐 Configuración PostgreSQL para SES.GASTOS

## ⚠️ CONFIGURACIÓN ACTUAL CORRECTA

Esta aplicación usa **EXCLUSIVAMENTE PostgreSQL** en producción.

---

## 📋 Variable de Entorno Requerida

### **SOLO SE USA: `DATABASE_URL`**

❌ **NO uses:** `POSTGRES_URL`, `DATABASE_PRIVATE_URL`, ni otras variantes  
✅ **SOLO usa:** `DATABASE_URL`

---

## 🔗 Formato de la URL

```
postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
```

### Elementos OBLIGATORIOS:

1. **`postgresql://`** - Protocolo (no `postgres://`)
2. **`:5432`** - Puerto explícito después del host
3. **`?sslmode=require`** - SSL obligatorio al final
4. **Dominio completo** - Incluir `.frankfurt-postgres.render.com` (o la región correspondiente)

---

## ✅ URL CORRECTA para Render Frankfurt

```
postgresql://ses_gastos_user:vXI94nnE7wvwqcCpHYgnF4robJTc2g6m@dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com:5432/ses_gastos?sslmode=require
```

### Desglose:
- **Usuario:** `ses_gastos_user`
- **Contraseña:** `vXI94nnE7wvwqcCpHYgnF4robJTc2g6m`
- **Host:** `dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com`
- **Puerto:** `5432` (explícito)
- **Base de datos:** `ses_gastos`
- **SSL:** `require` (obligatorio)

---

## 🚀 Configurar en Render

### Paso 1: Ve al Dashboard
```
https://dashboard.render.com/
```

### Paso 2: Configura la Variable

1. Selecciona el servicio: **ses-gastos**
2. Ve a: **Environment** (menú lateral)
3. Busca o crea: **`DATABASE_URL`**
4. Pega la URL completa de arriba
5. **ELIMINA** cualquier otra variable como:
   - ❌ `POSTGRES_URL`
   - ❌ `DATABASE_PRIVATE_URL`
   - ❌ Cualquier URL con credenciales viejas
6. Click en **"Save Changes"**

### Paso 3: Deploy

- Render hará auto-deploy automáticamente
- O haz click en **"Manual Deploy"** → **"Deploy latest commit"**

---

## ✅ Logs Esperados (Éxito)

```
[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...
[DB] ✅ DATABASE_URL configurada correctamente
[DB] 🔗 Conexión PostgreSQL: postgresql+psycopg://ses_gastos_user:***@dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com:5432/ses_gastos?sslmode=require
[DB] 🔌 Puerto: 5432
[DB] 🔒 SSL Mode: require
[DB] 🗄️  Base de datos: ses_gastos
[DB] 🌍 Host: dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com
[DB] 📦 SQLAlchemy version: 2.0.36
[DB] 📦 psycopg version: 3.2.10
[DB] 🔧 Creando engine de PostgreSQL...
[DB] 🔍 Verificando conexión con PostgreSQL...
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: ses_gastos
[DB] 📊 Versión PostgreSQL: 16.x
[DB] 🚀 Sistema listo para operar
[DB] 🎉 Configuración de base de datos completada
[DB] 📌 Sistema configurado EXCLUSIVAMENTE con PostgreSQL
[DB] 🚫 SQLite no está disponible ni como fallback
[DB] ✅ Usando SOLO la variable DATABASE_URL
```

---

## ❌ Errores Comunes y Soluciones

### Error: "autenticación de contraseña falló"

**Causa:** Credenciales incorrectas

**Solución:** Verifica que la URL sea EXACTAMENTE:
```
postgresql://ses_gastos_user:vXI94nnE7wvwqcCpHYgnF4robJTc2g6m@dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com:5432/ses_gastos?sslmode=require
```

### Error: "Nombre o servicio desconocido"

**Causa:** Falta el dominio completo `.frankfurt-postgres.render.com`

**Solución:** Asegúrate de usar el host COMPLETO:
```
dpg-d40htmumcj7s739b70b0-a.frankfurt-postgres.render.com
```

NO uses solo: `dpg-d40htmumcj7s739b70b0-a`

### Error: "DATABASE_URL no está configurada"

**Causa:** Variable no existe en Render

**Solución:** Ve a Environment y créala con el valor correcto

### Error: "could not connect to server"

**Causa:** Base de datos no disponible o puerto incorrecto

**Solución:** 
1. Verifica que la base de datos esté "Available" en Render
2. Asegúrate que la URL incluya `:5432`

---

## 🔒 Seguridad

- ⚠️ **NUNCA** pongas credenciales en el código
- ⚠️ **NUNCA** subas archivos `.env` a Git
- ✅ **SIEMPRE** usa variables de entorno
- ✅ El archivo `.env` está en `.gitignore`

---

## 📦 Dependencias Verificadas

### requirements.txt (CORRECTO):
```
SQLAlchemy==2.0.36          ✅ Versión 2.0+
psycopg[binary]==3.2.10     ✅ psycopg v3 (NO psycopg2)
```

### ⚠️ NO uses:
```
❌ psycopg2
❌ psycopg2-binary
```

Estas son versiones antiguas. Usa **psycopg[binary]** versión 3.

---

## 🎯 Resumen de Cambios Aplicados

1. ✅ **app/db.py** simplificado para usar SOLO `DATABASE_URL`
2. ✅ Eliminadas referencias a `POSTGRES_URL` y `DATABASE_PRIVATE_URL`
3. ✅ Sin fallback a SQLite en producción
4. ✅ Normalización automática de URL a `postgresql+psycopg://`
5. ✅ Puerto `:5432` añadido automáticamente si falta
6. ✅ `?sslmode=require` añadido automáticamente si falta
7. ✅ Logs claros mostrando host, puerto, SSL, base de datos
8. ✅ 3 reintentos con 2 segundos de espera entre cada uno
9. ✅ Mensajes de error detallados con soluciones

---

## 📞 Verificación Post-Deploy

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

## 🎓 Notas Importantes

1. **Una sola variable:** Solo `DATABASE_URL`, nada más
2. **Puerto obligatorio:** Siempre incluir `:5432`
3. **SSL obligatorio:** Siempre incluir `?sslmode=require`
4. **Dominio completo:** Usar `.frankfurt-postgres.render.com`
5. **Sin SQLite:** No hay fallback en producción
6. **psycopg v3:** Usar `psycopg[binary]`, no `psycopg2`

---

*Configuración actualizada: 2025-10-28*  
*Base de datos: ses_gastos @ Render Frankfurt PostgreSQL*  
*Usa EXCLUSIVAMENTE la configuración de este documento*
