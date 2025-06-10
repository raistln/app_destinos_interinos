import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.db_manager import DatabaseManager
from distance_calculator import DistanceCalculator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Inicializa la base de datos con las ciudades de referencia."""
    try:
        # Inicializar la base de datos
        db = DatabaseManager("data/distancias_cache.db")
        calculator = DistanceCalculator()
        
        # Lista de ciudades de referencia (puedes modificarla según tus necesidades)
        ciudades_referencia = [
            {"nombre": "Granada", "provincia": "Granada"},
            {"nombre": "Almería", "provincia": "Almería"},
            {"nombre": "Cádiz", "provincia": "Cádiz"},
            {"nombre": "Córdoba", "provincia": "Córdoba"},
            {"nombre": "Huelva", "provincia": "Huelva"},
            {"nombre": "Jaén", "provincia": "Jaén"},
            {"nombre": "Málaga", "provincia": "Málaga"},
            {"nombre": "Sevilla", "provincia": "Sevilla"}
        ]
        
        # Cargar cada ciudad de referencia
        for ciudad in ciudades_referencia:
            try:
                coords = calculator._get_coordinates(ciudad["nombre"], ciudad["provincia"])
                if coords:
                    logger.info(f"Ciudad de referencia cargada: {ciudad['nombre']} ({coords[0]}, {coords[1]})")
                else:
                    logger.error(f"No se pudieron obtener coordenadas para {ciudad['nombre']}")
            except Exception as e:
                logger.error(f"Error cargando {ciudad['nombre']}: {str(e)}")
        
        logger.info("Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando la base de datos: {str(e)}")

if __name__ == "__main__":
    init_database() 