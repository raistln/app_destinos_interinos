import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from typing import Dict, List, Tuple
import time
import requests

class DistanceCalculator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="preferencia_interinos")
        self.coordinates_cache: Dict[str, Tuple[float, float]] = {}
        self.distance_cache: Dict[Tuple[str, str], float] = {}
        self.osrm_url = "http://router.project-osrm.org/route/v1/driving"
        
    def _get_coordinates(self, location: str, province: str) -> Tuple[float, float]:
        """
        Obtiene las coordenadas de una localidad usando el caché si está disponible.
        
        Args:
            location: Nombre de la localidad
            province: Nombre de la provincia
            
        Returns:
            Tupla con (latitud, longitud)
        """
        cache_key = f"{location}, {province}, España"
        
        if cache_key in self.coordinates_cache:
            return self.coordinates_cache[cache_key]
            
        try:
            # Añadir un pequeño delay para no sobrecargar la API
            time.sleep(1)
            
            # Intentar primero con el nombre exacto y provincia
            location_data = self.geolocator.geocode(cache_key)
            
            # Si no se encuentra, intentar con más contexto
            if not location_data:
                # Intentar con "Municipio de" o "Villa de"
                for prefix in ["Municipio de", "Villa de"]:
                    alt_query = f"{prefix} {location}, {province}, España"
                    location_data = self.geolocator.geocode(alt_query)
                    if location_data:
                        break
            
            # Si aún no se encuentra, intentar con Andalucía
            if not location_data:
                location_data = self.geolocator.geocode(f"{location}, {province}, Andalucía, España")
            
            if location_data:
                coords = (location_data.latitude, location_data.longitude)
                self.coordinates_cache[cache_key] = coords
                print(f"Coordenadas encontradas para {cache_key}: {coords}")
                return coords
            else:
                print(f"ADVERTENCIA: No se encontraron coordenadas para {cache_key}")
                # Intentar con una búsqueda más amplia
                location_data = self.geolocator.geocode(f"{location}, España")
                if location_data:
                    coords = (location_data.latitude, location_data.longitude)
                    self.coordinates_cache[cache_key] = coords
                    print(f"Coordenadas encontradas (búsqueda amplia) para {cache_key}: {coords}")
                    return coords
                raise ValueError(f"No se encontraron coordenadas para {cache_key}")
        except Exception as e:
            print(f"Error al obtener coordenadas para {cache_key}: {str(e)}")
            return None
            
    def get_distance(self, location1: str, province1: str, location2: str, province2: str) -> float:
        """
        Calcula la distancia por carretera entre dos localidades en kilómetros usando OSRM.
        
        Args:
            location1: Primera localidad
            province1: Provincia de la primera localidad
            location2: Segunda localidad
            province2: Provincia de la segunda localidad
            
        Returns:
            Distancia en kilómetros
        """
        cache_key = (f"{location1}, {province1}", f"{location2}, {province2}")
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]
            
        coords1 = self._get_coordinates(location1, province1)
        coords2 = self._get_coordinates(location2, province2)
        
        if coords1 and coords2:
            try:
                # Construir la URL para OSRM
                url = f"{self.osrm_url}/{coords1[1]},{coords1[0]};{coords2[1]},{coords2[0]}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['code'] == 'Ok':
                        # La distancia viene en metros, convertir a kilómetros
                        distance = data['routes'][0]['distance'] / 1000
                        self.distance_cache[cache_key] = distance
                        return distance
                
                # Si OSRM falla, usar distancia en línea recta como fallback
                print(f"ADVERTENCIA: OSRM falló para {location1}-{location2}, usando distancia en línea recta")
                distance = geodesic(coords1, coords2).kilometers
                self.distance_cache[cache_key] = distance
                return distance
                
            except Exception as e:
                print(f"Error al calcular distancia por carretera entre {location1} y {location2}: {str(e)}")
                # Fallback a distancia en línea recta
                distance = geodesic(coords1, coords2).kilometers
                self.distance_cache[cache_key] = distance
                return distance
                
        return float('inf')
        
    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza los nombres de las columnas del DataFrame."""
        # Mapeo exacto de las columnas que tenemos
        column_mapping = {
            'Código': ['codigo'],
            'Nombre': ['nombre'],
            'Localidad': ['localidad'],
            'Municipio': ['municipio'],
            'Provincia': ['provincia'],
            'Dirección': ['direccion'],
            'Código Postal': ['codigo_postal']
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
        
    def load_centers_data(self, data_path: str) -> pd.DataFrame:
        """Carga los datos de los centros desde los archivos CSV."""
        all_data = []
        
        # Recorrer todos los directorios de provincias
        for province_dir in os.listdir(data_path):
            province_path = os.path.join(data_path, province_dir)
            if os.path.isdir(province_path):
                # Buscar archivos CSV en el directorio de la provincia
                for file in os.listdir(province_path):
                    if file.endswith('.csv'):
                        file_path = os.path.join(province_path, file)
                        print(f"\nLeyendo archivo: {file_path}")
                        df = pd.read_csv(file_path)
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
        
    def get_unique_localities(self, df: pd.DataFrame) -> List[Dict]:
        """Obtiene una lista única de localidades con sus provincias."""
        # Asegurarse de que las columnas necesarias existen
        required_columns = ['Localidad', 'Provincia']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print("Columnas disponibles:", df.columns.tolist())
            raise ValueError(f"Faltan las siguientes columnas en el DataFrame: {missing_columns}")
            
        unique_localities = df[required_columns].drop_duplicates()
        return unique_localities.to_dict('records')
        
    def sort_localities_by_distance(self, reference_locations: List[Dict], localities: List[Dict]) -> List[Dict]:
        """
        Ordena las localidades siguiendo el criterio de proximidad a las localidades de referencia.
        
        Args:
            reference_locations: Lista de diccionarios con localidades de referencia en orden de prioridad
            localities: Lista de diccionarios con localidades a ordenar
            
        Returns:
            Lista ordenada de localidades
        """
        # Crear un conjunto de todas las localidades (incluyendo las de referencia)
        all_localities = []
        reference_cities = {loc['Localidad']: loc for loc in reference_locations}
        
        # Añadir primero las localidades de referencia
        for ref_loc in reference_locations:
            all_localities.append(ref_loc)
        
        # Añadir el resto de localidades
        for loc in localities:
            if loc['Localidad'] not in reference_cities:
                all_localities.append(loc)
        
        # Para cada localidad, calcular su distancia a cada punto de referencia
        locality_distances = []
        for locality in all_localities:
            distances = []
            for ref_loc in reference_locations:
                try:
                    distance = self.get_distance(
                        ref_loc['Localidad'], ref_loc['Provincia'],
                        locality['Localidad'], locality['Provincia']
                    )
                    distances.append((ref_loc['Localidad'], distance))
                except Exception as e:
                    print(f"Error calculando distancia entre {ref_loc['Localidad']} y {locality['Localidad']}: {str(e)}")
                    distances.append((ref_loc['Localidad'], float('inf')))
            
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
        
        # Ordenar las localidades:
        # 1. Primero por el índice de la localidad de referencia más cercana (prioridad)
        # 2. Luego por la distancia a esa localidad de referencia
        def sort_key(item):
            locality, distance, ref_index, ref_name = item
            return (ref_index, distance)
        
        # Ordenar y devolver solo las localidades
        sorted_localities = [loc for loc, _, _, _ in sorted(locality_distances, key=sort_key)]
        
        # Verificar y reordenar si es necesario
        final_order = []
        current_ref_index = 0
        
        while current_ref_index < len(reference_locations):
            current_ref = reference_locations[current_ref_index]
            next_ref = reference_locations[current_ref_index + 1] if current_ref_index + 1 < len(reference_locations) else None
            
            # Agrupar localidades por su referencia más cercana
            current_group = []
            for loc in sorted_localities:
                if loc in final_order:
                    continue
                    
                # Calcular distancias a las referencias actual y siguiente
                dist_to_current = self.get_distance(
                    current_ref['Localidad'], current_ref['Provincia'],
                    loc['Localidad'], loc['Provincia']
                )
                
                if next_ref:
                    dist_to_next = self.get_distance(
                        next_ref['Localidad'], next_ref['Provincia'],
                        loc['Localidad'], loc['Provincia']
                    )
                    
                    # Si está más cerca de la siguiente referencia, dejarlo para el siguiente grupo
                    if dist_to_next < dist_to_current:
                        continue
                
                current_group.append((loc, dist_to_current))
            
            # Ordenar el grupo actual por distancia
            current_group.sort(key=lambda x: x[1])
            
            # Añadir al orden final
            final_order.extend([loc for loc, _ in current_group])
            
            current_ref_index += 1
        
        # Añadir cualquier localidad que se haya quedado sin asignar
        remaining = [loc for loc in sorted_localities if loc not in final_order]
        final_order.extend(remaining)
        
        return final_order 