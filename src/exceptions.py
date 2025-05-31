class PreferenciaInterinosError(Exception):
    """Clase base para excepciones del proyecto."""
    pass

class ConfiguracionError(PreferenciaInterinosError):
    """Error en la configuración del sistema."""
    pass

class LLMError(PreferenciaInterinosError):
    """Error en la comunicación con el LLM."""
    pass

class DistanciaError(PreferenciaInterinosError):
    """Error en el cálculo de distancias."""
    pass

class DatosError(PreferenciaInterinosError):
    """Error en el procesamiento de datos."""
    pass

class ValidacionError(PreferenciaInterinosError):
    """Error en la validación de datos."""
    pass

class APIError(PreferenciaInterinosError):
    """Error en la comunicación con APIs externas."""
    pass

class ArchivoError(PreferenciaInterinosError):
    """Error en la lectura/escritura de archivos."""
    pass 