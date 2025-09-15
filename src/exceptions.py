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

class APIRateLimitError(APIError):
    """Error cuando se excede el límite de peticiones de la API."""
    def __init__(self, message="Se ha excedido el límite de la API. Prueba en 5 minutos.", retry_after=300):
        super().__init__(message)
        self.retry_after = retry_after

class APIServerError(APIError):
    """Error cuando los servidores de la API están saturados."""
    def __init__(self, message="Servidores saturados. Prueba en 5 minutos.", retry_after=300):
        super().__init__(message)
        self.retry_after = retry_after

class APITimeoutError(APIError):
    """Error cuando la API no responde en tiempo."""
    def __init__(self, message="La API no responde. Verifica tu conexión e inténtalo de nuevo.", retry_after=60):
        super().__init__(message)
        self.retry_after = retry_after

class ArchivoError(PreferenciaInterinosError):
    """Error en la lectura/escritura de archivos."""
    pass