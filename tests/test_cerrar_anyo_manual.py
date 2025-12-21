"""
Test script for cerrar-anio (close year) functionality.

This script sets up test data and runs the year closing command with:
- 3 users with varying vacation days remaining (2, 7, -2)
- 3 festivos for 2024
- Max carryover of 3 days

Expected results after closing 2024:
- All 2024 festivos should be disabled (activo=False)
- User vacations reset to 25 + min(remaining, 3):
  - User with 2 days remaining → 25 + 2 = 27 days
  - User with 7 days remaining → 25 + 3 (capped) = 28 days
  - User with -2 days remaining → 25 + (-2) = 23 days (debt carries fully)
"""

import os
import sys

# Add project root to path (parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from src import app, db
from src.models import Usuario, SaldoVacaciones, Festivo
from src.cli import cerrar_anio_command
from werkzeug.security import generate_password_hash
from click.testing import CliRunner


def setup_test_data():
    """Create test users, saldos, and festivos for 2024."""
    
    print("\n" + "=" * 70)
    print("  SETUP: Creating test data for 2024")
    print("=" * 70 + "\n")
    
    # Clean up any existing test data first
    print("🧹 Limpiando datos existentes...")
    # Delete in order due to foreign keys
    SaldoVacaciones.query.filter(SaldoVacaciones.anio.in_([2024, 2025])).delete()
    Usuario.query.filter(Usuario.email.like('%test_cerrar_%')).delete()
    Festivo.query.filter(Festivo.fecha >= date(2024, 1, 1), Festivo.fecha <= date(2024, 12, 31)).delete()
    db.session.commit()
    print("   ✅ Datos limpiados\n")
    
    # === CREATE 3 TEST USERS ===
    print("👤 Creando usuarios de prueba...")
    
    users_data = [
        {"nombre": "Usuario Prueba 1 (2 días sobrantes)", "email": "test_cerrar_1@test.com", "dias_restantes": 2},
        {"nombre": "Usuario Prueba 2 (7 días sobrantes)", "email": "test_cerrar_2@test.com", "dias_restantes": 7},
        {"nombre": "Usuario Prueba 3 (-2 días deuda)", "email": "test_cerrar_3@test.com", "dias_restantes": -2},
    ]
    
    created_users = []
    for u_data in users_data:
        user = Usuario(
            nombre=u_data["nombre"],
            email=u_data["email"],
            password=generate_password_hash("test123"),
            rol='empleado',
            dias_vacaciones=25
        )
        db.session.add(user)
        db.session.flush()  # Get ID
        
        # Calculate dias_disfrutados to achieve desired remaining days
        # remaining = dias_totales - dias_disfrutados
        # dias_disfrutados = dias_totales - remaining
        dias_disfrutados = 25 - u_data["dias_restantes"]
        
        saldo = SaldoVacaciones(
            usuario_id=user.id,
            anio=2024,
            dias_totales=25,
            dias_disfrutados=dias_disfrutados,
            dias_carryover=0
        )
        db.session.add(saldo)
        created_users.append((user, u_data["dias_restantes"]))
        
        remaining = 25 - dias_disfrutados
        print(f"   ✅ {u_data['nombre']}")
        print(f"      Saldo 2024: Total=25, Disfrutados={dias_disfrutados}, Restantes={remaining}")
    
    db.session.commit()
    print()
    
    # === CREATE 3 FESTIVOS FOR 2024 ===
    print("📅 Creando festivos para 2024...")
    
    festivos_data = [
        {"fecha": date(2024, 1, 1), "descripcion": "Año Nuevo 2024"},
        {"fecha": date(2024, 5, 1), "descripcion": "Día del Trabajo 2024"},
        {"fecha": date(2024, 12, 25), "descripcion": "Navidad 2024"},
    ]
    
    created_festivos = []
    for f_data in festivos_data:
        festivo = Festivo(
            fecha=f_data["fecha"],
            descripcion=f_data["descripcion"],
            activo=True
        )
        db.session.add(festivo)
        created_festivos.append(festivo)
        print(f"   ✅ {f_data['fecha'].strftime('%d/%m/%Y')}: {f_data['descripcion']} (activo=True)")
    
    db.session.commit()
    print()
    
    return created_users, created_festivos


