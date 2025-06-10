import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.db_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    db = DatabaseManager("data/distancias_cache.db")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info("Tablas en la base de datos:")
        for table in tables:
            logger.info(f"- {table[0]}")
        
        # Contar registros en cada tabla
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            logger.info(f"Registros en {table[0]}: {count}")
        
        # Mostrar algunas distancias calculadas
        cursor.execute("""
            SELECT c1.nombre_normalizado, c2.nombre_normalizado, d.distancia_km, d.tipo_calculo
            FROM distancias_calculadas d
            JOIN ciudades_referencia c1 ON d.centro_id = c1.id
            JOIN ciudades_referencia c2 ON d.ciudad_id = c2.id
            LIMIT 7
        """)
        distances = cursor.fetchall()
        
        logger.info("\nAlgunas distancias calculadas:")
        for dist in distances:
            logger.info(f"De {dist[0]} a {dist[1]}: {dist[2]:.1f} km (calculado con {dist[3]})")

if __name__ == "__main__":
    check_database() 