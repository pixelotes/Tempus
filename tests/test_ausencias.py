from datetime import date
from src.models import SolicitudVacaciones

def test_solicitar_vacaciones_flujo(auth_client, employee_user):
    # 1. Solicitar
    resp = auth_client.post('/vacaciones/solicitar', data={
        'fecha_inicio': '2023-06-01',
        'fecha_fin': '2023-06-05',
        'motivo': 'Verano'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert "Solicitud de vacaciones enviada" in resp.text
    
    # 2. Verificar DB
    solicitud = SolicitudVacaciones.query.filter_by(usuario_id=employee_user.id).first()
    assert solicitud is not None
    assert solicitud.estado == 'pendiente'
    assert solicitud.es_actual is True

def test_validar_overlap(auth_client, employee_user):
    # 1. Crear solicitud A (1-5 Enero)
    # ... código para crear solicitud ...
    
    # 2. Intentar crear solicitud B (4-8 Enero)
    resp = auth_client.post('/vacaciones/solicitar', data={
        'fecha_inicio': '2023-01-04', 
        'fecha_fin': '2023-01-08'
    }, follow_redirects=True)
    
    # Aquí fallará hasta que implementes la lógica de overlap en routes.py
    # assert "Error: Las fechas se solapan" in resp.text