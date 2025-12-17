# Crear script de test: test_performance.py
from src import app, db
from src.models import Usuario, Fichaje
from datetime import date, time, datetime
import time as timer

with app.app_context():
    # Asegurar que las tablas existan
    db.create_all()
    
    # Crear datos de prueba si no existen
    usuario = Usuario.query.first()
    if not usuario:
        from werkzeug.security import generate_password_hash
        usuario = Usuario(
            nombre='Admin Test',
            email='admin@test.com',
            password=generate_password_hash('admin123'),
            rol='admin',
            dias_vacaciones=25
        )
        db.session.add(usuario)
        db.session.commit()
    
    if Fichaje.query.count() < 100:
        print("Generando 100 fichajes de prueba...")
        for i in range(100):
            f = Fichaje(
                usuario_id=usuario.id,
                editor_id=usuario.id,
                grupo_id=f"test-{i}",
                fecha=date(2024, 12, i % 28 + 1),
                hora_entrada=time(9, 0),
                hora_salida=time(18, 0),
                pausa=60,
                version=1,
                es_actual=True,
                tipo_accion='creacion'
            )
            db.session.add(f)
        db.session.commit()
    
    # Test
    print("\n🔬 Testeando performance del admin_resumen...")
    start = timer.time()
    
    with app.test_client() as client:
        # Login como admin
        with client.session_transaction() as sess:
            admin_user = Usuario.query.filter_by(rol='admin').first()
            if admin_user:
                 sess['_user_id'] = admin_user.id
            else:
                 print("⚠️ No admin user found. Please create one.")
                 exit(1)
        
        response = client.get('/admin/resumen')
        
    elapsed = timer.time() - start
    print(f"⏱️  Tiempo de respuesta: {elapsed:.3f}s")
    print(f"📊 Status code: {response.status_code}")
    
    if elapsed < 2:
        print("✅ PERFORMANCE EXCELENTE")
    elif elapsed < 5:
        print("⚠️  PERFORMANCE ACEPTABLE")
    else:
        print("❌ PERFORMANCE POBRE")
