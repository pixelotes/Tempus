# Scripts

Scripts auxiliares de Tempus para tareas que se ejecutan fuera de la aplicación web (autenticación de Google Calendar y exportación de datos para recuperación ante desastres).

## Contenido

| Script | Descripción |
|--------|-------------|
| [authenticate_calendar.py](authenticate_calendar.py) | Genera las credenciales OAuth de Google Calendar para desarrollo local. |
| [tempus_bcdr_export.py](tempus_bcdr_export.py) | Exporta todos los datos de la base de datos a ficheros Excel (BCDR / backup). |

> `__init__.py` solo existe para que `scripts` sea un paquete Python; no contiene lógica.

---

## authenticate_calendar.py

Ejecuta el flujo de autenticación OAuth de Google y guarda el token resultante en `token.pickle`. **Solo es necesario si NO usas una Service Account** (típicamente, para desarrollo local).

### Requisitos

```bash
pip install google-auth-oauthlib google-auth
```

Además necesitas un fichero `credentials.json` descargado desde la
[consola de Google Cloud](https://console.cloud.google.com/apis/credentials)
(tipo de credencial: *OAuth client ID*). Debe estar en el directorio desde el que ejecutes el script.

### Uso

```bash
python scripts/authenticate_calendar.py
```

- Si ya existe `token.pickle` válido, no hace nada.
- Si el token está caducado pero es renovable, lo refresca automáticamente.
- En caso contrario, abre el navegador para iniciar sesión y genera un nuevo `token.pickle`.

El ámbito (scope) solicitado es `https://www.googleapis.com/auth/calendar.events`.

---

## tempus_bcdr_export.py

Script independiente para extraer **todos** los datos de la base de datos de Tempus y generar un fichero Excel (`.xlsx`) por usuario, pensado como mecanismo de continuidad de negocio / recuperación ante desastres (BCDR).

Cada fichero generado contiene dos pestañas:

- **Fichajes**: registros de entrada/salida, pausas, horas trabajadas y rectificaciones.
- **Vacaciones y Ausencias**: saldo de vacaciones por año, solicitudes de vacaciones y solicitudes de bajas/ausencias.

### Requisitos

```bash
pip install psycopg2-binary openpyxl
```

### Uso

```bash
# Conexión con valores por defecto (o variables de entorno POSTGRES_*)
python scripts/tempus_bcdr_export.py

# Especificar directorio de salida
python scripts/tempus_bcdr_export.py --output /backups/tempus

# Especificar parámetros de conexión manualmente
python scripts/tempus_bcdr_export.py \
    --host localhost --port 5432 \
    --db fichador_db --user fichador_user --password fichador_pass

# Incluir también usuarios inactivos
python scripts/tempus_bcdr_export.py --all
```

### Argumentos

| Argumento | Por defecto | Descripción |
|-----------|-------------|-------------|
| `--host` | `$POSTGRES_HOST` o `localhost` | Host de PostgreSQL. |
| `--port` | `$POSTGRES_PORT` o `5432` | Puerto de PostgreSQL. |
| `--db` | `$POSTGRES_DB` o `fichador_db` | Nombre de la base de datos. |
| `--user` | `$POSTGRES_USER` o `fichador_user` | Usuario de la base de datos. |
| `--password` | `$POSTGRES_PASSWORD` o `fichador_pass` | Contraseña de la base de datos. |
| `--output`, `-o` | `bcdr_export_YYYYMMDD_HHMM/` | Directorio de salida. |
| `--all` | (desactivado) | Incluye también a los usuarios inactivos. |

### Salida

Se crea un directorio con un fichero `<nombre_usuario>.xlsx` por cada usuario exportado. Si no se indica `--output`, el directorio se nombra con la marca de tiempo de la exportación (`bcdr_export_YYYYMMDD_HHMM/`).
