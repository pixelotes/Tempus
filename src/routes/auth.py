from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from flask_dance.contrib.google import google
from flask_dance.consumer import oauth_authorized
from src import google_bp
from src.models import Usuario
from . import auth_bp

from src import limiter

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not google.authorized:
        return False
    
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Error al obtener información de Google", "danger")
        return False
    
    google_info = resp.json()
    email = google_info["email"]
    
    user = Usuario.query.filter_by(email=email).first()
    if user:
        login_user(user)
        flash("Inicio de sesión exitoso con Google", "success")
    else:
        flash("No existe un usuario con este email.", "danger")
        return redirect(url_for("auth.login"))
        
    return redirect(url_for("main.index"))

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  #Límite de 5 intentos por minuto
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 1. Sanitización: quitar espacios en blanco al inicio/final
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        # 2. Validación básica de campos vacíos
        if not email or not password:
            flash('Por favor, introduce email y contraseña.', 'warning')
            return render_template('login.html')

        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('auth.login'))