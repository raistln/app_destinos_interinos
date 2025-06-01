import logging
from typing import Optional, Tuple, List
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from ..database.db_manager import DatabaseManager
import time

logger = logging.getLogger(__name__)

class GeocodingService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.geocoder = Nominatim(user_agent="destinos_interinos")
        self.cache = {}  # Simple in-memory cache for geocoding results

    def _normalize_location(self, location: str) -> str:
        """Normalize location string for consistent lookups."""
        return location.lower().strip()

    def _validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate if coordinates are within Spain's bounds."""
        return self.db.validate_spain_coordinates(lat, lon)

    def geocodificar_ciudad(self, nombre_ciudad: str) -> Optional[Tuple[float, float]]:
        """Geocode a city and store in database."""
        nombre_normalizado = self._normalize_location(nombre_ciudad)
        
        # Check database first
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT latitud, longitud
                FROM ciudades_referencia
                WHERE nombre_normalizado = ?
            """, (nombre_normalizado,))
            result = cursor.fetchone()
            
            if result:
                return result

        # Check memory cache
        if nombre_normalizado in self.cache:
            return self.cache[nombre_normalizado]

        # Geocode with Nominatim
        try:
            location = self.geocoder.geocode(f"{nombre_ciudad}, Spain")
            if location and self._validate_coordinates(location.latitude, location.longitude):
                coords = (location.latitude, location.longitude)
                
                # Store in database
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO ciudades_referencia 
                            (nombre_normalizado, latitud, longitud)
                        VALUES (?, ?, ?)
                        ON CONFLICT(nombre_normalizado) DO UPDATE SET
                            latitud = excluded.latitud,
                            longitud = excluded.longitud,
                            fecha_geocodificacion = CURRENT_TIMESTAMP
                    """, (nombre_normalizado, coords[0], coords[1]))
                    conn.commit()
                
                # Store in memory cache
                self.cache[nombre_normalizado] = coords
                return coords
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.error(f"Geocoding failed for {nombre_ciudad}: {str(e)}")
            return None

    def geocodificar_centro(self, municipio: str, provincia: str) -> Optional[Tuple[float, float]]:
        """Geocode a school center location."""
        location_str = f"{municipio}, {provincia}, Spain"
        
        try:
            location = self.geocoder.geocode(location_str)
            if location and self._validate_coordinates(location.latitude, location.longitude):
                return (location.latitude, location.longitude)
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.error(f"Geocoding failed for {location_str}: {str(e)}")
            return None

    def importar_centros_desde_csv(self, ruta_csv: str) -> int:
        """Import school centers from CSV and geocode them."""
        try:
            df = pd.read_csv(ruta_csv)
            imported_count = 0
            
            for _, row in df.iterrows():
                try:
                    coords = self.geocodificar_centro(row['municipio'], row['provincia'])
                    if coords:
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO centros_educativos 
                                    (nombre, direccion, municipio, provincia, tipo, 
                                     latitud, longitud, geocodificado)
                                VALUES (?, ?, ?, ?, ?, ?, ?, TRUE)
                            """, (
                                row['nombre'],
                                row.get('direccion', ''),
                                row['municipio'],
                                row['provincia'],
                                row['tipo'],
                                coords[0],
                                coords[1]
                            ))
                            conn.commit()
                            imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import center {row.get('nombre', 'unknown')}: {str(e)}")
                    continue
                
                # Rate limiting
                time.sleep(1)  # Basic rate limiting for Nominatim
            
            return imported_count
        except Exception as e:
            logger.error(f"Failed to import centers from CSV: {str(e)}")
            return 0 