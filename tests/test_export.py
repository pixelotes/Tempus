import pytest
import io
from src.services.export_service import generate_user_report
from datetime import datetime, time

class MockUser:
    def __init__(self, nombre):
        self.nombre = nombre

class MockFichaje:
    def __init__(self, fecha, hora_entrada, hora_salida, pausa, motivo):
        self.fecha = fecha
        self.hora_entrada = hora_entrada
        self.hora_salida = hora_salida
        self.pausa = pausa
        self.motivo_rectificacion = motivo

class MockAusencia:
    def __init__(self, inicio, fin, dias, motivo, estado):
        self.fecha_inicio = inicio
        self.fecha_fin = fin
        self.dias_solicitados = dias
        self.motivo = motivo
        self.estado = estado

def test_generate_user_report_output():
    # Setup
    usuario = MockUser("Test User")
    fichajes = [MockFichaje(
        fecha=datetime(2026, 1, 1),
        hora_entrada=time(9, 0),
        hora_salida=time(18, 0),
        pausa=60,
        motivo="Normal"
    )]
    ausencias = [MockAusencia(
        inicio=datetime(2026, 2, 1),
        fin=datetime(2026, 2, 5),
        dias=5,
        motivo="Vacaciones",
        estado="aprobada"
    )]
    
    # Execution
    buffer = generate_user_report(usuario, fichajes, ausencias)
    
    # Assertions
    assert isinstance(buffer, io.BytesIO)
    assert buffer.getbuffer().nbytes > 0
