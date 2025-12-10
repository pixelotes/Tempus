
import click
from flask.cli import with_appcontext
from src import db
from src.models import Usuario, SaldoVacaciones

MAX_CARRYOVER = 5

@click.command('cerrar-anio')
@click.argument('anio_origen', type=int)
@with_appcontext
def cerrar_anio_command(anio_origen):
    """
    Cierra el año fiscal especificado y genera los saldos del siguiente.
    Uso: flask cerrar-anio 2024
    """
    anio_nuevo = anio_origen + 1
    usuarios = Usuario.query.all()
    count = 0
    
    print(f"--- Cerrando Año Fiscal {anio_origen} -> {anio_nuevo} ---")

    for u in usuarios:
        # 1. Obtener saldo del año que cierra
        saldo_antiguo = SaldoVacaciones.query.filter_by(usuario_id=u.id, anio=anio_origen).first()

        # Si no tuvo saldo el año anterior, asumimos 0 sobrante
        sobrante = 0
        if saldo_antiguo:
            sobrante = saldo_antiguo.dias_totales - saldo_antiguo.dias_disfrutados

        # 2. Aplicar política de Carryover
        # Si sobraron días negativos (comió días de más), se restan del año siguiente (deuda)
        # Si sobraron positivos, aplicamos el tope (MAX_CARRYOVER)
        if sobrante > 0:
            dias_a_traspasar = min(sobrante, MAX_CARRYOVER)
        else:
            dias_a_traspasar = sobrante # Arrastra la deuda íntegra

        # 3. Calcular base del nuevo año
        # Usamos u.dias_vacaciones como la "Base Contractual"
        dias_base_nuevo_anio = u.dias_vacaciones 
        total_nuevo = dias_base_nuevo_anio + dias_a_traspasar

        # 4. Crear o Actualizar Saldo del Año Nuevo
        saldo_nuevo = SaldoVacaciones.query.filter_by(usuario_id=u.id, anio=anio_nuevo).first()

        if not saldo_nuevo:
            saldo_nuevo = SaldoVacaciones(
                usuario_id=u.id,
                anio=anio_nuevo,
                dias_totales=total_nuevo,
                dias_disfrutados=0,
                dias_carryover=dias_a_traspasar
            )
            db.session.add(saldo_nuevo)
            count += 1
            print(f"> Generado saldo {anio_nuevo} para {u.nombre}: Base {dias_base_nuevo_anio} + Carryover {dias_a_traspasar} = {total_nuevo}")
        else:
            print(f"> Saltado {u.nombre}: Ya tiene saldo para {anio_nuevo}")

    db.session.commit()
    print(f"✅ Proceso finalizado. Se generaron {count} nuevos saldos.")
