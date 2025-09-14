import os
import logging
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
import streamlit as st
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class SupabaseManager:
    """
    Gestor de base de datos PostgreSQL usando Supabase.
    Maneja conexiones y operaciones de base de datos para el caché de distancias y coordenadas.
    """
    
    def __init__(self):
        """Inicializa el gestor de Supabase."""
        self.supabase_url = self._get_supabase_url()
        self.supabase_key = self._get_supabase_key()
        
        # Validar que tenemos las credenciales necesarias
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL no está configurada. Verifica tu archivo secrets.toml o variables de entorno.")
        if not self.supabase_key:
            raise ValueError("SUPABASE_KEY no está configurada. Verifica tu archivo secrets.toml o variables de entorno.")
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self._initialize_tables()
    
    def _get_supabase_url(self) -> str:
        """Obtiene la URL de Supabase desde las variables de entorno o secrets."""
        # Cargar .env solo una vez
        load_dotenv()
        
        # Prioridad: 1. Streamlit secrets, 2. Variables de entorno
        try:
            if hasattr(st, 'secrets') and "SUPABASE_URL" in st.secrets:
                return st.secrets["SUPABASE_URL"]
        except Exception:
            # st.secrets puede no estar disponible en algunos contextos
            pass
        
        # Fallback a variables de entorno
        url = os.getenv("SUPABASE_URL")
        return url if url else ""
    
    def _get_supabase_key(self) -> str:
        """Obtiene la clave de Supabase desde las variables de entorno o secrets."""
        # No necesitamos load_dotenv() de nuevo, ya se cargó en _get_supabase_url
        
        # Prioridad: 1. Streamlit secrets, 2. Variables de entorno
        try:
            if hasattr(st, 'secrets') and "SUPABASE_KEY" in st.secrets:
                return st.secrets["SUPABASE_KEY"]
        except Exception:
            # st.secrets puede no estar disponible en algunos contextos
            pass
        
        # Fallback a variables de entorno
        key = os.getenv("SUPABASE_KEY")
        return key if key else ""
    
    def _initialize_tables(self):
        """Inicializa las tablas necesarias si no existen."""
        try:
            # Crear tabla de ciudades si no existe
            self.supabase.rpc('create_ciudades_table_if_not_exists').execute()
            
            # Crear tabla de distancias si no existe
            self.supabase.rpc('create_distancias_table_if_not_exists').execute()
            
            logger.info("Tablas inicializadas correctamente")
        except Exception as e:
            logger.warning(f"No se pudieron crear las tablas automáticamente: {str(e)}")
            # Las tablas deben crearse manualmente en Supabase
    
    def get_city_coordinates(self, city_name: str, province: str = None) -> Optional[Dict]:
        """
        Obtiene las coordenadas de una ciudad desde la base de datos.
        
        Args:
            city_name: Nombre de la ciudad
            province: Provincia (opcional)
            
        Returns:
            Diccionario con información de la ciudad o None si no se encuentra
        """
        try:
            query = self.supabase.table('ciudades').select('*').eq('nombre', city_name)
            
            if province:
                query = query.eq('provincia', province)
            
            result = query.execute()
            
            if result.data:
                city_data = result.data[0]
                return {
                    'nombre': city_data['nombre'],
                    'provincia': city_data['provincia'],
                    'latitud': float(city_data['latitud']),
                    'longitud': float(city_data['longitud'])
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo coordenadas de {city_name}: {str(e)}")
            return None
    
    def save_city_coordinates(self, city_info: Dict) -> bool:
        """
        Guarda las coordenadas de una ciudad en la base de datos.
        
        Args:
            city_info: Diccionario con información de la ciudad
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            data = {
                'nombre': city_info['nombre'],
                'provincia': city_info['provincia'],
                'latitud': city_info['latitud'],
                'longitud': city_info['longitud']
            }
            
            # Usar upsert para insertar o actualizar
            result = self.supabase.table('ciudades').upsert(data).execute()
            
            if result.data:
                logger.info(f"Coordenadas guardadas para {city_info['nombre']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error guardando coordenadas: {str(e)}")
            return False
    
    def get_cached_distance(self, city1: str, city2: str) -> Optional[float]:
        """
        Obtiene una distancia cacheada entre dos ciudades.
        
        Args:
            city1: Primera ciudad
            city2: Segunda ciudad
            
        Returns:
            Distancia en kilómetros o None si no está cacheada
        """
        try:
            # Buscar en ambas direcciones
            result1 = self.supabase.table('distancias').select('distancia').eq('ciudad1', city1).eq('ciudad2', city2).execute()
            
            if result1.data:
                return float(result1.data[0]['distancia'])
            
            # Buscar en dirección inversa
            result2 = self.supabase.table('distancias').select('distancia').eq('ciudad1', city2).eq('ciudad2', city1).execute()
            
            if result2.data:
                return float(result2.data[0]['distancia'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo distancia cacheada entre {city1} y {city2}: {str(e)}")
            return None
    
    def save_distance(self, city1: str, city2: str, distance: float) -> bool:
        """
        Guarda una distancia calculada en el caché.
        
        Args:
            city1: Primera ciudad
            city2: Segunda ciudad
            distance: Distancia en kilómetros
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            data = {
                'ciudad1': city1,
                'ciudad2': city2,
                'distancia': distance
            }
            
            result = self.supabase.table('distancias').upsert(data).execute()
            
            if result.data:
                logger.info(f"Distancia guardada: {city1} -> {city2}: {distance:.1f} km")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error guardando distancia: {str(e)}")
            return False
    
    def get_cache_stats(self) -> Dict:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            cities_count = self.supabase.table('ciudades').select('id', count='exact').execute()
            distances_count = self.supabase.table('distancias').select('id', count='exact').execute()
            
            return {
                'ciudades': cities_count.count if cities_count.count else 0,
                'distancias': distances_count.count if distances_count.count else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {'ciudades': 0, 'distancias': 0}
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión a Supabase.
        
        Returns:
            True si la conexión es exitosa, False en caso contrario
        """
        try:
            # Intentar una consulta simple
            result = self.supabase.table('ciudades').select('id').limit(1).execute()
            logger.info("Conexión a Supabase exitosa")
            return True
            
        except Exception as e:
            logger.error(f"Error de conexión a Supabase: {str(e)}")
            return False