from datetime import datetime, time, timedelta
from src import db
from src.models import Fichaje

def cerrar_fichajes_abiertos(app):
    """
    Busca fichajes que sigan abiertos (hora_salida IS NULL) y sean de fechas anteriores a hoy.
    Los cierra automáticamente marcándolos como incidencia.
    """
    with app.app_context():
        # Definir "hoy" y "ayer"
        ahora = datetime.now()
        hoy = ahora.date()
        
        # Buscamos fichajes abiertos cuya fecha sea ANTERIOR a hoy.
        # (Si alguien está trabajando a las 00:01 del mismo día, no se lo cerramos aún, 
        #  solo cerramos los que se olvidaron ayer).
        fichajes_olvidados = Fichaje.query.filter(
            Fichaje.hora_salida.is_(None),
            Fichaje.es_actual == True,
            Fichaje.tipo_accion != 'eliminacion',
            Fichaje.fecha < hoy 
        ).all()
        
        count = 0
        for f in fichajes_olvidados:
            # LÓGICA DE CIERRE DE INCIDENCIA
            # 1. Establecemos la hora de salida al final del día (23:59:59)
            #    para cerrar el registro técnicamente.
            f.hora_salida = time(23, 59, 59)
            
            # 2. Marcamos la incidencia en el motivo
            # Esto servirá para que el usuario o admin vea que hay algo raro.
            f.motivo_rectificacion = "CIERRE AUTOMÁTICO (OLVIDO DE SALIDA) - PENDIENTE DE REVISAR"
            
            # 3. Opcional: Podríamos poner pausa=0 para no complicar cálculos
            
            count += 1
            print(f"🔄 [CRON] Fichaje cerrado automáticamente para usuario {f.usuario_id} (Fecha: {f.fecha})")

        if count > 0:
            db.session.commit()
            print(f"✅ [CRON] Se han cerrado {count} fichajes olvidados.")
        else:
            print("💤 [CRON] No se encontraron fichajes olvidados para cerrar.")