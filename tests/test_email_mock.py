import pytest
from src.email_service import enviar_email_solicitud, enviar_email_respuesta, enviar_email_otp

def test_enviar_email_solicitud_mocked(mocker):
    # Mock the send_email_async function
    mock_send = mocker.patch('src.email_service.send_email_async')
    
    # Mock objects for the function call
    class MockUser:
        def __init__(self, nombre, email):
            self.nombre = nombre
            self.email = email
            
    class MockSolicitud:
        def __init__(self, fecha_inicio, fecha_fin, dias):
            self.fecha_inicio = fecha_inicio
            self.fecha_fin = fecha_fin
            self.dias_solicitados = dias
            self.motivo = "Test"

    aprobador = MockUser("Aprobador", "aprobador@test.com")
    solicitante = MockUser("Solicitante", "solicitante@test.com")
    solicitud = MockSolicitud("2026-07-01", "2026-07-05", 5)
    
    enviar_email_solicitud([aprobador], solicitante, solicitud)
    
    # Assert
    assert mock_send.called
    assert mock_send.call_args.kwargs['template_name'] == 'solicitud'
    assert mock_send.call_args.kwargs['recipients'] == ['aprobador@test.com']

def test_enviar_email_respuesta_mocked(mocker):
    mock_send = mocker.patch('src.email_service.send_email_async')
    
    class MockUser:
        def __init__(self, nombre, email):
            self.nombre = nombre
            self.email = email
            
    class MockSolicitud:
        def __init__(self, estado):
            self.estado = estado
            self.fecha_inicio = "2026-07-01"
            self.fecha_fin = "2026-07-05"
            self.dias_solicitados = 5
            self.aprobador = MockUser("Aprobador", "aprob@test.com")

    usuario = MockUser("User", "user@test.com")
    solicitud = MockSolicitud("aprobada")
    
    enviar_email_respuesta(usuario, solicitud)
    
    assert mock_send.called
    assert mock_send.call_args.kwargs['template_name'] == 'respuesta'

def test_enviar_email_otp_mocked(mocker):
    mock_send = mocker.patch('src.email_service.send_email_async')
    
    class MockUser:
        def __init__(self, nombre, email):
            self.nombre = nombre
            self.email = email
            
    usuario = MockUser("User", "user@test.com")
    
    enviar_email_otp(usuario, "123456")
    
    assert mock_send.called
    assert mock_send.call_args.kwargs['template_name'] == 'otp'
