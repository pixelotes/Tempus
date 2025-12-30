"""Tests for overlapping validation across fichajes, vacaciones, and bajas."""
from datetime import date, time
from src.models import SolicitudVacaciones, SolicitudBaja, Fichaje, TipoAusencia
from src.utils import verificar_solapamiento, verificar_solapamiento_fichaje
from src import db


# =========================================================================
# FICHAJE OVERLAP TESTS
# =========================================================================

def test_fichaje_overlap_detection(test_app, employee_user):
    """Detect overlapping fichaje time slots on the same day."""
    # Create existing fichaje: 9:00 - 13:00
    fichaje = Fichaje(
        usuario_id=employee_user.id,
        fecha=date(2025, 1, 15),
        hora_entrada=time(9, 0),
        hora_salida=time(13, 0),
        es_actual=True
    )
    db.session.add(fichaje)
    db.session.commit()
    
    # Test: Overlapping (10:00 - 14:00)
    hay_solape, msg = verificar_solapamiento_fichaje(
        employee_user.id, date(2025, 1, 15), time(10, 0), time(14, 0)
    )
    assert hay_solape is True, "Should detect overlap with 10-14 slot"
    
    # Test: No overlap (14:00 - 18:00)
    hay_solape, msg = verificar_solapamiento_fichaje(
        employee_user.id, date(2025, 1, 15), time(14, 0), time(18, 0)
    )
    assert hay_solape is False, "Should not detect overlap with 14-18 slot"
    
    # Test: Different day (no overlap)
    hay_solape, msg = verificar_solapamiento_fichaje(
        employee_user.id, date(2025, 1, 16), time(9, 0), time(13, 0)
    )
    assert hay_solape is False, "Should not detect overlap on different day"


def test_fichaje_overlap_allows_edit_own(test_app, employee_user):
    """When editing, shouldn't conflict with itself."""
    fichaje = Fichaje(
        usuario_id=employee_user.id,
        fecha=date(2025, 1, 20),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0),
        es_actual=True
    )
    db.session.add(fichaje)
    db.session.commit()
    
    # Editing same fichaje with overlapping times should not conflict
    hay_solape, msg = verificar_solapamiento_fichaje(
        employee_user.id, date(2025, 1, 20), time(8, 0), time(18, 0),
        excluir_fichaje_id=fichaje.id
    )
    assert hay_solape is False, "Editing own fichaje should not conflict"


# =========================================================================
# VACACIONES + BAJAS CROSS-OVERLAP TESTS
# =========================================================================

def test_vacaciones_overlap_with_existing_baja(test_app, employee_user):
    """Vacation request should detect overlap with existing baja."""
    # Create tipo ausencia
    tipo = TipoAusencia(
        nombre='Baja Test',
        descripcion='For testing',
        max_dias=30,
        tipo_dias='naturales',
        activo=True
    )
    db.session.add(tipo)
    db.session.commit()
    
    # Create existing baja: Jan 10-15
    baja = SolicitudBaja(
        usuario_id=employee_user.id,
        tipo_ausencia_id=tipo.id,
        fecha_inicio=date(2025, 1, 10),
        fecha_fin=date(2025, 1, 15),
        dias_solicitados=6,
        motivo='Test baja',
        estado='aprobada',
        es_actual=True
    )
    db.session.add(baja)
    db.session.commit()
    
    # Try to request vacation that overlaps (Jan 13-20)
    hay_solape, msg = verificar_solapamiento(
        employee_user.id, date(2025, 1, 13), date(2025, 1, 20), tipo='vacaciones'
    )
    
    assert hay_solape is True, "Vacation should detect overlap with baja"
    assert "baja" in msg.lower(), "Message should mention baja"


def test_baja_overlap_with_existing_vacaciones(test_app, employee_user):
    """Baja request should detect overlap with existing vacation."""
    # Create existing vacation: Feb 1-10
    vacaciones = SolicitudVacaciones(
        usuario_id=employee_user.id,
        fecha_inicio=date(2025, 2, 1),
        fecha_fin=date(2025, 2, 10),
        dias_solicitados=7,
        motivo='Test vacation',
        estado='aprobada',
        es_actual=True
    )
    db.session.add(vacaciones)
    db.session.commit()
    
    # Try to request baja that overlaps (Feb 5-15)
    hay_solape, msg = verificar_solapamiento(
        employee_user.id, date(2025, 2, 5), date(2025, 2, 15), tipo='baja'
    )
    
    assert hay_solape is True, "Baja should detect overlap with vacation"
    assert "vacaciones" in msg.lower(), "Message should mention vacaciones"


def test_no_overlap_adjacent_dates(test_app, employee_user):
    """Adjacent but non-overlapping dates should not conflict."""
    # Create vacation: Jan 1-5
    vacaciones = SolicitudVacaciones(
        usuario_id=employee_user.id,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 1, 5),
        dias_solicitados=5,
        motivo='First vacation',
        estado='aprobada',
        es_actual=True
    )
    db.session.add(vacaciones)
    db.session.commit()
    
    # Request adjacent vacation: Jan 6-10 (should NOT overlap)
    hay_solape, msg = verificar_solapamiento(
        employee_user.id, date(2025, 1, 6), date(2025, 1, 10), tipo='vacaciones'
    )
    
    assert hay_solape is False, "Adjacent dates should not overlap"


def test_cancelled_vacaciones_dont_cause_overlap(test_app, employee_user):
    """Cancelled/rejected vacations should not block new requests."""
    # Create rejected vacation
    vacaciones = SolicitudVacaciones(
        usuario_id=employee_user.id,
        fecha_inicio=date(2025, 3, 1),
        fecha_fin=date(2025, 3, 10),
        dias_solicitados=7,
        motivo='Rejected vacation',
        estado='rechazada',  # Rejected!
        es_actual=True
    )
    db.session.add(vacaciones)
    db.session.commit()
    
    # Request same dates (should NOT overlap because original was rejected)
    hay_solape, msg = verificar_solapamiento(
        employee_user.id, date(2025, 3, 1), date(2025, 3, 10), tipo='vacaciones'
    )
    
    assert hay_solape is False, "Rejected vacations should not block new requests"
