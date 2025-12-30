from datetime import date
from src.utils import calcular_dias_habiles, verificar_solapamiento, decimal_to_human, verificar_solapamiento_fichaje, simular_modificacion_vacaciones
from src.models import Festivo, SolicitudVacaciones, Fichaje, SaldoVacaciones
from src import db
from unittest.mock import MagicMock
from datetime import time

def test_calcular_dias_habiles_simple(test_app):
    """Semana normal lunes-viernes."""
    inicio = date(2023, 1, 2) # Lunes
    fin = date(2023, 1, 6)    # Viernes
    assert calcular_dias_habiles(inicio, fin) == 5

def test_calcular_dias_con_finde(test_app):
    """Semana completa (7 días naturales -> 5 hábiles)."""
    inicio = date(2023, 1, 2) # Lunes
    fin = date(2023, 1, 8)    # Domingo
    assert calcular_dias_habiles(inicio, fin) == 5

def test_calcular_dias_con_festivo(test_app):
    """Semana con un festivo entre medias."""
    from src.utils import invalidar_cache_festivos
    
    # Crear festivo el Miércoles (must be activo=True to be counted)
    festivo = Festivo(fecha=date(2023, 1, 4), descripcion="Festivo Test", activo=True)
    db.session.add(festivo)
    db.session.commit()
    
    # Invalidate festivos cache so the new festivo is picked up
    invalidar_cache_festivos()
    
    inicio = date(2023, 1, 2) # Lunes
    fin = date(2023, 1, 6)    # Viernes
    # L(1) M(1) X(0) J(1) V(1) = 4 días
    assert calcular_dias_habiles(inicio, fin) == 4

def test_verificar_solapamiento_limpio(test_app, employee_user):
    """No hay solapamiento si no hay solicitudes."""
    hay_solape, msg = verificar_solapamiento(employee_user.id, date(2023, 1, 1), date(2023, 1, 5))
    assert hay_solape is False
    assert msg is None

def test_verificar_solapamiento_detectado(test_app, employee_user):
    """Detectar choque con solicitud existente."""
    # 1. Crear solicitud base (1-5 Enero)
    sol = SolicitudVacaciones(
        usuario_id=employee_user.id,
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2023, 1, 5),
        dias_solicitados=5,
        motivo="Test",
        estado="pendiente"
    )
    db.session.add(sol)
    db.session.commit()
    
    # 2. Probar Overlap Total (mismas fechas)
    hay_solape, _ = verificar_solapamiento(employee_user.id, date(2023, 1, 1), date(2023, 1, 5))
    assert hay_solape is True
    
    # 3. Probar Overlap Parcial (3-7 Enero)
    hay_solape, _ = verificar_solapamiento(employee_user.id, date(2023, 1, 3), date(2023, 1, 7))
    assert hay_solape is True
    
    # 4. Probar Sin Overlap (6-10 Enero)
    hay_solape, _ = verificar_solapamiento(employee_user.id, date(2023, 1, 6), date(2023, 1, 10))
    assert hay_solape is False

def test_decimal_to_human():
    assert decimal_to_human(8.5) == "08:30"
    assert decimal_to_human(8.0) == "08:00"
    assert decimal_to_human(0) == "00:00"
    assert decimal_to_human(None) == "00:00"
    assert decimal_to_human(10.25) == "10:15"

def test_verificar_solapamiento_fichaje(test_app, employee_user):
    
    fecha = date(2023, 5, 1)
    
    # 1. Crear fichaje existente (09:00 - 13:00)
    with test_app.app_context():
        f = Fichaje(
            usuario_id=employee_user.id,
            fecha=fecha,
            hora_entrada=time(9, 0),
            hora_salida=time(13, 0),
            es_actual=True,
            grupo_id="grp_fich_1"
        )
        db.session.add(f)
        db.session.commit()
        f_id = f.id

    # 2. Test Solapamiento Total (mismo horario)
    hay, msg = verificar_solapamiento_fichaje(employee_user.id, fecha, time(9, 0), time(13, 0))
    assert hay is True
    
    # 3. Test Solapamiento Parcial (12:00 - 14:00)
    hay, msg = verificar_solapamiento_fichaje(employee_user.id, fecha, time(12, 0), time(14, 0))
    assert hay is True
    
    # 4. Test Sin Solape (After)
    hay, msg = verificar_solapamiento_fichaje(employee_user.id, fecha, time(13, 0), time(14, 0))
    assert hay is False
    
    # 5. Test Exclusión (Editando el mismo fichaje)
    hay, msg = verificar_solapamiento_fichaje(employee_user.id, fecha, time(9, 0), time(13, 0), excluir_fichaje_id=f_id)
    assert hay is False

def test_simular_modificacion_vacaciones(test_app, employee_user):
    
    with test_app.app_context():
        # Setup Saldo: 25 totales, 0 disfrutados
        saldo = SaldoVacaciones(usuario_id=employee_user.id, anio=2023, dias_totales=25, dias_disfrutados=0)
        db.session.add(saldo)
        
        # Setup Original Request (Approved): 5 days
        orig = SolicitudVacaciones(
            usuario_id=employee_user.id,
            fecha_inicio=date(2023, 6, 5), # Mon
            fecha_fin=date(2023, 6, 9),    # Fri
            dias_solicitados=5,
            estado="aprobada",
            es_actual=True
        )
        db.session.add(orig)
        db.session.commit()
        orig_id = orig.id
        
        # Test Case 1: Reducing days (3 days: 5-7 June)
        # Old: 5 (5-9 June). New: 3 (5-7 June). Diff: 3 - 5 = -2.
        res = simular_modificacion_vacaciones(employee_user.id, orig_id, date(2023, 6, 5), date(2023, 6, 7))
        
        assert res['valido'] is True
        assert res['dias_diff'] == -2
        assert res['es_adelanto'] is False
        
        # Test Case 2: Extending days (7 days: 5-13 June?) 
        # 5-9 June (5 days). 10-11 (Sat/Sun). 12-13 (Mon/Tue). Total 7 days.
        
        res = simular_modificacion_vacaciones(employee_user.id, orig_id, date(2023, 6, 5), date(2023, 6, 13))
        assert res['valido'] is True
        assert res['dias_diff'] == 7 - 5
        
def test_verificar_solapamiento_in_memory(test_app):
    
    # Mock SolicitudVacaciones object
    vac = MagicMock()
    vac.usuario_id = 1
    vac.es_actual = True
    vac.tipo_accion = 'creacion'
    vac.estado = 'aprobada'
    vac.fecha_inicio = date(2023, 1, 1)
    vac.fecha_fin = date(2023, 1, 5)
    
    cached_list = [vac]
    
    # Test Overlap with Cached list
    # Even in memory checks might access global objects/lazy loads if not prevented, or utils logic accesses something.
    # Actually, verification logic 108 accesses vac.grupo_id.
    vac.grupo_id = "grp_mock" 
    
    with test_app.app_context():
        hay, _ = verificar_solapamiento(1, date(2023, 1, 3), date(2023, 1, 6), cached_vacaciones=cached_list)
        assert hay is True
        
        # Test No Overlap
        hay, _ = verificar_solapamiento(1, date(2023, 1, 6), date(2023, 1, 10), cached_vacaciones=cached_list)
        assert hay is False