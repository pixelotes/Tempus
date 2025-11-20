"""
Integración con Google Calendar para sincronizar vacaciones y bajas
"""
import os
import pickle
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarService:
    """
    Servicio para integración con Google Calendar.
    Gestiona la creación, actualización y eliminación de eventos.
    """
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    TOKEN_FILE = 'token.pickle'
    CREDENTIALS_FILE = 'credentials.json'  # Descargar desde Google Cloud Console
    
    def __init__(self, calendar_id=None):
        """
        Inicializa el servicio de Google Calendar
        
        Args:
            calendar_id: ID del calendario (usar 'primary' para el principal)
        """
        self.calendar_id = calendar_id or os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Calendar API"""
        creds = None
        
        # Cargar credenciales guardadas si existen
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # Si no hay credenciales válidas, obtener nuevas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"No se encontró {self.CREDENTIALS_FILE}. "
                        "Descárgalo desde Google Cloud Console"
                    )
                flow = Flow.from_client_secrets_file(
                    self.CREDENTIALS_FILE,
                    scopes=self.SCOPES,
                    redirect_uri='http://localhost:5000/oauth2callback'
                )
                # Este paso requiere autorización del usuario la primera vez
                # En producción, deberías implementar un flujo OAuth completo
                creds = flow.credentials
            
            # Guardar credenciales para la próxima ejecución
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    def crear_evento_vacaciones(self, solicitud):
        """
        Crea un evento en Google Calendar para vacaciones aprobadas
        
        Args:
            solicitud: Objeto SolicitudVacaciones
        
        Returns:
            str: ID del evento creado o None si falla
        """
        try:
            evento = {
                'summary': f'🏖️ Vacaciones - {solicitud.usuario.nombre}',
                'description': (
                    f'Vacaciones aprobadas\n'
                    f'Empleado: {solicitud.usuario.nombre}\n'
                    f'Email: {solicitud.usuario.email}\n'
                    f'Días: {solicitud.dias_solicitados}\n'
                    f'Motivo: {solicitud.motivo or "No especificado"}'
                ),
                'start': {
                    'date': solicitud.fecha_inicio.isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
                'end': {
                    # Google Calendar: fecha fin es exclusiva, sumamos 1 día
                    'date': (solicitud.fecha_fin + timedelta(days=1)).isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
                'colorId': '10',  # Verde para vacaciones
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},  # 1 día antes
                    ],
                },
            }
            
            evento_creado = self.service.events().insert(
                calendarId=self.calendar_id,
                body=evento
            ).execute()
            
            print(f"✅ Evento de vacaciones creado: {evento_creado.get('htmlLink')}")
            return evento_creado.get('id')
            
        except HttpError as error:
            print(f"❌ Error al crear evento de vacaciones: {error}")
            return None
    
    def crear_evento_baja(self, solicitud):
        """
        Crea un evento en Google Calendar para baja aprobada
        
        Args:
            solicitud: Objeto SolicitudBaja
        
        Returns:
            str: ID del evento creado o None si falla
        """
        try:
            evento = {
                'summary': f'🏥 Baja - {solicitud.usuario.nombre}',
                'description': (
                    f'Baja médica\n'
                    f'Empleado: {solicitud.usuario.nombre}\n'
                    f'Email: {solicitud.usuario.email}\n'
                    f'Días: {solicitud.dias_solicitados}\n'
                    f'Motivo: {solicitud.motivo}'
                ),
                'start': {
                    'date': solicitud.fecha_inicio.isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
                'end': {
                    'date': (solicitud.fecha_fin + timedelta(days=1)).isoformat(),
                    'timeZone': 'Europe/Madrid',
                },
                'colorId': '11',  # Rojo para bajas
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},
                    ],
                },
            }
            
            evento_creado = self.service.events().insert(
                calendarId=self.calendar_id,
                body=evento
            ).execute()
            
            print(f"✅ Evento de baja creado: {evento_creado.get('htmlLink')}")
            return evento_creado.get('id')
            
        except HttpError as error:
            print(f"❌ Error al crear evento de baja: {error}")
            return None
    
    def eliminar_evento(self, event_id):
        """
        Elimina un evento del calendario
        
        Args:
            event_id: ID del evento en Google Calendar
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            print(f"✅ Evento eliminado: {event_id}")
            return True
            
        except HttpError as error:
            print(f"❌ Error al eliminar evento: {error}")
            return False
    
    def actualizar_evento(self, event_id, solicitud, tipo='vacaciones'):
        """
        Actualiza un evento existente
        
        Args:
            event_id: ID del evento en Google Calendar
            solicitud: Objeto SolicitudVacaciones o SolicitudBaja
            tipo: 'vacaciones' o 'baja'
        
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Obtener el evento actual
            evento = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Actualizar campos
            emoji = '🏖️' if tipo == 'vacaciones' else '🏥'
            tipo_texto = 'Vacaciones' if tipo == 'vacaciones' else 'Baja médica'
            
            evento['summary'] = f'{emoji} {tipo_texto} - {solicitud.usuario.nombre}'
            evento['start']['date'] = solicitud.fecha_inicio.isoformat()
            evento['end']['date'] = (solicitud.fecha_fin + timedelta(days=1)).isoformat()
            
            # Enviar actualización
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=evento
            ).execute()
            
            print(f"✅ Evento actualizado: {event_id}")
            return True
            
        except HttpError as error:
            print(f"❌ Error al actualizar evento: {error}")
            return False


# Funciones helper para usar en routes.py
def sincronizar_vacaciones_a_google(solicitud):
    """
    Sincroniza una solicitud de vacaciones aprobada con Google Calendar
    
    Args:
        solicitud: Objeto SolicitudVacaciones aprobada
    
    Returns:
        str: ID del evento creado o None
    """
    try:
        calendar = GoogleCalendarService()
        return calendar.crear_evento_vacaciones(solicitud)
    except Exception as e:
        print(f"Error en sincronización con Google Calendar: {e}")
        return None


def sincronizar_baja_a_google(solicitud):
    """
    Sincroniza una solicitud de baja aprobada con Google Calendar
    
    Args:
        solicitud: Objeto SolicitudBaja aprobada
    
    Returns:
        str: ID del evento creado o None
    """
    try:
        calendar = GoogleCalendarService()
        return calendar.crear_evento_baja(solicitud)
    except Exception as e:
        print(f"Error en sincronización con Google Calendar: {e}")
        return None


def eliminar_evento_google(event_id):
    """
    Elimina un evento de Google Calendar
    
    Args:
        event_id: ID del evento
    
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        calendar = GoogleCalendarService()
        return calendar.eliminar_evento(event_id)
    except Exception as e:
        print(f"Error al eliminar evento de Google Calendar: {e}")
        return False