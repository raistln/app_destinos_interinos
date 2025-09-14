import logging
import os
from pathlib import Path

def setup_logging():
    """
    Configura el sistema de logging para la aplicación.
    """
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Handler para archivo
            logging.FileHandler(log_dir / "app.log", encoding='utf-8'),
            # Handler para consola (solo errores en producción)
            logging.StreamHandler()
        ]
    )
    
    # Configurar niveles específicos para librerías externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Logger principal de la aplicación
    logger = logging.getLogger(__name__)
    logger.info("Sistema de logging configurado correctamente")
    
    return logger
