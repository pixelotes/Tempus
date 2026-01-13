#!/bin/sh
# entrypoint.sh

# 1. Detener el script si ocurre algún error
set -e

echo "🚀 Iniciando script de arranque (Entrypoint)..."

# 2. (Opcional) Esperar a que la base de datos esté lista
# Si usas PostgreSQL, a veces el contenedor de la app arranca antes que la DB.
# Herramientas como 'wait-for-it' o un bucle simple pueden ayudar, 
# pero Flask suele reintentar o fallar rápido y Kubernetes reinicia el pod.
# Por ahora, confiamos en el 'depends_on' de Docker Compose o la política de reinicio.

# 3. Inicializar Migraciones (SOLO SI NO EXISTEN)
# ATENCIÓN: En producción, lo ideal es que la carpeta 'migrations' venga en el código (git).
# Pero para facilitar el primer despliegue si no la tienes, podemos poner este bloque de seguridad:
if [ ! -d "migrations" ]; then
    echo "⚠️  No se encontró carpeta de migraciones. Inicializando..."
    flask db init
    # Generar la primera migración automáticamente (CUIDADO: Revisar en producción)
    flask db migrate -m "Migración inicial automática al arrancar"
fi

# 4. Aplicar Migraciones pendientes
echo "🔄 Aplicando migraciones de base de datos..."
flask db upgrade

# 5. Inicializar o asegurar el Usuario Admin
# Usamos el comando CLI que ya tienes en src/cli.py
echo "👤 Asegurando existencia de usuario administrador..."
flask init-admin

# 6. Ejecutar el comando principal del contenedor
# 'exec' reemplaza el proceso actual (shell) por el comando final (gunicorn)
# Esto es vital para que las señales de parada (SIGTERM) lleguen a la app.
echo "✅ Todo listo. Arrancando servidor..."
exec "$@"