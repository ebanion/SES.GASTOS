# 🔐 Configuración de Credenciales en Render

## ⚠️ IMPORTANTE: Configurar Variables de Entorno

Para que la aplicación funcione correctamente con PostgreSQL, debes configurar estas variables en Render:

---

## 📍 Dónde Configurar

1. Ve a: **https://dashboard.render.com/**
2. Selecciona el servicio: **ses-gastos**
3. Ve a: **Environment** (en el menú lateral)
4. Añade o actualiza las siguientes variables:

---

## 🔑 Variables de Entorno Requeridas

### **DATABASE_URL** (OBLIGATORIA)
```
postgresql://dbname_zoe8_user:hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
```

### **DATABASE_PRIVATE_URL** (Recomendada)
```
postgresql://dbname_zoe8_user:hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
```

### **POSTGRES_URL** (Opcional)
```
postgresql://dbname_zoe8_user:hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
```

---

## 📊 Detalles de Conexión

| Parámetro | Valor |
|-----------|-------|
| **Host** | `dpg-d33s6rruibrs73asgjp0-a` |
| **Puerto** | `5432` |
| **Base de datos** | `dbname_zoe8` |
| **Usuario** | `dbname_zoe8_user` |
| **Contraseña** | `hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz` |
| **SSL Mode** | `require` (OBLIGATORIO) |

---

## ✅ Verificación

### URL Completa Correcta:
```
postgresql://dbname_zoe8_user:hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
```

### ⚠️ Elementos CRÍTICOS:
- ✅ Incluye el puerto `:5432`
- ✅ Incluye `?sslmode=require` al final
- ✅ Usa el host interno de Render: `dpg-d33s6rruibrs73asgjp0-a`
- ✅ Usuario correcto: `dbname_zoe8_user`
- ✅ Contraseña correcta: `hnqHqSRLFRdYTzZdq69b6M569Q6oG1Oz`

---

## 🚀 Después de Configurar

1. **Guarda los cambios** en Environment variables
2. Render te preguntará si quieres redesplegar
3. Haz click en **"Deploy"** o espera el auto-deploy
4. Monitorea los logs

---

## 📋 Logs Esperados (Éxito)

Cuando funcione correctamente verás:

```
[DB] 🐘 Iniciando configuración de base de datos PostgreSQL...
[DB] ✅ DATABASE_URL encontrada desde: DATABASE_URL
[DB] 🔗 Conexión PostgreSQL: postgresql+psycopg://dbname_zoe8_user:***@dpg-d33s6rruibrs73asgjp0-a:5432/dbname_zoe8?sslmode=require
[DB] 🔌 Puerto: 5432
[DB] 🔒 SSL Mode: require
[DB] 🗄️  Base de datos: dbname_zoe8
[DB] ✅ PostgreSQL CONECTADO exitosamente
[DB] 🎯 Base de datos: dbname_zoe8
[DB] 📊 Versión PostgreSQL: 16.x
[DB] 🚀 Sistema listo para operar
```

---

## ❌ Errores Comunes

### Error: "autenticación de contraseña fallida"
**Causa:** Credenciales incorrectas en `DATABASE_URL`  
**Solución:** Verifica que la URL sea EXACTAMENTE la de arriba

### Error: "could not connect to server"
**Causa:** Base de datos no disponible  
**Solución:** Ve a Dashboard → Databases → Verifica que esté "Available" (verde)

### Error: "DATABASE_URL no está configurada"
**Causa:** Variable no existe en Render  
**Solución:** Añade `DATABASE_URL` en Environment con el valor correcto

---

## 🔒 Seguridad

⚠️ **NUNCA** pongas estas credenciales en el código fuente  
⚠️ **NUNCA** las subas a Git  
✅ **SIEMPRE** configúralas como variables de entorno en Render  
✅ Este archivo está en `.gitignore` para proteger las credenciales  

---

## 📞 Soporte

Si después de configurar las variables sigues viendo errores:

1. Verifica que la base de datos esté "Available" en Render
2. Verifica que las credenciales sean exactamente las de arriba
3. Fuerza un rebuild: "Clear build cache & deploy"
4. Revisa los logs completos en Render Dashboard

---

*Fecha: 2025-10-28*  
*Base de datos: dbname_zoe8 @ Render PostgreSQL*
