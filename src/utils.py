from datetime import timedelta
from .models import Festivo


def calcular_dias_laborables(fecha_inicio, fecha_fin):
    """
    Calcula los días laborables entre dos fechas.
    No cuenta fines de semana (sábados y domingos) ni festivos.
    
    Args:
        fecha_inicio: Fecha de inicio (date)
        fecha_fin: Fecha de fin (date)
    
    Returns:
        int: Número de días laborables
    """
    dias = 0
    fecha_actual = fecha_inicio
    festivos = set([f.fecha for f in Festivo.query.all()])
    
    while fecha_actual <= fecha_fin:
        # No contar fines de semana (5=sábado, 6=domingo)
        if fecha_actual.weekday() < 5 and fecha_actual not in festivos:
            dias += 1
        fecha_actual += timedelta(days=1)
    
    return dias