import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import DatabaseManager
from src.database.distance_cache import DistanceCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_cache():
    """Verifica el estado de la caché de distancias."""
    try:
        # Obtener la ruta base del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "data", "distancias_cache.db")
        
        # Inicializar la caché
        db = DatabaseManager(db_path)
        cache = DistanceCache(db)
        
        # Imprimir estadísticas
        cache.print_stats()
        
        # Exportar a CSV para análisis
        csv_path = os.path.join(base_dir, "data", "distancias_cache.csv")
        cache.export_to_csv(csv_path)
        
        # Mostrar algunas distancias faltantes
        missing = cache.get_missing_distances()
        if missing:
            print("\nPrimeras 10 distancias faltantes:")
            for origen, destino in missing[:10]:
                print(f"- {origen} -> {destino}")
            print(f"\nTotal de distancias faltantes: {len(missing)}")
        else:
            print("\n¡No hay distancias faltantes!")
            
    except Exception as e:
        logger.error(f"Error verificando la caché: {str(e)}")

if __name__ == "__main__":
    check_cache() 