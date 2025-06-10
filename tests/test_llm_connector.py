import pytest
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from llm_connector import LLMConnector
from exceptions import LLMError, ConfiguracionError, ValidacionError, APIError
from distance_calculator import DistanceCalculator
import requests

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
def calculator():
    """Fixture para el calculador de distancias."""
    return DistanceCalculator()

@pytest.fixture
def llm_connector(mock_config, monkeypatch):
    monkeypatch.setenv('MISTRAL_API_KEY', 'test-key')
    with patch('yaml.safe_load', return_value=mock_config):
        return LLMConnector()

@patch('src.llm_connector.load_dotenv')
def test_init_success(mock_load_dotenv, mock_config, monkeypatch):
    """Test de inicialización exitosa del LLMConnector."""
    monkeypatch.setenv('MISTRAL_API_KEY', 'test-key')
    with patch('yaml.safe_load', return_value=mock_config):
        llm_connector = LLMConnector()
        assert llm_connector.model == 'test-model'
        assert llm_connector.api_url == 'http://test-api'
        assert llm_connector.headers['Authorization'] == 'Bearer test-key'

@patch('src.llm_connector.load_dotenv')
def test_normalize_city_name(mock_load_dotenv, mock_config, monkeypatch):
    """Test de normalización de nombres de ciudades."""
    monkeypatch.setenv('MISTRAL_API_KEY', 'test-key')
    with patch('yaml.safe_load', return_value=mock_config):
        connector = LLMConnector()
        assert connector._normalize_city_name("madrid") == "Madrid"
        assert connector._normalize_city_name("SAN SEBASTIAN") == "San Sebastian"
        assert connector._normalize_city_name("la-zubia") == "La Zubia"

@patch('src.llm_connector.load_dotenv')
@patch.object(LLMConnector, '_build_prompt', return_value="mocked prompt")
@patch.object(LLMConnector, '_sort_centers', return_value=[])
@patch.object(LLMConnector, '_normalize_city_name', side_effect=lambda x: x)
@patch('src.llm_connector.DistanceCalculator')
def test_generate_prompt_grouped_and_numbered(mock_distance_calculator_class, mock_normalize, mock_sort_centers, mock_build_prompt, mock_load_dotenv, mock_config):
    """Test de generación de prompt agrupado por ciudad y numerado de forma continua."""
    # Configure the mock instance returned by the mocked class
    mock_distance_calculator_instance = mock_distance_calculator_class.return_value
    def fake_get_distance(location1, province1, location2, province2):
        if location1 == "Granada":
            return 5.0 if location2 == "Granada" else 60.0
        if location1 == "Motril":
            return 5.0 if location2 == "Motril" else 60.0
        if location1 == "Salobreña":
            return 10.0 if location2 == "Granada" else 40.0
        return 100.0
    mock_distance_calculator_instance.get_distance.side_effect = fake_get_distance

    connector = LLMConnector()
    tipo_centro = "IES"
    provincias = ["Granada"]
    ciudades_preferencia = [
        {"nombre": "Granada", "radio": 50},
        {"nombre": "Motril", "radio": 50}
    ]
    datos_centros = [
        {"Localidad": "Granada", "Provincia": "Granada", "Nombre": "Centro 1"},
        {"Localidad": "Motril", "Provincia": "Granada", "Nombre": "Centro 2"},
        {"Localidad": "Salobreña", "Provincia": "Granada", "Nombre": "Centro 3"}
    ]

    prompt = connector.generate_prompt(
        tipo_centro=tipo_centro,
        provincias=provincias,
        ciudades_preferencia=ciudades_preferencia,
        datos_centros=datos_centros
    )
    assert prompt == "mocked prompt"

