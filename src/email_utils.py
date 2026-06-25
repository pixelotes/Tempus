from flask import render_template
from flask_mail import Message
from src.email_service import mail, email_executor, _send_async
from flask import current_app

def send_email_async(subject, recipients, template_name, context):
    """
    Renderiza templates Jinja2 y envía un email de forma asíncrona.
    """
    # Renderizar templates
    body = render_template(f'emails/{template_name}.txt', **context)
    html = render_template(f'emails/{template_name}.html', **context)
    
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=recipients,
        body=body,
        html=html
    )
    
    app = current_app._get_current_object()
    future = email_executor.submit(_send_async, app, msg)
    
    def handle_email_result(fut):
        try:
            fut.result()
        except Exception as e:
            print(f"⚠️ Email callback error: {e}")
    
    future.add_done_callback(handle_email_result)
