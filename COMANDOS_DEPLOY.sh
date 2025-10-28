#!/bin/bash

# Script para facilitar el deploy a Render
# Ejecuta: bash COMANDOS_DEPLOY.sh

echo "═══════════════════════════════════════════════════════════"
echo "  🚀 DEPLOY A RENDER - PostgreSQL Migration"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "app/db.py" ]; then
    echo "❌ Error: No estás en el directorio del proyecto"
    exit 1
fi

echo "📋 Paso 1: Verificando cambios pendientes..."
git status --short

echo ""
echo "═══════════════════════════════════════════════════════════"
read -p "¿Continuar con el commit y deploy? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Deploy cancelado"
    exit 1
fi

echo ""
echo "📦 Paso 2: Añadiendo archivos al staging..."
git add .

echo ""
echo "📝 Paso 3: Creando commit..."
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

if [ $? -ne 0 ]; then
    echo "❌ Error al crear el commit"
    exit 1
fi

echo ""
echo "🚀 Paso 4: Pusheando a GitHub..."
BRANCH=$(git branch --show-current)
git push origin $BRANCH

if [ $? -ne 0 ]; then
    echo "❌ Error al hacer push"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ PUSH COMPLETADO"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 Render detectará el cambio automáticamente y comenzará el deploy"
echo ""
echo "🔍 Monitorea el deploy en:"
echo "   https://dashboard.render.com/"
echo ""
echo "📋 Logs esperados:"
echo "   [DB] ✅ PostgreSQL CONECTADO exitosamente"
echo "   [startup] ✅ PostgreSQL conectado exitosamente"
echo "   [startup] ✅ Tablas creadas/verificadas"
echo ""
echo "🌐 Verifica tu app en:"
echo "   https://ses-gastos.onrender.com/debug/database-status"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  🎉 ¡Deploy iniciado correctamente!"
echo "═══════════════════════════════════════════════════════════"

