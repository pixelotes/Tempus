"""
Test para verificar que los años en los dropdowns son dinámicos
"""
from datetime import datetime


def test_anios_dinamicos_resumen_vacaciones(client, admin_user):
    """Verifica que el dropdown de años en Resumen Vacaciones es dinámico"""
    # Login como admin
    client.post('/login', data={
        'email': admin_user.email,
        'password': 'admin123'
    })
    
    # Acceder a la página de resumen
    response = client.get('/admin/resumen')
    assert response.status_code == 200
    
    # Verificar que el año actual del servidor está en la respuesta
    anio_actual = datetime.now().year
    assert str(anio_actual).encode() in response.data
    
    # Verificar que los 4 años anteriores también están
    for i in range(1, 5):
        anio = anio_actual - i
        assert str(anio).encode() in response.data
    
    # Verificar que NO hay años hardcodeados fuera del rango
    # (esto fallaría si todavía estuviera hardcodeado 2023-2026)
    if anio_actual > 2026:
        assert b'2023' not in response.data


def test_anios_dinamicos_resumen_fichajes(client, admin_user):
    """Verifica que el dropdown de años en Resumen Fichajes es dinámico"""
    # Login como admin
    client.post('/login', data={
        'email': admin_user.email,
        'password': 'admin123'
    })
    
    # Acceder a la página de fichajes admin
    response = client.get('/admin/admin_fichajes')
    assert response.status_code == 200
    
    # Verificar que el año actual del servidor está en la respuesta
    anio_actual = datetime.now().year
    assert str(anio_actual).encode() in response.data
    
    # Verificar que los 4 años anteriores también están
    for i in range(1, 5):
        anio = anio_actual - i
        assert str(anio).encode() in response.data
