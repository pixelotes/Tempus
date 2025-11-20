from flask_mail import Mail, Message
from flask import current_app, copy_current_request_context
from threading import Thread
import os

# Configuración Flask-Mail
mail = Mail()

def init_mail(app):
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@empresa.com')
    
    mail.init_app(app)


def _send_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"✅ Email enviado en segundo plano a: {msg.recipients}")
        except Exception as e:
            print(f"❌ Error enviando email asíncrono: {e}")


def enviar_email_solicitud(aprobador, solicitante, solicitud):
    # CREAR EL MENSAJE REAL
    msg = Message(
        subject=f'Nueva solicitud de vacaciones de {solicitante.nombre}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[aprobador.email]
    )
    
    msg.body = f'''
    Hola {aprobador.nombre},
    
    {solicitante.nombre} ha solicitado vacaciones:
    
    - Desde: {solicitud.fecha_inicio}
    - Hasta: {solicitud.fecha_fin}
    - Días solicitados: {solicitud.dias_solicitados}
    - Motivo: {solicitud.motivo or 'No especificado'}
    
    Por favor, revisa y responde a esta solicitud en el sistema.
    
    Saludos,
    Sistema de Gestión de Fichajes
    '''
    
    # Enviar en segundo plano
    app = current_app._get_current_object()
    thr = Thread(target=_send_async, args=(app, msg))
    thr.start()

def enviar_email_respuesta(usuario, solicitud):
    estado_texto = "APROBADA" if solicitud.estado == 'aprobada' else "RECHAZADA"
    
    msg = Message(
        subject=f'Tu solicitud de vacaciones ha sido {estado_texto}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[usuario.email]
    )
    
    msg.body = f'''
    Hola {usuario.nombre},
    
    Tu solicitud de vacaciones ha sido {estado_texto}.
    
    Detalles de la solicitud:
    - Desde: {solicitud.fecha_inicio}
    - Hasta: {solicitud.fecha_fin}
    - Días solicitados: {solicitud.dias_solicitados}
    - Estado: {estado_texto}
    - Respondida por: {solicitud.aprobador.nombre if solicitud.aprobador else 'Sistema'}
    - Fecha de respuesta: {solicitud.fecha_respuesta}
    {f"- Comentarios: {solicitud.comentarios}" if solicitud.comentarios else ""}
    
    Saludos,
    Sistema de Gestión de Fichajes
    '''
    
    # Enviar en segundo plano
    app = current_app._get_current_object()
    thr = Thread(target=_send_async, args=(app, msg))
    thr.start()


