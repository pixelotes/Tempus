import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import date, timedelta
from src.google_calendar import (
    get_calendar_service,
    crear_evento_vacaciones,
    crear_evento_baja,
    eliminar_evento,
    actualizar_evento
)
from src.models import Usuario, SolicitudVacaciones, SolicitudBaja, TipoAusencia

@pytest.fixture
def mock_user():
    user = Usuario(
        id=1,
        nombre="Test User",
        email="test@example.com",
        google_calendar_enabled=True,
        google_token=json.dumps({
            "access_token": "fake_access_token",
            "refresh_token": "fake_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client_id",
            "client_secret": "fake_client_secret",
            "scopes": ["https://www.googleapis.com/auth/calendar.events"]
        })
    )
    return user

@pytest.fixture
def mock_service():
    service = MagicMock()
    events = MagicMock()
    service.events.return_value = events
    return service

def test_get_calendar_service_no_token():
    user = Usuario(nombre="No Token", google_token=None)
    assert get_calendar_service(user) is None

def test_get_calendar_service_disabled():
    user = Usuario(nombre="Disabled", google_token="{}", google_calendar_enabled=False)
    assert get_calendar_service(user) is None

@patch("src.google_calendar.build")
@patch("src.google_calendar.Credentials")
def test_get_calendar_service_success(mock_credentials, mock_build, mock_user):
    mock_creds_instance = MagicMock()
    mock_creds_instance.expired = False
    mock_credentials.return_value = mock_creds_instance
    
    mock_service_instance = MagicMock()
    mock_build.return_value = mock_service_instance
    
    service = get_calendar_service(mock_user)
    
    assert service == mock_service_instance
    mock_build.assert_called_once_with('calendar', 'v3', credentials=mock_creds_instance)

@patch("src.google_calendar.build")
@patch("src.google_calendar.Credentials")
@patch("src.db.session.commit")
def test_get_calendar_service_refresh(mock_commit, mock_credentials, mock_build, mock_user):
    # Setup credentials that are expired and have a refresh token
    mock_creds_instance = MagicMock()
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = "valid_refresh_token"
    # Mock attributes for new token saving
    mock_creds_instance.token = "new_access_token"
    mock_creds_instance.token_uri = "uri"
    mock_creds_instance.client_id = "id"
    mock_creds_instance.client_secret = "secret"
    mock_creds_instance.scopes = ["scope"]
    
    mock_credentials.return_value = mock_creds_instance
    
    with patch("google.auth.transport.requests.Request") as mock_request:
        service = get_calendar_service(mock_user)
        
        # Verify refresh was called
        mock_creds_instance.refresh.assert_called_once()
        # Verify DB commit (token update)
        mock_commit.assert_called_once()
        # Verify user token was updated
        token_data = json.loads(mock_user.google_token)
        assert token_data['access_token'] == "new_access_token"

@patch("src.google_calendar.get_calendar_service")
def test_crear_evento_vacaciones(mock_get_service, mock_user, mock_service):
    mock_get_service.return_value = mock_service
    mock_service.events().insert().execute.return_value = {"id": "evt_123", "htmlLink": "http://link"}
    
    solicitud = SolicitudVacaciones(
        usuario=mock_user,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 1, 5),
        dias_solicitados=5,
        motivo="Vacaciones prueba"
    )
    
    event_id = crear_evento_vacaciones(solicitud)
    
    assert event_id == "evt_123"
    
    # Verify payload
    args, kwargs = mock_service.events().insert.call_args
    body = kwargs['body']
    assert body['summary'] == '🏖️ Vacaciones'
    assert body['start']['date'] == '2025-01-01'
    assert body['end']['date'] == '2025-01-06' # +1 day

@patch("src.google_calendar.get_calendar_service")
def test_crear_evento_baja(mock_get_service, mock_user, mock_service):
    mock_get_service.return_value = mock_service
    mock_service.events().insert().execute.return_value = {"id": "evt_baja_123", "htmlLink": "http://link"}
    
    tipo = TipoAusencia(nombre="Baja Médica")
    solicitud = SolicitudBaja(
        usuario=mock_user,
        fecha_inicio=date(2025, 2, 1),
        fecha_fin=date(2025, 2, 2),
        dias_solicitados=2,
        motivo="Gripe",
        tipo_ausencia=tipo
    )
    
    event_id = crear_evento_baja(solicitud)
    
    assert event_id == "evt_baja_123"
    
    # Verify payload
    args, kwargs = mock_service.events().insert.call_args
    body = kwargs['body']
    assert body['summary'] == '🏥 Baja Médica'
    assert body['colorId'] == '11'

@patch("src.google_calendar.get_calendar_service")
def test_eliminar_evento(mock_get_service, mock_user, mock_service):
    mock_get_service.return_value = mock_service
    
    result = eliminar_evento(mock_user, "evt_to_delete")
    
    assert result is True
    mock_service.events().delete.assert_called_once_with(calendarId='primary', eventId='evt_to_delete')

@patch("src.google_calendar.get_calendar_service")
def test_actualizar_evento(mock_get_service, mock_user, mock_service):
    mock_get_service.return_value = mock_service
    
    # Setup mock for get()
    current_event = {
        'summary': 'Old Summary',
        'start': {'date': '2020-01-01'},
        'end': {'date': '2020-01-02'}
    }
    mock_service.events().get().execute.return_value = current_event
    
    solicitud = SolicitudVacaciones(
        usuario=mock_user,
        fecha_inicio=date(2025, 5, 1),
        fecha_fin=date(2025, 5, 5),
    )
    
    result = actualizar_evento(mock_user, "evt_update", solicitud, tipo='vacaciones')
    
    assert result is True
    mock_service.events().get.assert_called_with(calendarId='primary', eventId='evt_update')
    
    # Verify update call
    update_args, update_kwargs = mock_service.events().update.call_args
    assert update_kwargs['eventId'] == 'evt_update'
    assert update_kwargs['body']['summary'] == '🏖️ Vacaciones'
    assert update_kwargs['body']['start']['date'] == '2025-05-01'
