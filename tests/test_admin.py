from src.models import TipoAusencia

def test_admin_access_denied_for_employee(auth_client):
    """Verificar que un usuario normal recibe un error o redirect al intentar entrar a /admin/usuarios."""
    response = auth_client.get('/admin/usuarios', follow_redirects=True)
    
    assert response.status_code == 200
    # El decorador admin_required redirige a main.index con un flash
    assert "Acceso denegado" in response.text

def test_admin_access_allowed(auth_admin_client):
    """Verificar que un admin puede entrar."""
    response = auth_admin_client.get('/admin/usuarios')
    assert response.status_code == 200
    # Verificamos contenido de la página de usuarios
    assert "Usuarios" in response.text

def test_crud_tipo_ausencia(auth_admin_client):
    """Testear la creación de un tipo de ausencia."""
    # Crear uno nuevo
    response = auth_admin_client.post('/admin/tipos-ausencia', data={
        'nombre': 'Permiso Paternidad',
        'descripcion': 'Permiso por nacimiento',
        'max_dias': '112', # 16 semanas * 7
        'tipo_dias': 'naturales'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Tipo de ausencia creado" in response.text
    
    # Verificar en BBDD
    tipo = TipoAusencia.query.filter_by(nombre='Permiso Paternidad').first()
    assert tipo is not None
    assert tipo.max_dias == 112
    assert tipo.tipo_dias == 'naturales'
