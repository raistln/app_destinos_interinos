import pytest
import os
from unittest.mock import Mock, patch
from src.llm_connector import LLMConnector
from src.exceptions import LLMError, ConfiguracionError, ValidacionError, APIError

@pytest.fixture
def mock_config():
    return {
        'llm': {
            'models': {
                'mistral': {
                    'name': 'test-model',
                    'api_url': 'http://test-api'
                }
            },
            'temperature': 0.7,
            'max_tokens': 100
        }
    }

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('MISTRAL_API_KEY', 'test-key')

@pytest.fixture
def llm_connector(mock_config, mock_env_vars):
    with patch('yaml.safe_load', return_value=mock_config):
        return LLMConnector()

def test_init_success(llm_connector):
    """Test de inicialización exitosa del LLMConnector."""
    assert llm_connector.model == 'test-model'
    assert llm_connector.api_url == 'http://test-api'
    assert llm_connector.headers['Authorization'] == 'Bearer test-key'

def test_init_missing_api_key(monkeypatch):
    """Test de inicialización fallida por falta de API key."""
    monkeypatch.delenv('MISTRAL_API_KEY', raising=False)
    with pytest.raises(ValidacionError) as exc_info:
        LLMConnector()
    assert "MISTRAL_API_KEY no encontrada" in str(exc_info.value)

def test_init_config_error():
    """Test de inicialización fallida por error en configuración."""
    with patch('builtins.open', side_effect=Exception("File not found")):
        with pytest.raises(ConfiguracionError) as exc_info:
            LLMConnector()
        assert "Error al cargar configuración" in str(exc_info.value)

def test_normalize_city_name(llm_connector):
    """Test de normalización de nombres de ciudades."""
    assert llm_connector._normalize_city_name("madrid") == "Madrid"
    assert llm_connector._normalize_city_name("SAN SEBASTIAN") == "San Sebastian"
    assert llm_connector._normalize_city_name("la-zubia") == "La Zubia"

def test_normalize_city_name_empty(llm_connector):
    """Test de normalización con nombre de ciudad vacío."""
    with pytest.raises(ValidacionError) as exc_info:
        llm_connector._normalize_city_name("")
    assert "El nombre de la ciudad no puede estar vacío" in str(exc_info.value)

def test_generate_prompt_validation(llm_connector):
    """Test de validación de parámetros en generate_prompt."""
    with pytest.raises(ValidacionError) as exc_info:
        llm_connector.generate_prompt("", [], [], [])
    assert "Tipo de centro debe ser 'IES' o 'CEIP'" in str(exc_info.value)

    with pytest.raises(ValidacionError) as exc_info:
        llm_connector.generate_prompt("IES", [], [], [])
    assert "Debe especificar al menos una provincia" in str(exc_info.value)

    with pytest.raises(ValidacionError) as exc_info:
        llm_connector.generate_prompt("IES", ["Granada"], [], [])
    assert "Debe especificar al menos una ciudad de preferencia" in str(exc_info.value)

def test_generate_prompt_success(llm_connector):
    """Test de generación exitosa de prompt."""
    tipo_centro = "IES"
    provincias = ["Granada"]
    ciudades_preferencia = [{"nombre": "Granada", "radio": 50}]
    datos_centros = [{
        "Localidad": "Granada",
        "Provincia": "Granada",
        "Nombre": "Test Center"
    }]

    with patch.object(llm_connector.distance_calculator, 'get_distance', return_value=10.0):
        prompt = llm_connector.generate_prompt(
            tipo_centro=tipo_centro,
            provincias=provincias,
            ciudades_preferencia=ciudades_preferencia,
            datos_centros=datos_centros
        )
        
        assert "IES" in prompt
        assert "Granada" in prompt
        assert "10.0 km" in prompt

def test_process_with_llm_success(llm_connector):
    """Test de procesamiento exitoso con LLM."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }
    mock_response.raise_for_status = Mock()

    with patch.object(llm_connector.session, 'post', return_value=mock_response):
        result = llm_connector.process_with_llm("Test prompt")
        assert result == "Test response"

def test_process_with_llm_api_error(llm_connector):
    """Test de error en API durante procesamiento."""
    with patch.object(llm_connector.session, 'post', side_effect=requests.exceptions.RequestException("API Error")):
        with pytest.raises(APIError) as exc_info:
            llm_connector.process_with_llm("Test prompt")
        assert "Error en comunicación con API" in str(exc_info.value)

def test_process_with_llm_invalid_response(llm_connector):
    """Test de respuesta inválida de la API."""
    mock_response = Mock()
    mock_response.json.return_value = {'invalid': 'response'}
    mock_response.raise_for_status = Mock()

    with patch.object(llm_connector.session, 'post', return_value=mock_response):
        with pytest.raises(APIError) as exc_info:
            llm_connector.process_with_llm("Test prompt")
        assert "Error en formato de respuesta" in str(exc_info.value) 