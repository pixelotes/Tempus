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


# --- TESTS DE ARCHIVADO LÓGICO DE USUARIOS ---

def test_archivar_usuario_soft_delete(auth_admin_client, employee_user):
    """Verificar que archivar usuario no elimina registros históricos."""
    from src.models import Usuario
    
    # Archivar usuario
    response = auth_admin_client.post(
        f'/admin/usuarios/eliminar/{employee_user.id}',
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Usuario archivado correctamente" in response.text
    
    # Verificar que usuario sigue en DB pero inactivo
    usuario = Usuario.query.get(employee_user.id)
    assert usuario is not None
    assert usuario.activo is False


def test_usuario_archivado_no_aparece_en_lista(auth_admin_client, employee_user):
    """Verificar que usuarios archivados no aparecen en la lista."""
    from src.models import Usuario
    from src import db
    
    # Archivar
    employee_user.activo = False
    db.session.commit()
    
    # Verificar que no aparece en lista
    response = auth_admin_client.get('/admin/usuarios')
    assert response.status_code == 200
    assert employee_user.nombre not in response.text


def test_usuario_archivado_no_aparece_en_busqueda(auth_admin_client, employee_user):
    """Verificar que usuarios archivados no aparecen en búsqueda AJAX."""
    from src.models import Usuario
    from src import db
    
    # Archivar
    employee_user.activo = False
    db.session.commit()
    
    # Verificar que no aparece en búsqueda
    response = auth_admin_client.get(f'/admin/api/usuarios/buscar?q={employee_user.nombre[:5]}')
    assert response.status_code == 200
    data = response.get_json()
    assert not any(employee_user.email in r['text'] for r in data.get('results', []))
