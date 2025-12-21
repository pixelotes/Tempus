import pytest
from src.models import Usuario, db, UserKnownIP
from werkzeug.security import check_password_hash

def test_init_admin_command(runner, test_app):
    """Prueba que el comando init-admin crea el usuario correctamente."""
    # Configurar env vars en la app de test
    test_app.config['DEFAULT_ADMIN_EMAIL'] = 'newadmin@test.com'
    test_app.config['DEFAULT_ADMIN_INITIAL_PASSWORD'] = 'secret123'
    
    # 1. Ejecutar comando
    result = runner.invoke(args=['init-admin'])
    assert result.exit_code == 0
    assert "Usuario Administrador creado: newadmin@test.com" in result.output
    
    # 2. Verificar en BD
    with test_app.app_context():
        user = Usuario.query.filter_by(email='newadmin@test.com').first()
        assert user is not None
        assert user.rol == 'admin'
        assert check_password_hash(user.password, 'secret123')

def test_admin_password_warning(client, test_app):
    """Prueba que se muestra el aviso de seguridad si se usa la pass por defecto."""
    from werkzeug.security import generate_password_hash
    
    test_app.config['DEFAULT_ADMIN_INITIAL_PASSWORD'] = 'admin123'
    test_app.config['MFA_ENABLED'] = False
    
    # 1. Crear admin con pass por defecto
    with test_app.app_context():
        admin = Usuario(
            nombre='Admin Security Test',
            email='security@admin.com',
            password=generate_password_hash('admin123'),
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Whitelist IP
        db.session.add(UserKnownIP(usuario_id=admin.id, ip_address='127.0.0.1'))
        db.session.commit()

    # 2. Login
    client.post('/login', data={'email': 'security@admin.com', 'password': 'admin123'}, follow_redirects=True)
    
    # 3. Acceder al index
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert "usando la contrase" in response.data.decode('utf-8')

def test_admin_password_no_warning_after_change(client, test_app):
    """Prueba que el aviso DESAPARECE si se cambia la pass."""
    from werkzeug.security import generate_password_hash
    
    test_app.config['DEFAULT_ADMIN_INITIAL_PASSWORD'] = 'admin123'
    test_app.config['MFA_ENABLED'] = False
    
    # 1. Crear admin con pass DISTINTA a la por defecto
    with test_app.app_context():
        admin = Usuario(
            nombre='Admin Safe Test',
            email='safe@admin.com',
            password=generate_password_hash('changed_password_456'),
            rol='admin'
        )
        db.session.add(admin)
        db.session.commit()
        
        # Whitelist IP
        db.session.add(UserKnownIP(usuario_id=admin.id, ip_address='127.0.0.1'))
        db.session.commit()

    # 2. Login
    client.post('/login', data={'email': 'safe@admin.com', 'password': 'changed_password_456'}, follow_redirects=True)
    
    # 3. Acceder al index
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert "Seguridad: Est\xc3\xa1s usando la contrase\xc3\xb1a de administrador por defecto" not in response.data.decode('utf-8')
