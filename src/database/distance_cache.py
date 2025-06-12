import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .db_manager import DatabaseManager
import logging
import unicodedata

logger = logging.getLogger(__name__)

class DistanceCache:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.distances_df = pd.DataFrame()
    
    def _normalize_name(self, name: str) -> str:
        """Normaliza el nombre de una ciudad para búsquedas consistentes."""
        # Convertir a minúsculas y eliminar acentos
        normalized = unicodedata.normalize('NFKD', name.lower())
        normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
        return normalized.strip()
    
    def get_distance(self, origen: str, destino: str) -> Optional[float]:
        """Obtiene la distancia entre dos ciudades desde la base de datos."""
        try:
            logger.info(f"Buscando en caché la distancia entre {origen} y {destino}")
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT d.distancia_km
                    FROM distancias d
                    JOIN ciudades c1 ON d.origen_id = c1.id
                    JOIN ciudades c2 ON d.destino_id = c2.id
                    WHERE LOWER(c1.nombre) = LOWER(?) AND LOWER(c2.nombre) = LOWER(?)
                """, (origen, destino))
                result = cursor.fetchone()
                if result:
                    logger.info(f"✅ Distancia encontrada en caché: {origen} -> {destino}: {result[0]:.1f} km")
                else:
                    logger.info(f"❌ Distancia no encontrada en caché: {origen} -> {destino}")
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo distancia de la caché: {str(e)}")
            return None
    
    def save_distance(self, origen: Dict, destino: Dict, distancia: float):
        """Guarda una distancia en la base de datos."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener o crear IDs de las ciudades
                cursor.execute("""
                    INSERT OR IGNORE INTO ciudades (nombre, provincia, latitud, longitud)
                    VALUES (?, ?, ?, ?)
                """, (origen['nombre'], origen['provincia'], 
                      origen['latitud'], origen['longitud']))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO ciudades (nombre, provincia, latitud, longitud)
                    VALUES (?, ?, ?, ?)
                """, (destino['nombre'], destino['provincia'], 
                      destino['latitud'], destino['longitud']))
                
                # Obtener los IDs
                cursor.execute("""
                    SELECT id FROM ciudades 
                    WHERE nombre = ? AND provincia = ?
                """, (origen['nombre'], origen['provincia']))
                origen_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT id FROM ciudades 
                    WHERE nombre = ? AND provincia = ?
                """, (destino['nombre'], destino['provincia']))
                destino_id = cursor.fetchone()[0]
                
                # Guardar la distancia
                cursor.execute("""
                    INSERT INTO distancias (origen_id, destino_id, distancia_km)
                    VALUES (?, ?, ?)
                    ON CONFLICT(origen_id, destino_id) DO UPDATE SET
                        distancia_km = excluded.distancia_km,
                        fecha_calculo = CURRENT_TIMESTAMP
                """, (origen_id, destino_id, distancia))
                
                conn.commit()
                logger.info(f"Distancia guardada: {origen['nombre']} -> {destino['nombre']}: {distancia:.1f} km")
                
        except Exception as e:
            logger.error(f"Error guardando distancia: {str(e)}")
    
    def get_cache_stats(self) -> dict:
        """Obtiene estadísticas de la caché."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total de distancias
                cursor.execute("SELECT COUNT(*) FROM distancias")
                total = cursor.fetchone()[0]
                
                # Total de ciudades
                cursor.execute("SELECT COUNT(*) FROM ciudades")
                total_ciudades = cursor.fetchone()[0]
                
                return {
                    'total_distancias': total,
                    'total_ciudades': total_ciudades,
                    'porcentaje_completado': (total / (total_ciudades * (total_ciudades - 1))) * 100 if total_ciudades > 1 else 0
                }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {} 