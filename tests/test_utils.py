from datetime import date
from src.utils import calcular_dias_laborables
from src.models import Festivo
from src import db

def test_calcular_dias_laborables_simple(test_app):
    # Lunes a Viernes (5 días)
    inicio = date(2023, 1, 2)
    fin = date(2023, 1, 6)
    assert calcular_dias_laborables(inicio, fin) == 5

def test_calcular_dias_con_finde(test_app):
    # Lunes a Domingo (5 días laborables)
    inicio = date(2023, 1, 2)
    fin = date(2023, 1, 8)
    assert calcular_dias_laborables(inicio, fin) == 5

def test_calcular_dias_con_festivo(test_app):
    # Crear festivo el Miércoles
    festivo = Festivo(fecha=date(2023, 1, 4), descripcion="Festivo Test")
    db.session.add(festivo)
    db.session.commit()
    
    # Lunes a Viernes con 1 festivo (4 días)
    inicio = date(2023, 1, 2)
    fin = date(2023, 1, 6)
    assert calcular_dias_laborables(inicio, fin) == 4