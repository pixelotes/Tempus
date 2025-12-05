def test_login_success(client, employee_user):
    """Prueba de login con credenciales correctas."""
    response = client.post('/login', data={
        'email': employee_user.email,
        'password': 'emp123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Verificamos el mensaje flash o contenido de la home
    assert "Inicio de sesión exitoso" in response.text

def test_login_failure(client, employee_user):
    """Prueba de login con credenciales incorrectas."""
    response = client.post('/login', data={
        'email': employee_user.email,
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Email o contraseña incorrectos" in response.text

def test_logout(client, auth_client):
    """Verificar que cierra sesión."""
    # auth_client ya está logueado
    response = client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    assert "Sesión cerrada correctamente" in response.text
    
    # Verificar que ya no tenemos acceso
    response = client.get('/fichajes', follow_redirects=True)
    # Debería redirigir al login
    assert "Iniciar Sesión" in response.text or "Login" in response.text

def test_route_protection(client):
    """Intentar acceder a /fichajes sin loguearse."""
    response = client.get('/fichajes', follow_redirects=True)
    
    # Debería redirigir al login
    # Verificamos que estamos en la página de login
    assert "Iniciar Sesión" in response.text or "Login" in response.text
