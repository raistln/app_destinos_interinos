import logging
from typing import Optional, Tuple, List, Dict
import requests
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from ..database.cache_manager import DistanceCacheManager
from ..database.db_manager import DatabaseManager
import time

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_calls_per_minute: int):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.window = 60  # 1 minute window

    def wait_if_needed(self):
        """Wait if we've made too many calls in the last minute."""
        now = time.time()
        # Remove calls older than 1 minute
        self.calls = [t for t in self.calls if now - t < self.window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.window - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.calls.append(now)

class OptimizedDistanceService:
    def __init__(self, db_manager: DatabaseManager, osrm_url: str = "http://router.project-osrm.org/route/v1"):
        self.cache = DistanceCacheManager(db_manager)
        self.osrm_url = osrm_url
        self.osrm_limiter = RateLimiter(60)  # 60 calls per minute for OSRM
        self.geopy_limiter = RateLimiter(100)  # 100 calls per minute for Geopy
        self.geocoder = Nominatim(user_agent="destinos_interinos")

    def _get_coordinates(self, centro_id: int, ciudad_id: int) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get coordinates for both center and city."""
        with self.cache.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get center coordinates
            cursor.execute("""
                SELECT latitud, longitud
                FROM centros_educativos
                WHERE id = ?
            """, (centro_id,))
            centro_coords = cursor.fetchone()
            
            # Get city coordinates
            cursor.execute("""
                SELECT latitud, longitud
                FROM ciudades_referencia
                WHERE id = ?
            """, (ciudad_id,))
            ciudad_coords = cursor.fetchone()
            
            if not centro_coords or not ciudad_coords:
                raise ValueError("Coordinates not found for center or city")
            
            return centro_coords, ciudad_coords

    def _calculate_osrm_distance(self, start: Tuple[float, float], end: Tuple[float, float]) -> Optional[float]:
        """Calculate distance using OSRM."""
        try:
            self.osrm_limiter.wait_if_needed()
            url = f"{self.osrm_url}/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == "Ok":
                # Convert meters to kilometers
                return data["routes"][0]["distance"] / 1000
            return None
        except Exception as e:
            logger.warning(f"OSRM calculation failed: {str(e)}")
            return None

    def _calculate_geopy_distance(self, start: Tuple[float, float], end: Tuple[float, float]) -> float:
        """Calculate distance using Geopy."""
        self.geopy_limiter.wait_if_needed()
        return geodesic(start, end).kilometers

    def calcular_distancia(self, centro_id: int, ciudad_id: int) -> float:
        """Calculate distance with caching and fallback strategy."""
        # Try cache first
        cached_distance = self.cache.obtener_distancia_cached(centro_id, ciudad_id)
        if cached_distance is not None:
            return cached_distance

        # Get coordinates
        centro_coords, ciudad_coords = self._get_coordinates(centro_id, ciudad_id)

        # Try OSRM first
        osrm_distance = self._calculate_osrm_distance(centro_coords, ciudad_coords)
        if osrm_distance is not None:
            self.cache.guardar_distancia(centro_id, ciudad_id, osrm_distance, 'osrm')
            return osrm_distance

        # Fallback to Geopy
        geopy_distance = self._calculate_geopy_distance(centro_coords, ciudad_coords)
        self.cache.guardar_distancia(centro_id, ciudad_id, geopy_distance, 'geopy')
        return geopy_distance

    def _clean_location_name(self, name: str) -> str:
        """Remove IES prefix and clean location name."""
        # Remove IES prefix if it exists
        if name.upper().startswith('IES '):
            name = name[4:]
        return name.strip()

    def sort_localities_by_distance(self, reference_locations: List[Dict], localities: List[Dict]) -> List[Dict]:
        """
        Ordena las localidades siguiendo el criterio de proximidad a las localidades de referencia.
        
        Args:
            reference_locations: Lista de diccionarios con localidades de referencia en orden de prioridad
            localities: Lista de diccionarios con localidades a ordenar
            
        Returns:
            Lista ordenada de localidades
        """
        logger.info("\nIniciando ordenación de localidades...")
        logger.info(f"Número de localidades de referencia: {len(reference_locations)}")
        logger.info(f"Número total de localidades a ordenar: {len(localities)}")
        
        # Crear un conjunto de todas las localidades (incluyendo las de referencia)
        all_localities = []
        reference_cities = {loc['nombre']: loc for loc in reference_locations}
        
        # Añadir primero las localidades de referencia
        for ref_loc in reference_locations:
            all_localities.append({
                'Localidad': self._clean_location_name(str(ref_loc['nombre'])),
                'Provincia': str(ref_loc['Provincia']),
                'radio': ref_loc.get('radio', 50)  # Radio por defecto de 50km
            })
            logger.info(f"Añadida localidad de referencia: {ref_loc['nombre']} ({ref_loc['Provincia']}) con radio {ref_loc.get('radio', 50)}km")
        
        # Añadir el resto de localidades
        for loc in localities:
            if loc['Localidad'] not in reference_cities:
                all_localities.append({
                    'Localidad': self._clean_location_name(str(loc['Localidad'])),
                    'Provincia': str(loc['Provincia'])
                })
        
        # Para cada localidad, calcular su distancia a cada punto de referencia
        locality_distances = []
        for locality in all_localities:
            distances = []
            for ref_loc in reference_locations:
                try:
                    # Obtener IDs de la base de datos
                    with self.cache.db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Obtener ID de la ciudad de referencia
                        cursor.execute("""
                            SELECT id FROM ciudades_referencia 
                            WHERE nombre_normalizado = ?
                        """, (ref_loc['nombre'].lower(),))
                        ciudad_id = cursor.fetchone()
                        
                        # Obtener ID del centro
                        cursor.execute("""
                            SELECT id FROM centros_educativos 
                            WHERE municipio = ? AND provincia = ?
                        """, (locality['Localidad'], locality['Provincia']))
                        centro_id = cursor.fetchone()
                        
                        if ciudad_id and centro_id:
                            distance = self.calcular_distancia(centro_id[0], ciudad_id[0])
                            # Verificar si la localidad está dentro del radio de la ciudad de referencia
                            if distance <= ref_loc.get('radio', 50):
                                distances.append((ref_loc['nombre'], distance))
                                logger.info(f"Localidad {locality['Localidad']} ({locality['Provincia']}) dentro del radio de {ref_loc['nombre']} ({distance:.1f} km)")
                            else:
                                logger.info(f"Localidad {locality['Localidad']} ({locality['Provincia']}) fuera del radio de {ref_loc['nombre']} ({distance:.1f} km > {ref_loc.get('radio', 50)} km)")
                                distances.append((ref_loc['nombre'], float('inf')))
                except Exception as e:
                    logger.error(f"Error calculando distancia entre {ref_loc['nombre']} y {locality['Localidad']}: {str(e)}")
                    distances.append((ref_loc['nombre'], float('inf')))
            
            # Encontrar la localidad de referencia más cercana y su índice
            min_distance = float('inf')
            closest_ref_index = -1
            closest_ref_name = ""
            
            for i, (ref_name, dist) in enumerate(distances):
                if dist < min_distance:
                    min_distance = dist
                    closest_ref_index = i
                    closest_ref_name = ref_name
            
            locality_distances.append((locality, min_distance, closest_ref_index, closest_ref_name))
            logger.info(f"Localidad {locality['Localidad']} ({locality['Provincia']}) más cercana a {closest_ref_name} (índice {closest_ref_index})")
        
        # Filtrar localidades que están fuera del radio de su referencia más cercana
        valid_locality_distances = [item for item in locality_distances if item[1] != float('inf')]

        # Ordenar las localidades:
        # 1. Primero por el índice de la localidad de referencia más cercana (prioridad)
        # 2. Luego por la distancia a esa localidad de referencia
        def sort_key(item):
            locality, distance, ref_index, ref_name = item
            return (ref_index, distance)

        # Ordenar la lista filtrada
        sorted_valid_localities = sorted(valid_locality_distances, key=sort_key)

        # Extraer solo los diccionarios de localidades de la lista ordenada
        final_order = [loc for loc, _, _, _ in sorted_valid_localities]

        # Imprimir el orden final
        logger.info("\nOrden final de localidades:")
        for i, loc in enumerate(final_order):
            logger.info(f"{i+1}. {loc['Localidad']} ({loc['Provincia']})")
        
        return final_order

    def actualizar_distancias_geopy(self) -> int:
        """Update distances marked for update from Geopy to OSRM."""
        updated_count = 0
        pendientes = self.cache.obtener_pendientes_actualizacion()
        
        for centro_id, ciudad_id in pendientes:
            try:
                centro_coords, ciudad_coords = self._get_coordinates(centro_id, ciudad_id)
                osrm_distance = self._calculate_osrm_distance(centro_coords, ciudad_coords)
                
                if osrm_distance is not None:
                    self.cache.guardar_distancia(centro_id, ciudad_id, osrm_distance, 'osrm')
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update distance for {centro_id}-{ciudad_id}: {str(e)}")
                continue
        
        return updated_count 