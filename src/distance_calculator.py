import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from typing import Dict, List, Tuple, Optional
import time
import requests
import tempfile
from database.db_manager import DatabaseManager
from database.distance_cache import DistanceCache
import logging

logger = logging.getLogger(__name__)

class DistanceCalculator:
    def __init__(self):
        self.db_manager = DatabaseManager("data/distancias_cache.db")
        self.cache = DistanceCache(self.db_manager)
        self.geocoder = Nominatim(user_agent="destinos_interinos")
        self.osrm_url = "https://router.project-osrm.org/route/v1/driving"
        
    def _get_coordinates(self, location: str, province: str) -> Tuple[float, float]:
        """
        Obtiene las coordenadas de una localidad usando el caché si está disponible.
        
        Args:
            location: Nombre de la localidad
            province: Nombre de la provincia
            
        Returns:
            Tupla con (latitud, longitud)
        """
        # Primero intentar obtener de la base de datos
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT latitud, longitud
                FROM ciudades_referencia
                WHERE nombre_normalizado = ?
            """, (f"{location}, {province}, España".lower(),))
            result = cursor.fetchone()
            
            if result:
                return result
            
        try:
            # Añadir un pequeño delay para no sobrecargar la API
            time.sleep(3)
            
            # Intentar primero con el nombre y Andalucía
            location_data = self.geocoder.geocode(f"{location}, Andalucía, España", timeout=10)
            
            # Si no se encuentra, intentar con más contexto
            if not location_data:
                # Intentar con "Municipio de" o "Villa de"
                for prefix in ["Municipio de", "Villa de"]:
                    alt_query = f"{prefix} {location}, Andalucía, España"
                    location_data = self.geocoder.geocode(alt_query, timeout=10)
                    if location_data:
                        break
            
            if location_data:
                coords = (location_data.latitude, location_data.longitude)
                # Guardar en la base de datos
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO ciudades_referencia (nombre_normalizado, latitud, longitud)
                        VALUES (?, ?, ?)
                        ON CONFLICT(nombre_normalizado) DO UPDATE SET
                            latitud = excluded.latitud,
                            longitud = excluded.longitud
                    """, (f"{location}, {province}, España".lower(), coords[0], coords[1]))
                    conn.commit()
                logger.info(f"Coordenadas guardadas en la base de datos para {location}, {province}")
                return coords
            else:
                logger.warning(f"No se encontraron coordenadas para {location}, {province}")
                # Intentar con una búsqueda más amplia
                location_data = self.geocoder.geocode(f"{location}, España", timeout=10)
                if location_data:
                    coords = (location_data.latitude, location_data.longitude)
                    # Guardar en la base de datos
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO ciudades_referencia (nombre_normalizado, latitud, longitud)
                            VALUES (?, ?, ?)
                            ON CONFLICT(nombre_normalizado) DO UPDATE SET
                                latitud = excluded.latitud,
                                longitud = excluded.longitud
                        """, (f"{location}, {province}, España".lower(), coords[0], coords[1]))
                        conn.commit()
                    logger.info(f"Coordenadas guardadas en la base de datos (búsqueda amplia) para {location}, {province}")
                    return coords
                raise ValueError(f"No se encontraron coordenadas para {location}, {province}")
        except Exception as e:
            logger.error(f"Error al obtener coordenadas para {location}, {province}: {str(e)}")
            return None
            
    def get_distance(self, location1: str, province1: str, location2: str, province2: str) -> float:
        """
        Calcula la distancia por carretera entre dos localidades en kilómetros.
        
        Args:
            location1: Nombre de la primera localidad
            province1: Provincia de la primera localidad
            location2: Nombre de la segunda localidad
            province2: Provincia de la segunda localidad
            
        Returns:
            Distancia en kilómetros
        """
        try:
            # Normalizar nombres de localidades
            loc1_norm = f"{location1}, {province1}, España".lower()
            loc2_norm = f"{location2}, {province2}, España".lower()
            
            # Intentar obtener de la caché
            cached_distance = self.cache.get_distance(loc1_norm, loc2_norm)
            if cached_distance is not None:
                logger.info(f"Distancia obtenida de la caché entre {location1} y {location2}: {cached_distance:.1f} km")
                return cached_distance
            
            # Si no está en caché, obtener coordenadas
            coords1 = self._get_coordinates(location1, province1)
            coords2 = self._get_coordinates(location2, province2)
            
            if not coords1 or not coords2:
                raise ValueError("No se pudieron obtener las coordenadas para alguna de las localidades")
            
            # Intentar obtener la distancia por carretera usando OSRM
            try:
                url = f"{self.osrm_url}/{coords1[1]},{coords1[0]};{coords2[1]},{coords2[0]}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 'Ok':
                        distance = data['routes'][0]['distance'] / 1000  # Convertir a kilómetros
                        # Guardar en la caché
                        self.cache.save_distance(loc1_norm, loc2_norm, distance, 'osrm')
                        logger.info(f"Distancia calculada con OSRM entre {location1} y {location2}: {distance:.1f} km")
                        return distance
            except Exception as e:
                logger.warning(f"Error usando OSRM: {str(e)}")
            
            # Si OSRM falla, usar Geopy como respaldo
            distance = geodesic(coords1, coords2).kilometers
            # Guardar en la caché
            self.cache.save_distance(loc1_norm, loc2_norm, distance, 'geopy')
            logger.info(f"Distancia calculada con Geopy entre {location1} y {location2}: {distance:.1f} km")
            return distance
            
        except Exception as e:
            logger.error(f"Error calculando distancia entre {location1} y {location2}: {str(e)}")
            raise
        
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza los nombres de las columnas del DataFrame."""
        # Mapeo exacto de las columnas que tenemos
        column_mapping = {
            'Código': ['codigo', 'Código'],
            'Denominación': ['denominacion', 'Denominación'],
            'Nombre': ['nombre', 'Nombre'],
            'Dependencia': ['dependencia', 'Dependencia'],
            'Localidad': ['localidad', 'Localidad'],
            'Municipio': ['municipio', 'Municipio'],
            'Provincia': ['provincia', 'Provincia'],
            'Código Postal': ['codigo_postal', 'Cód.Postal']
        }
        
        # Crear un nuevo DataFrame con las columnas normalizadas
        normalized_df = pd.DataFrame()
        
        for normalized_name, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    normalized_df[normalized_name] = df[col]
                    print(f"Mapeando columna '{col}' a '{normalized_name}'")
                    break
        
        return normalized_df
        
    def load_centers_data(self, data_path: str, provincias_seleccionadas: List[str] = None) -> pd.DataFrame:
        """
        Carga los datos de los centros desde los archivos CSV.
        
        Args:
            data_path: Ruta al directorio de datos
            provincias_seleccionadas: Lista de provincias a cargar. Si es None, carga todas.
            
        Returns:
            DataFrame con los datos de los centros
        """
        all_data = []
        
        # Si no se especifican provincias, usar todas las disponibles
        if provincias_seleccionadas is None:
            provincias_seleccionadas = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d))]
        
        # Recorrer los directorios de las provincias seleccionadas
        for province_dir in provincias_seleccionadas:
            province_path = os.path.join(data_path, province_dir)
            if os.path.isdir(province_path):
                # Buscar archivos CSV en el directorio de la provincia
                for file in os.listdir(province_path):
                    if file.endswith('.csv'):
                        file_path = os.path.join(province_path, file)
                        print(f"\nLeyendo archivo: {file_path}")
                        try:
                            # Intentar primero con UTF-8
                            df = pd.read_csv(file_path, encoding='utf-8')
                        except UnicodeDecodeError:
                            try:
                                # Si falla, intentar con Windows-1252
                                df = pd.read_csv(file_path, encoding='windows-1252')
                            except UnicodeDecodeError:
                                # Si también falla, intentar con ISO-8859-1
                                df = pd.read_csv(file_path, encoding='iso-8859-1')
                        print(f"Columnas originales: {df.columns.tolist()}")
                        # Normalizar nombres de columnas
                        df = self._normalize_column_names(df)
                        print(f"Columnas después de normalizar: {df.columns.tolist()}")
                        # No necesitamos añadir la provincia ya que viene en el CSV
                        all_data.append(df)
        
        if not all_data:
            raise ValueError("No se encontraron archivos CSV en el directorio de datos")
            
        final_df = pd.concat(all_data, ignore_index=True)
        print("\nColumnas finales del DataFrame:", final_df.columns.tolist())
        return final_df
        
    def _normalize_city_name(self, city_name: str) -> str:
        """
        Normaliza el nombre de una ciudad para que tenga el formato correcto.
        Primera letra de cada palabra en mayúscula, resto en minúscula.
        
        Args:
            city_name: Nombre de la ciudad a normalizar
            
        Returns:
            Nombre normalizado
        """
        # Dividir por espacios y guiones
        words = city_name.replace('-', ' ').split()
        # Capitalizar cada palabra
        normalized_words = [word.capitalize() for word in words]
        # Unir las palabras
        return ' '.join(normalized_words)

    def get_unique_localities(self, df: pd.DataFrame) -> List[Dict]:
        """Obtiene una lista única de localidades con sus provincias."""
        # Asegurarse de que las columnas necesarias existen
        required_columns = ['Localidad', 'Provincia']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print("Columnas disponibles:", df.columns.tolist())
            raise ValueError(f"Faltan las siguientes columnas en el DataFrame: {missing_columns}")
        
        # Normalizar los nombres de las localidades
        df['Localidad'] = df['Localidad'].apply(self._normalize_city_name)
        
        # Obtener localidades únicas y convertirlas a diccionario
        unique_localities = df[required_columns].drop_duplicates()
        
        # Convertir a lista de diccionarios y asegurar que los valores son strings
        result = []
        for _, row in unique_localities.iterrows():
            result.append({
                'Localidad': str(row['Localidad']),
                'Provincia': str(row['Provincia'])
            })
        
        return result
        
    def sort_localities_by_distance(self, reference_locations: List[Dict], localities: List[Dict]) -> List[Dict]:
        """
        Ordena las localidades siguiendo el criterio de proximidad a las localidades de referencia.
        Solo calcula distancias desde las ciudades de referencia.
        """
        print("\nIniciando ordenación de localidades...")
        print(f"Número de localidades de referencia: {len(reference_locations)}")
        print(f"Número total de localidades a ordenar: {len(localities)}")
        
        # Crear un conjunto de todas las localidades (incluyendo las de referencia)
        all_localities = []
        reference_cities = {loc['nombre']: loc for loc in reference_locations}
        
        # Añadir primero las localidades de referencia
        for ref_loc in reference_locations:
            all_localities.append({
                'Localidad': str(ref_loc['nombre']),
                'Provincia': str(ref_loc['Provincia']),
                'radio': ref_loc.get('radio', 50)  # Radio por defecto de 50km
            })
            print(f"Añadida localidad de referencia: {ref_loc['nombre']} ({ref_loc['Provincia']}) con radio {ref_loc.get('radio', 50)}km")
        
        # Añadir el resto de localidades
        for loc in localities:
            if loc['Localidad'] not in reference_cities:
                all_localities.append({
                    'Localidad': str(loc['Localidad']),
                    'Provincia': str(loc['Provincia'])
                })
        
        # Para cada localidad, calcular su distancia a cada punto de referencia
        locality_distances = []
        for locality in all_localities:
            distances = []
            for ref_loc in reference_locations:
                try:
                    # Solo calculamos la distancia si la localidad actual no es una ciudad de referencia
                    if locality['Localidad'] != ref_loc['nombre']:
                        distance = self.get_distance(
                            ref_loc['nombre'], ref_loc['Provincia'],
                            locality['Localidad'], locality['Provincia']
                        )
                        # Verificar si la localidad está dentro del radio de la ciudad de referencia
                        if distance <= ref_loc.get('radio', 50):
                            distances.append((ref_loc['nombre'], distance))
                            print(f"Localidad {locality['Localidad']} ({locality['Provincia']}) dentro del radio de {ref_loc['nombre']} ({distance:.1f} km)")
                        else:
                            print(f"Localidad {locality['Localidad']} ({locality['Provincia']}) fuera del radio de {ref_loc['nombre']} ({distance:.1f} km > {ref_loc.get('radio', 50)} km)")
                            distances.append((ref_loc['nombre'], float('inf')))
                    else:
                        # Si es la misma ciudad, distancia 0
                        distances.append((ref_loc['nombre'], 0.0))
                        print(f"Localidad {locality['Localidad']} es la ciudad de referencia {ref_loc['nombre']}")
                except Exception as e:
                    print(f"Error calculando distancia entre {ref_loc['nombre']} y {locality['Localidad']}: {str(e)}")
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
            print(f"Localidad {locality['Localidad']} ({locality['Provincia']}) más cercana a {closest_ref_name} (índice {closest_ref_index})")
        
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
        print("\nOrden final de localidades:")
        for i, loc in enumerate(final_order):
            print(f"{i+1}. {loc['Localidad']} ({loc['Provincia']})")
        
        # Imprimir estadísticas de la caché
        self.cache.print_stats()
        
        return final_order 