# 🔐 CREDENCIALES ACTUALES - BASE DE DATOS NUEVA

## ✅ NUEVA BASE DE DATOS (USAR ESTA)

**Creada:** 2025-10-28

---

## 📊 CREDENCIALES

| Campo | Valor |
|-------|-------|
| **Base de datos** | `dbname_datos` |
| **Usuario** | `dbname_datos_user` |
| **Contraseña** | `Pzo5TmCecLKblGlNCB1IqF8YXbje7D21` |
| **Host INTERNO** | `dpg-d410jvodl3ps73dd84vg-a` |
| **Host EXTERNO** | `dpg-d410jvodl3ps73dd84vg-a.frankfurt-postgres.render.com` |
| **Puerto** | `5432` |
| **Región** | Frankfurt |

---

## 🎯 URL CORRECTA PARA RENDER ENVIRONMENT

**Variable:** `DATABASE_URL`

**Valor (COPIA EXACTA):**

```
postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require
```

**IMPORTANTE:**
- ✅ Usa host INTERNO (corto): `dpg-d410jvodl3ps73dd84vg-a`
- ✅ Incluye puerto: `:5432`
- ✅ Incluye SSL: `?sslmode=require`

---

## 📋 URLs DE RENDER

### Internal (lo que Render te da):
```
postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a/dbname_datos
```

### Internal CORRECTA (añadir :5432 y ?sslmode=require):
```
postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require
```

### External (lo que Render te da):
```
postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a.frankfurt-postgres.render.com/dbname_datos
```

### External CORRECTA (añadir :5432 y ?sslmode=require):
```
postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a.frankfurt-postgres.render.com:5432/dbname_datos?sslmode=require
```

---

## ✅ VERIFICACIÓN DEL CÓDIGO

### **✅ app/db.py** - CORRECTO
- NO tiene credenciales hardcodeadas
- Lee de `os.getenv("DATABASE_URL")`
- Normaliza automáticamente la URL

### **✅ app/config.py** - CORRECTO
- NO tiene credenciales hardcodeadas
- Lee de `os.getenv("DATABASE_URL")`

### **✅ app/main.py** - CORRECTO
- NO tiene credenciales hardcodeadas
- Usa el engine de app/db.py

---

## 🚀 CONFIGURACIÓN EN RENDER

1. Ve a: **https://dashboard.render.com/**
2. Selecciona: **ses-gastos**
3. Ve a: **Environment**
4. Busca: **`DATABASE_URL`**
5. **VERIFICA** que tenga:
   ```
   postgresql://dbname_datos_user:Pzo5TmCecLKblGlNCB1IqF8YXbje7D21@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require
   ```
6. Si no tiene `:5432` y `?sslmode=require`, añádelos
7. **Guarda** cambios

---

## ⚠️ BASES DE DATOS ANTIGUAS (NO USAR)

### ❌ Base de datos 1 (ANTIGUA):
- Usuario: `dbname_zoe8_user`
- Host: `dpg-d33s6rruibrs73asgjp0-a`
- ❌ NO USAR

### ❌ Base de datos 2 (ANTIGUA):
- Usuario: `ses_gastos_user`
- Host: `dpg-d40htmumcj7s739b70b0-a`
- ❌ NO USAR

### ✅ Base de datos 3 (ACTUAL):
- Usuario: `dbname_datos_user`
- Host: `dpg-d410jvodl3ps73dd84vg-a`
- ✅ **USAR ESTA**

---

## 📝 LOGS ESPERADOS

```
[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...
[DB] ✅ DATABASE_URL configurada correctamente
[DB] 🔗 Conexión PostgreSQL: postgresql+psycopg://dbname_datos_user:***@dpg-d410jvodl3ps73dd84vg-a:5432/dbname_datos?sslmode=require
[DB] 🔌 Puerto: 5432
[DB] 🔒 SSL Mode: require
[DB] 🗄️  Base de datos: dbname_datos
[DB] 🌍 Host: dpg-d410jvodl3ps73dd84vg-a
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: dbname_datos
[DB] 📊 Versión PostgreSQL: 16.x
[DB] 🚀 Sistema listo para operar
```

---

## 🔍 SI AÚN FALLA

Verifica en Render Environment que NO existan estas variables:
- ❌ `POSTGRES_URL`
- ❌ `DATABASE_PRIVATE_URL`
- ❌ Ninguna URL con credenciales viejas

Solo debe existir:
- ✅ `DATABASE_URL` (con la URL correcta de arriba)

---

*Base de datos actual: dbname_datos*  
*Host: dpg-d410jvodl3ps73dd84vg-a*  
*Región: Frankfurt*
