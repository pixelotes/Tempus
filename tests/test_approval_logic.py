import pytest
from unittest.mock import patch
from datetime import date, timedelta
from src.models import Usuario, SolicitudVacaciones, SolicitudBaja, TipoAusencia, SaldoVacaciones
from src import db

# We use the fixtures from conftest.py to ensure DB is populated
@pytest.fixture
def logic_data(test_app, admin_user, employee_user, approver_user, absence_type):
    """
    Returns IDs to avoid DetachedInstanceError.
    Data is guaranteed to exist because we requested the fixtures.
    """
    return {
        'admin_id': admin_user.id,
        'employee_id': employee_user.id,
        'approver_id': approver_user.id,
        'tipo_id': absence_type.id
    }

@patch("src.email_service.enviar_email_respuesta")
@patch("src.routes.ausencias.crear_evento_baja")
def test_approve_reject_baja(mock_calendar, mock_email, auth_admin_client, logic_data, test_app):
    mock_calendar.return_value = "evt_baja_mock"
    admin_id = logic_data['admin_id']
    employee_id = logic_data['employee_id']
    tipo_id = logic_data['tipo_id']
    
    with test_app.app_context():
        # Create Pending Baja
        sol = SolicitudBaja(
            usuario_id=employee_id,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_solicitados=1,
            motivo="Prueba Baja",
            estado="pendiente",
            tipo_ausencia_id=tipo_id,
            es_actual=True
        )
        db.session.add(sol)
        db.session.commit()
        sol_id = sol.id
        
    # Act: Approve
    resp = auth_admin_client.post(f'/aprobaciones/bajas/{sol_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    assert b"aprobada" in resp.data.lower()
    mock_calendar.assert_called_once()
    
    with test_app.app_context():
        sol = SolicitudBaja.query.get(sol_id)
        assert sol.estado == 'aprobada'

    # Create another for Rejection
    with test_app.app_context():
        sol_rej = SolicitudBaja(
            usuario_id=employee_id,
            fecha_inicio=date.today() + timedelta(days=2),
            fecha_fin=date.today() + timedelta(days=2),
            dias_solicitados=1,
            motivo="Prueba Rechazo",
            estado="pendiente",
            tipo_ausencia_id=tipo_id,
            es_actual=True
        )
        db.session.add(sol_rej)
        db.session.commit()
        rej_id = sol_rej.id
        
    # Act: Reject
    resp = auth_admin_client.post(f'/aprobaciones/bajas/{rej_id}/rechazar', follow_redirects=True)
    assert resp.status_code == 200
    assert b"rechazada" in resp.data.lower()
    
    with test_app.app_context():
        sol = SolicitudBaja.query.get(rej_id)
        assert sol.estado == 'rechazada'

@patch("src.email_service.enviar_email_respuesta") 
@patch("src.routes.ausencias.eliminar_evento")
@patch("src.routes.ausencias.crear_evento_vacaciones")
def test_approve_modification(mock_create, mock_delete, mock_email, auth_admin_client, logic_data, test_app):
    mock_create.return_value = "evt_new_mock"
    mock_delete.return_value = True
    employee_id = logic_data['employee_id']
    
    with test_app.app_context():
        # Setup Saldo
        saldo = SaldoVacaciones(usuario_id=employee_id, anio=date.today().year, dias_disfrutados=0, dias_totales=25)
        db.session.add(saldo)
        
        # v1 Approved
        v1 = SolicitudVacaciones(
            usuario_id=employee_id,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_solicitados=1,
            estado="aprobada",
            es_actual=True,
            grupo_id="grp_mod",
            version=1,
            google_event_id="evt_old"
        )
        db.session.add(v1)
        db.session.commit()
        
        # v2 Pending Modification
        v2 = SolicitudVacaciones(
            usuario_id=employee_id,
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=5), 
            dias_solicitados=1,
            estado="pendiente",
            es_actual=True, # In logic often new request starts as actual, old one stays actual until approved change
            grupo_id="grp_mod",
            version=2,
            tipo_accion="modificacion"
        )
        db.session.add(v2)
        db.session.commit()
        v2_id = v2.id
        
    # Act: Approve Modification
    resp = auth_admin_client.post(f'/aprobaciones/vacaciones/{v2_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    
    # Assert
    mock_delete.assert_called_once()
    mock_create.assert_called_once()
    
    with test_app.app_context():
        v1_db = SolicitudVacaciones.query.filter_by(grupo_id="grp_mod", version=1).first()
        v2_db = SolicitudVacaciones.query.get(v2_id)
        
        assert v1_db.es_actual is False
        assert v2_db.es_actual is True
        assert v2_db.estado == "aprobada"

def test_permission_denied(auth_client, logic_data, test_app):
    """Employee trying to access approval routes."""
    employee_id = logic_data['employee_id']
    
    with test_app.app_context():
        sol = SolicitudVacaciones(
            usuario_id=employee_id,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_solicitados=1,
            estado="pendiente",
            grupo_id="grp_perm",
            version=1,
            tipo_accion="creacion"
        )
        db.session.add(sol)
        db.session.commit()
        sol_id = sol.id
        
    # Act: Employee triggers approval URL
    resp = auth_client.post(f'/aprobaciones/vacaciones/{sol_id}/aprobar', follow_redirects=True)
    
    # Assert: Should be redirected or denied
    assert resp.status_code == 200 
    assert b"No tienes permisos" in resp.data or b"Acceso denegado" in resp.data or b"Redirecting" in resp.data

@patch("src.email_service.enviar_email_respuesta")
@patch("src.routes.ausencias.eliminar_evento")
def test_approve_cancellation(mock_delete, mock_email, auth_admin_client, logic_data, test_app):
    employee_id = logic_data['employee_id']
    
    with test_app.app_context():
         # v1 Approved
        v1 = SolicitudVacaciones(
            usuario_id=employee_id,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_solicitados=1,
            estado="aprobada",
            es_actual=True,
            grupo_id="grp_cancel",
            version=1,
            google_event_id="evt_cancel"
        )
        db.session.add(v1)
        db.session.commit()
        
        # v2 Pending Cancellation
        v2 = SolicitudVacaciones(
            usuario_id=employee_id,
            fecha_inicio=v1.fecha_inicio,
            fecha_fin=v1.fecha_fin,
            dias_solicitados=1,
            estado="pendiente",
            es_actual=True,
            grupo_id="grp_cancel",
            version=2,
            tipo_accion="cancelacion"
        )
        db.session.add(v2)
        db.session.commit()
        v2_id = v2.id
        
    # Act: Approve Cancellation
    resp = auth_admin_client.post(f'/aprobaciones/vacaciones/{v2_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    
    mock_delete.assert_called_once()
    
    with test_app.app_context():
        v2_db = SolicitudVacaciones.query.get(v2_id)
        assert v2_db.estado == "aprobada"
