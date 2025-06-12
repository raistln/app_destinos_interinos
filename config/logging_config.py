import logging
import os
from logging.handlers import RotatingFileHandler
import sys

def setup_logging(log_level=logging.INFO):
    """
    Configura el sistema de logging para la aplicación.
    
    Args:
        log_level: Nivel de logging por defecto (default: INFO)
    """
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar el formato del log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar el handler para archivo con codificación UTF-8
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    
    # Configurar el handler para consola con codificación UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Eliminar handlers existentes para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Configurar loggers específicos
    loggers = {
        'llm_connector': logging.INFO,
        'distance_calculator': logging.INFO,
        'processor': logging.INFO
    }
    
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True  # Propagar logs al logger raíz
    
    return root_logger 