import pytest
from src import app, db
from src.models import Usuario, TipoAusencia
from werkzeug.security import generate_password_hash

@pytest.fixture
def test_app():
    # Configuración de la app para testing
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # Desactivar CSRF para facilitar los POST
        "SERVER_NAME": "localhost.localdomain"
    })

    # Contexto de la aplicación
    with app.app_context():
        db.create_all()
        # Evitar que el init_db original intente sembrar datos si ya lo hacemos aquí o si no es necesario
        app.db_initialized = True 
        
        # Crear datos semilla básicos si son necesarios para todos los tests
        # (Aunque es mejor tener fixtures específicos)
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(test_app):
    return test_app.test_client()

@pytest.fixture
def runner(test_app):
    return test_app.test_cli_runner()

@pytest.fixture
def admin_user(test_app):
    user = Usuario(
        nombre='Admin Test',
        email='admin@test.com',
        password=generate_password_hash('admin123'),
        rol='admin'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def employee_user(test_app):
    user = Usuario(
        nombre='Employee Test',
        email='employee@test.com',
        password=generate_password_hash('emp123'),
        rol='empleado'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def absence_type(test_app):
    tipo = TipoAusencia(
        nombre='Vacaciones',
        descripcion='Vacaciones anuales',
        max_dias=25,
        tipo_dias='naturales'
    )
    db.session.add(tipo)
    db.session.commit()
    return tipo

@pytest.fixture
def login_as(client):
    """Helper para loguear un usuario dado su email y password."""
    def _login(email, password):
        return client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    return _login

@pytest.fixture
def auth_client(client, employee_user):
    """Cliente pre-logueado como empleado."""
    with client:
        client.post('/login', data={
            'email': employee_user.email,
            'password': 'emp123'
        }, follow_redirects=True)
        yield client

@pytest.fixture
def auth_admin_client(client, admin_user):
    """Cliente pre-logueado como admin."""
    with client:
        client.post('/login', data={
            'email': admin_user.email,
            'password': 'admin123'
        }, follow_redirects=True)
        yield client