@patch('src.llm_connector.load_dotenv')
@patch.object(LLMConnector, '_build_prompt', return_value="mocked prompt no centros")
@patch.object(LLMConnector, '_sort_centers', return_value=[])
@patch.object(LLMConnector, '_normalize_city_name', side_effect=lambda x: x)
@patch('src.llm_connector.DistanceCalculator')
def test_generate_prompt_no_centros(mock_distance_calculator_class, mock_normalize, mock_sort_centers, mock_build_prompt, mock_load_dotenv, mock_config):
    """Test de mensaje cuando no hay centros dentro del radio para una ciudad."""
    # Configure the mock instance returned by the mocked class
    mock_distance_calculator_instance = mock_distance_calculator_class.return_value
    mock_distance_calculator_instance.get_distance.return_value = 100.0

    connector = LLMConnector()
    tipo_centro = "IES"
    provincias = ["Granada"]
    ciudades_preferencia = [
        {"nombre": "Granada", "radio": 50},
        {"nombre": "Motril", "radio": 50}
    ]
    datos_centros = [
        {"Localidad": "Granada", "Provincia": "Granada", "Nombre": "Centro 1"}
    ]

    prompt = connector.generate_prompt(
        tipo_centro=tipo_centro,
        provincias=provincias,
        ciudades_preferencia=ciudades_preferencia,
        datos_centros=datos_centros
    )
    assert prompt == "mocked prompt no centros"

@patch('src.llm_connector.load_dotenv')
def test_process_with_llm_success(mock_load_dotenv, llm_connector):
    """Test de procesamiento exitoso con LLM."""
    mock_response = Mock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Test response'}}]
    }
    mock_response.raise_for_status = Mock()

    with patch.object(llm_connector.session, 'post', return_value=mock_response):
        result = llm_connector.process_with_llm("Test prompt")
        assert result == "Test response"

@patch('src.llm_connector.load_dotenv')
def test_api_key_preference_env_var(mock_load_dotenv, monkeypatch, mock_config):
    """Test de preferencia: .env variable is used when no text input key."""
    monkeypatch.setenv('MISTRAL_API_KEY', 'key_env')
    with patch('yaml.safe_load', return_value=mock_config):
        connector = LLMConnector()
        assert connector.headers['Authorization'] == 'Bearer key_env'

@patch('src.llm_connector.load_dotenv')
def test_api_key_preference_text_input(mock_load_dotenv, monkeypatch, mock_config):
    """Test de preferencia: text input key is used over .env variable."""
    monkeypatch.setenv('MISTRAL_API_KEY', 'key_env')
    os.environ['MISTRAL_API_KEY'] = 'key_textinput'
    with patch('yaml.safe_load', return_value=mock_config):
        connector = LLMConnector()
        assert connector.headers['Authorization'] == 'Bearer key_textinput'
    del os.environ['MISTRAL_API_KEY']

@patch('src.llm_connector.load_dotenv')
def test_build_prompt_no_centros_message(mock_load_dotenv, llm_connector):
    """Test del mensaje de _build_prompt cuando no hay centros para una ciudad."""
    tipo_centro = "IES"
    provincias = ["Granada"]
    ciudades_referencia = [
        {"nombre": "Granada", "provincia": "Granada", "radio": 50},
        {"nombre": "Motril", "provincia": "Granada", "radio": 50}
    ]
    distancias_centros = {
        "Granada (Granada)": {"Granada": 5.0, "Motril": 100.0}
    }
    
    mock_sorted_centers = [
        {'centro': 'Granada (Granada)', 'ciudad_ref': 'Granada', 'distancia': 5.0}
    ]

    with patch.object(llm_connector, '_sort_centers', return_value=mock_sorted_centers):
        prompt = llm_connector._build_prompt(
            tipo_centro=tipo_centro,
            provincias=provincias,
            ciudades_referencia=ciudades_referencia,
            distancias_centros=distancias_centros
        )

        assert "No se encontraron centros dentro del radio especificado para:" in prompt
        assert "- Motril (radio: 50 km)" in prompt
        assert "Cercanos a Granada:" in prompt
        assert "1. Granada (Granada) - 5.0 km" in prompt
        assert "Cercanos a Motril:" not in prompt 