def verify_results(created_users, created_festivos):
    """Verify that results match expectations."""
    
    print("\n" + "=" * 70)
    print("  VERIFICATION: Checking results")
    print("=" * 70 + "\n")
    
    all_passed = True
    
    # === CHECK FESTIVOS ===
    print("📅 Verificando festivos 2024...")
    for festivo in created_festivos:
        db.session.refresh(festivo)
        status = "❌ ACTIVO (debería estar desactivado)" if festivo.activo else "✅ Desactivado correctamente"
        print(f"   {festivo.fecha.strftime('%d/%m/%Y')}: {festivo.descripcion} → {status}")
        if festivo.activo:
            all_passed = False
    print()
    
    # === CHECK USER SALDOS FOR 2025 ===
    print("💼 Verificando saldos de vacaciones 2025...")
    
    # Expected totals: base(25) + min(remaining, 3) or full debt if negative
    expected_totals = [
        27,  # 25 + 2 (2 < 3, so full carryover)
        28,  # 25 + 3 (7 > 3, so capped at 3)
        23,  # 25 + (-2) = 23 (debt carries fully)
    ]
    expected_carryovers = [
        2,   # 2 days
        3,   # capped from 7
        -2,  # -2 debt
    ]
    
    for i, (user, original_remaining) in enumerate(created_users):
        saldo_2025 = SaldoVacaciones.query.filter_by(
            usuario_id=user.id,
            anio=2025
        ).first()
        
        expected_total = expected_totals[i]
        expected_carryover = expected_carryovers[i]
        
        if saldo_2025:
            total_ok = saldo_2025.dias_totales == expected_total
            carryover_ok = saldo_2025.dias_carryover == expected_carryover
            
            total_status = "✅" if total_ok else "❌"
            carryover_status = "✅" if carryover_ok else "❌"
            
            print(f"   {user.nombre}:")
            print(f"      {total_status} dias_totales: {saldo_2025.dias_totales} (esperado: {expected_total})")
            print(f"      {carryover_status} dias_carryover: {saldo_2025.dias_carryover} (esperado: {expected_carryover})")
            print(f"         dias_disfrutados: {saldo_2025.dias_disfrutados}")
            
            if not total_ok or not carryover_ok:
                all_passed = False
        else:
            print(f"   ❌ {user.nombre}: No se encontró saldo 2025!")
            all_passed = False
    
    print()
    
    # === FINAL RESULT ===
    print("=" * 70)
    if all_passed:
        print("🎉 TODOS LOS TESTS PASARON CORRECTAMENTE")
    else:
        print("⚠️  ALGUNOS TESTS FALLARON - Revisar arriba")
    print("=" * 70 + "\n")
    
    return all_passed


def run_test():
    """Main test execution."""
    
    # Configure app for testing
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    
    with app.app_context():
        # Create all tables in the in-memory database
        db.create_all()
        # Setup
        created_users, created_festivos = setup_test_data()
        
        # Run the close year command
        print("=" * 70)
        print("  RUNNING: flask cerrar-anio 2024 --max-carryover 3 --force")
        print("=" * 70 + "\n")
        
        runner = CliRunner()
        result = runner.invoke(
            cerrar_anio_command,
            ['2024', '--max-carryover', '3', '--gestionar-festivos', 'archivar', '--force'],
            catch_exceptions=False
        )
        
        print(result.output)
        
        if result.exit_code != 0:
            print(f"\n❌ ERROR: El comando terminó con código {result.exit_code}")
            if result.exception:
                import traceback
                traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
            return False
        
        # Verify
        return verify_results(created_users, created_festivos)


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
