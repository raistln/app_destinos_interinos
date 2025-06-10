import pytest
from exceptions import (
    PreferenciaInterinosError, ConfiguracionError, LLMError, DistanciaError,
    DatosError, ValidacionError, APIError, ArchivoError
)

def test_preferencia_interinos_error():
    with pytest.raises(PreferenciaInterinosError):
        raise PreferenciaInterinosError("Error base")

def test_configuracion_error():
    with pytest.raises(ConfiguracionError):
        raise ConfiguracionError("Error de configuración")

def test_llm_error():
    with pytest.raises(LLMError):
        raise LLMError("Error LLM")

def test_distancia_error():
    with pytest.raises(DistanciaError):
        raise DistanciaError("Error de distancia")

def test_datos_error():
    with pytest.raises(DatosError):
        raise DatosError("Error de datos")

def test_validacion_error():
    with pytest.raises(ValidacionError):
        raise ValidacionError("Error de validación")

def test_api_error():
    with pytest.raises(APIError):
        raise APIError("Error de API")

def test_archivo_error():
    with pytest.raises(ArchivoError):
        raise ArchivoError("Error de archivo") 