from typing import Dict, Optional
import logging
from database.supabase_manager import SupabaseManager

logger = logging.getLogger(__name__)

class DistanceCache:
    def __init__(self, supabase_manager: SupabaseManager = None):
        self.supabase_manager = supabase_manager or SupabaseManager()
        self.cache_hits = 0
        self.cache_misses = 0
        
    def get_distance(self, location1: str, location2: str) -> Optional[float]:
        """
        Obtiene la distancia entre dos localidades desde la caché.
        
        Args:
            location1: Primera localidad
            location2: Segunda localidad
            
        Returns:
            Distancia en kilómetros o None si no está en caché
        """
        try:
            distance = self.supabase_manager.get_cached_distance(location1, location2)
            
            if distance is not None:
                self.cache_hits += 1
                return distance
            else:
                self.cache_misses += 1
                return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo distancia de caché: {str(e)}")
            self.cache_misses += 1
            return None
    
    def save_distance(self, loc1_info: Dict, loc2_info: Dict, distance: float):
        """
        Guarda una distancia en la caché.
        
        Args:
            loc1_info: Información de la primera localidad
            loc2_info: Información de la segunda localidad
            distance: Distancia en kilómetros
        """
        try:
            success = self.supabase_manager.save_distance(
                loc1_info['nombre'], 
                loc2_info['nombre'], 
                distance
            )
            
            if not success:
                logger.warning(f"No se pudo guardar la distancia entre {loc1_info['nombre']} y {loc2_info['nombre']}")
                
        except Exception as e:
            logger.error(f"Error guardando distancia en caché: {str(e)}")
    
    def print_stats(self):
        """Imprime estadísticas de la caché."""
        try:
            # Obtener estadísticas de la base de datos
            db_stats = self.supabase_manager.get_cache_stats()
            
            total_requests = self.cache_hits + self.cache_misses
            if total_requests > 0:
                hit_rate = (self.cache_hits / total_requests) * 100
                print(f"\n📊 Estadísticas de caché:")
                print(f"   Hits en esta sesión: {self.cache_hits}")
                print(f"   Misses en esta sesión: {self.cache_misses}")
                print(f"   Hit rate de sesión: {hit_rate:.1f}%")
                print(f"   Total ciudades en BD: {db_stats['ciudades']}")
                print(f"   Total distancias en BD: {db_stats['distancias']}")
            else:
                print(f"\n📊 Estadísticas de base de datos:")
                print(f"   Total ciudades: {db_stats['ciudades']}")
                print(f"   Total distancias: {db_stats['distancias']}")
                print("   No hay estadísticas de sesión disponibles")
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            print("\n📊 No se pudieron obtener estadísticas de caché") 