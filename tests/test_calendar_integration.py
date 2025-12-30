import pytest
from unittest.mock import patch
from datetime import date, timedelta
from src.models import Usuario, SolicitudVacaciones, SaldoVacaciones, TipoAusencia, SolicitudBaja
from src import db
import json

@patch("src.routes.ausencias.crear_evento_vacaciones")
def test_aprobar_vacaciones_triggers_calendar(mock_crear_evento, auth_admin_client, test_app):
    """Test that approving a vacation request triggers calendar event creation."""
    mock_crear_evento.return_value = "evt_google_id"
    
    with test_app.app_context():
        # 1. Update Admin to have Calendar enabled
        admin = Usuario.query.filter_by(email="admin@test.com").first()
        admin.google_token = json.dumps({"token": "mock"})
        admin.google_calendar_enabled = True
        
        # 2. Create Saldo
        saldo = SaldoVacaciones(usuario_id=admin.id, anio=date.today().year, dias_disfrutados=0)
        db.session.add(saldo)
        
        # 3. Create Pending Request
        sol = SolicitudVacaciones(
            usuario=admin,
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=2),
            dias_solicitados=2,
            motivo="Test Calendar",
            estado="pendiente",
            es_actual=True,
            tipo_accion="creacion",
            grupo_id="grp_1",
            version=1,
            # Approver can be self for admin, or irrelevant if we just call the endpoint as admin
        )
        db.session.add(sol)
        db.session.commit()
        sol_id = sol.id

    # Post approval
    resp = auth_admin_client.post(f'/aprobaciones/vacaciones/{sol_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    
    # Verify mock called
    mock_crear_evento.assert_called_once()
    
    # Verify DB update
    with test_app.app_context():
        sol = SolicitudVacaciones.query.get(sol_id)
        assert sol.estado == 'aprobada'
        assert sol.google_event_id == "evt_google_id"

@patch("src.routes.ausencias.crear_evento_baja")
def test_aprobar_baja_triggers_calendar(mock_crear_evento, auth_admin_client, test_app):
    """Test that approving a leave request triggers calendar event creation."""
    mock_crear_evento.return_value = "evt_baja_google_id"
    
    with test_app.app_context():
        admin = Usuario.query.filter_by(email="admin@test.com").first()
        admin.google_token = json.dumps({"token": "mock"})
        admin.google_calendar_enabled = True
        
        tipo = TipoAusencia.query.first() 
        if not tipo:
             tipo = TipoAusencia(nombre="TestType")
             db.session.add(tipo)
        
        sol = SolicitudBaja(
            usuario=admin,
            fecha_inicio=date.today() + timedelta(days=5),
            fecha_fin=date.today() + timedelta(days=6),
            dias_solicitados=2,
            motivo="Test Baja Calendar",
            estado="pendiente",
            es_actual=True,
            grupo_id="grp_baja_1",
            version=1,
            tipo_ausencia=tipo
        )
        db.session.add(sol)
        db.session.commit()
        sol_id = sol.id

    # Post approval
    resp = auth_admin_client.post(f'/aprobaciones/bajas/{sol_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    
    # Verify mock called
    mock_crear_evento.assert_called_once()
    
    # Verify DB update
    with test_app.app_context():
        sol = SolicitudBaja.query.get(sol_id)
        assert sol.estado == 'aprobada'
        assert sol.google_event_id == "evt_baja_google_id"

@patch("src.routes.ausencias.eliminar_evento")
@patch("src.routes.ausencias.crear_evento_vacaciones")
def test_modificar_vacaciones_triggers_calendar(mock_crear, mock_eliminar, auth_admin_client, test_app):
    """Test that modification (approve v2) deletes old event and creates new one."""
    mock_crear.return_value = "evt_new_id"
    mock_eliminar.return_value = True
    
    with test_app.app_context():
        admin = Usuario.query.filter_by(email="admin@test.com").first()
        admin.google_token = json.dumps({"token": "mock"})
        admin.google_calendar_enabled = True
        
        # Original (v1) - Approved with event
        v1 = SolicitudVacaciones(
            usuario=admin,
            fecha_inicio=date.today(),
            fecha_fin=date.today(),
            dias_solicitados=1,
            estado="aprobada",
            es_actual=True,
            tipo_accion="creacion",
            grupo_id="grp_mod_1",
            version=1,
            google_event_id="evt_old_id"
        )
        db.session.add(v1)
        db.session.commit()
        
        # New Request (v2) - Pending Modification
        v2 = SolicitudVacaciones(
            usuario=admin,
            fecha_inicio=date.today() + timedelta(days=1),
            fecha_fin=date.today() + timedelta(days=1),
            dias_solicitados=1,
            estado="pendiente",
            es_actual=True,
            tipo_accion="modificacion",
            grupo_id="grp_mod_1",
            version=2
        )
        db.session.add(v2)
        db.session.commit()
        v2_id = v2.id

    # Approve v2
    resp = auth_admin_client.post(f'/aprobaciones/vacaciones/{v2_id}/aprobar', follow_redirects=True)
    assert resp.status_code == 200
    
    # Verify mocks
    mock_eliminar.assert_called_once() # Should delete evt_old_id
    mock_crear.assert_called_once()    # Should create for v2
    
    # Verify DB
    with test_app.app_context():
        v2_reload = SolicitudVacaciones.query.get(v2_id)
        assert v2_reload.google_event_id == "evt_new_id"
        assert v2_reload.estado == "aprobada"
