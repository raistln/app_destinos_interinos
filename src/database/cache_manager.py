from typing import Optional, List, Tuple
from datetime import datetime
import logging
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class DistanceCacheManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def obtener_distancia_cached(self, centro_id: int, ciudad_id: int) -> Optional[float]:
        """Get cached distance if it exists."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT distancia_km, tipo_calculo, necesita_actualizacion
                FROM distancias_calculadas
                WHERE centro_id = ? AND ciudad_id = ?
            """, (centro_id, ciudad_id))
            result = cursor.fetchone()
            
            if result:
                distancia, tipo_calculo, necesita_actualizacion = result
                if tipo_calculo == 'geopy' and not necesita_actualizacion:
                    # Mark for update if it's a geopy calculation
                    self.marcar_para_actualizacion(centro_id, ciudad_id)
                return distancia
            return None

    def guardar_distancia(self, centro_id: int, ciudad_id: int, distancia: float, tipo_api: str):
        """Save or update a distance calculation."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO distancias_calculadas 
                    (centro_id, ciudad_id, distancia_km, tipo_calculo, fecha_calculo, necesita_actualizacion)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(centro_id, ciudad_id) DO UPDATE SET
                    distancia_km = excluded.distancia_km,
                    tipo_calculo = excluded.tipo_calculo,
                    fecha_calculo = excluded.fecha_calculo,
                    necesita_actualizacion = excluded.necesita_actualizacion
            """, (centro_id, ciudad_id, distancia, tipo_api, datetime.now(), False))
            conn.commit()

    def marcar_para_actualizacion(self, centro_id: int, ciudad_id: int):
        """Mark a distance calculation for update."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE distancias_calculadas
                SET necesita_actualizacion = TRUE
                WHERE centro_id = ? AND ciudad_id = ?
            """, (centro_id, ciudad_id))
            conn.commit()

    def obtener_pendientes_actualizacion(self) -> List[Tuple[int, int]]:
        """Get list of distance calculations pending update."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT centro_id, ciudad_id
                FROM distancias_calculadas
                WHERE necesita_actualizacion = TRUE
                AND tipo_calculo = 'geopy'
            """)
            return cursor.fetchall()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total cached distances
            cursor.execute("SELECT COUNT(*) FROM distancias_calculadas")
            total = cursor.fetchone()[0]
            
            # OSRM vs Geopy counts
            cursor.execute("""
                SELECT tipo_calculo, COUNT(*) 
                FROM distancias_calculadas 
                GROUP BY tipo_calculo
            """)
            tipo_counts = dict(cursor.fetchall())
            
            # Pending updates
            cursor.execute("""
                SELECT COUNT(*) 
                FROM distancias_calculadas 
                WHERE necesita_actualizacion = TRUE
            """)
            pending = cursor.fetchone()[0]
            
            return {
                'total_cached': total,
                'osrm_count': tipo_counts.get('osrm', 0),
                'geopy_count': tipo_counts.get('geopy', 0),
                'pending_updates': pending,
                'osrm_percentage': (tipo_counts.get('osrm', 0) / total * 100) if total > 0 else 0
            } 