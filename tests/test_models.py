from src.models import Usuario, Fichaje
from src import db
from werkzeug.security import check_password_hash
from datetime import date, time

def test_usuario_password_hashing(test_app, employee_user):
    """Verificar que el hash de contraseña funciona."""
    # employee_user se crea con password 'emp123' en conftest.py
    assert check_password_hash(employee_user.password, 'emp123')
    assert not check_password_hash(employee_user.password, 'wrongpass')

def test_fichaje_horas_trabajadas_normal(test_app):
    """Caso normal (ej: 9:00 a 17:00). Total 8 horas."""
    fichaje = Fichaje(
        fecha=date(2023, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0),
        pausa=0
    )
    assert fichaje.horas_trabajadas() == 8.0

def test_fichaje_horas_trabajadas_con_pausa(test_app):
    """Caso con pausa (ej: 9:00 a 17:00 con 60 min pausa). Total 7 horas."""
    fichaje = Fichaje(
        fecha=date(2023, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0),
        pausa=60
    )
    assert fichaje.horas_trabajadas() == 7.0

def test_fichaje_horas_trabajadas_nocturno(test_app):
    """Caso nocturno (ej: 22:00 a 06:00 del día siguiente). Total 8 horas."""
    fichaje = Fichaje(
        fecha=date(2023, 1, 1),
        hora_entrada=time(22, 0),
        hora_salida=time(6, 0),
        pausa=0
    )
    assert fichaje.horas_trabajadas() == 8.0

def test_fichaje_defaults(test_app, employee_user):
    """Verificar que al crear un objeto Fichaje se asignan los defaults correctos."""
    fichaje = Fichaje(
        usuario_id=employee_user.id,
        fecha=date(2023, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(17, 0)
    )
    
    db.session.add(fichaje)
    db.session.commit()
    
    assert fichaje.version == 1
    assert fichaje.es_actual is True
    assert fichaje.grupo_id is not None
    assert len(fichaje.grupo_id) > 0
