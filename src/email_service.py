from flask_mail import Mail
from flask import current_app
from concurrent.futures import ThreadPoolExecutor
import os
import atexit

# Configuración Flask-Mail
mail = Mail()

# Executor global para gestionar threads de email
# max_workers=3 permite enviar hasta 3 emails simultáneos
email_executor = ThreadPoolExecutor(
    max_workers=3,
    thread_name_prefix='email_worker'
)

def init_mail(app):
    """Inicializa Flask-Mail con configuración de entorno"""
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@empresa.com')
    
    mail.init_app(app)
    
    # Registrar shutdown del executor al cerrar la app
    atexit.register(lambda: email_executor.shutdown(wait=False))


def _send_async(app, msg):
    """
    Función interna que envía email en contexto de app.
    Se ejecuta en thread separado.
    """
    with app.app_context():
        try:
            mail.send(msg)
            print(f"✅ Email enviado: {msg.subject} -> {msg.recipients}")
        except Exception as e:
            print(f"❌ Error enviando email: {e}")


from src.email_utils import send_email_async

def enviar_email_solicitud(aprobadores, solicitante, solicitud):
    """
    Envía email de notificación de nueva solicitud a todos los responsables.
    """
    emails = [a.email for a in aprobadores]
    if not emails:
        return

    es_baja = hasattr(solicitud, 'tipo_ausencia')
    tipo_texto = f"ausencia ({solicitud.tipo_ausencia.nombre if solicitud.tipo_ausencia else 'Ausencia'})" if es_baja else "vacaciones"
    asunto_tipo = "Ausencia/Baja" if es_baja else "Vacaciones"

    context = {
        'solicitante': solicitante,
        'tipo_texto': tipo_texto,
        'solicitud': solicitud,
        'nombres_aprobadores': ', '.join([a.nombre for a in aprobadores])
    }
    
    send_email_async(
        subject=f'Nueva solicitud de {asunto_tipo} de {solicitante.nombre}',
        recipients=emails,
        template_name='solicitud',
        context=context
    )


def enviar_email_respuesta(usuario, solicitud):
    """
    Envía email de notificación de respuesta (aprobación/rechazo).
    """
    estado_texto = "APROBADA" if solicitud.estado == 'aprobada' else "RECHAZADA"
    es_baja = hasattr(solicitud, 'tipo_ausencia')
    tipo_texto = f"ausencia ({solicitud.tipo_ausencia.nombre if solicitud.tipo_ausencia else 'Ausencia'})" if es_baja else "vacaciones"

    context = {
        'usuario': usuario,
        'tipo_texto': tipo_texto,
        'estado_texto': estado_texto,
        'solicitud': solicitud,
        'nombre_aprobador': solicitud.aprobador.nombre if solicitud.aprobador else 'Sistema'
    }
    
    send_email_async(
        subject=f'Tu solicitud de {tipo_texto} ha sido {estado_texto}',
        recipients=[usuario.email],
        template_name='respuesta',
        context=context
    )


def enviar_email_otp(usuario, codigo):
    """
    Envía email con el código OTP para verificación de MFA.
    """
    context = {
        'usuario': usuario,
        'codigo': codigo
    }
    
    send_email_async(
        subject='Código de verificación de seguridad',
        recipients=[usuario.email],
        template_name='otp',
        context=context
    )