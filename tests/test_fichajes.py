from src.models import Fichaje
from src import db
from datetime import date, time

def test_crear_fichaje(auth_client, employee_user):
    """Crear: POST a /fichajes/crear y verificar que se guarda en BBDD."""
    response = auth_client.post('/fichajes/crear', data={
        'fecha': '2023-01-01',
        'hora_entrada': '09:00',
        'hora_salida': '17:00',
        'pausa': '60'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Fichaje registrado correctamente" in response.text
    
    # Verificar BBDD
    fichaje = Fichaje.query.filter_by(usuario_id=employee_user.id).first()
    assert fichaje is not None
    assert fichaje.fecha == date(2023, 1, 1)
    assert fichaje.hora_entrada == time(9, 0)
    assert fichaje.pausa == 60
    assert fichaje.es_actual is True
    assert fichaje.version == 1

def test_editar_fichaje_inmutabilidad(auth_client, employee_user):
    """Editar (Inmutabilidad): Verificar versionado y grupo_id."""
    # Setup: Crear fichaje inicial
    fichaje = Fichaje(
        usuario_id=employee_user.id,
        fecha=date(2023, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0),
        pausa=0
    )
    db.session.add(fichaje)
    db.session.commit()
    
    # Acción: Editar
    response = auth_client.post(f'/fichajes/editar/{fichaje.id}', data={
        'fecha': '2023-01-01',
        'hora_entrada': '10:00', # Cambio
        'hora_salida': '18:00',
        'pausa': '30',
        'motivo': 'Corrección horaria'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Fichaje rectificado correctamente" in response.text
    
    # Verificaciones
    # 1. El registro original pasa a es_actual=False
    old_fichaje = Fichaje.query.get(fichaje.id)
    assert old_fichaje.es_actual is False
    
    # 2. Se crea uno nuevo con version=2 y es_actual=True
    new_fichaje = Fichaje.query.filter_by(
        usuario_id=employee_user.id, 
        es_actual=True
    ).first()
    
    assert new_fichaje is not None
    assert new_fichaje.id != old_fichaje.id
    assert new_fichaje.version == 2
    assert new_fichaje.hora_entrada == time(10, 0)
    
    # 3. Ambos comparten el mismo grupo_id
    assert new_fichaje.grupo_id == old_fichaje.grupo_id

def test_eliminar_fichaje_soft_delete(auth_client, employee_user):
    """Eliminar (Soft Delete): Verificar creación de registro 'eliminacion'."""
    # Setup
    fichaje = Fichaje(
        usuario_id=employee_user.id,
        fecha=date(2023, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0)
    )
    db.session.add(fichaje)
    db.session.commit()
    
    # Acción: Eliminar
    response = auth_client.post(f'/fichajes/eliminar/{fichaje.id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert "Fichaje eliminado correctamente" in response.text
    
    # Verificaciones
    old_fichaje = Fichaje.query.get(fichaje.id)
    assert old_fichaje.es_actual is False
    
    # Verificar que se crea un registro con tipo_accion='eliminacion'
    tombstone = Fichaje.query.filter_by(
        usuario_id=employee_user.id,
        es_actual=True,
        tipo_accion='eliminacion'
    ).first()
    
    assert tombstone is not None
    assert tombstone.grupo_id == old_fichaje.grupo_id
