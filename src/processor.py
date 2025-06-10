import pandas as pd
from pathlib import Path
from typing import List, Dict
import os
import yaml
from distance_calculator import DistanceCalculator
from database.db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        # Inicializar la base de datos
        self.db_manager = DatabaseManager("data/distancias_cache.db")
        self.distance_calculator = DistanceCalculator()
        
    def _normalize_province_name(self, provincia: str) -> str:
        """
        Normaliza el nombre de la provincia para que coincida con el nombre del directorio.
        """
        # Mapeo de nombres con tildes a nombres sin tildes
        province_mapping = {
            "Almería": "Almeria",
            "Cádiz": "Cadiz",
            "Córdoba": "Cordoba",
            "Granada": "Granada",
            "Huelva": "Huelva",
            "Jaén": "Jaen",
            "Málaga": "Malaga",
            "Sevilla": "Sevilla"
        }
        return province_mapping.get(provincia, provincia)
        
    def load_data(self, provincias: List[str], tipo_centro: str) -> pd.DataFrame:
        """
        Carga los datos de los centros educativos para las provincias seleccionadas.
        
        Args:
            provincias: Lista de provincias seleccionadas
            tipo_centro: Tipo de centro ("Institutos (IES)" o "Colegios (CEIP)")
            
        Returns:
            DataFrame con los datos de los centros
        """
        dfs = []
        
        for provincia in provincias:
            # Normalizar el nombre de la provincia
            provincia_normalizada = self._normalize_province_name(provincia)
            
            # Determinar el nombre del archivo según el tipo de centro
            if tipo_centro == "Institutos (IES)":
                archivo = f"data/{provincia_normalizada}/centros_educativos_secundaria.csv"
            else:  # Colegios (CEIP)
                archivo = f"data/{provincia_normalizada}/centros_educativos_primaria.csv"
            
            try:
                print(f"Intentando cargar archivo: {archivo}")
                # Intentar diferentes codificaciones
                for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(archivo, encoding=encoding)
                        print(f"Archivo cargado con codificación {encoding}: {archivo}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                # Corregir nombres de columnas
                df.columns = [col.encode('latin1').decode('utf-8') if isinstance(col, str) else col for col in df.columns]
                
                # Asegurar que la columna Provincia existe
                if 'Provincia' not in df.columns:
                    df['Provincia'] = provincia
                
                dfs.append(df)
                print(f"Archivo cargado: {archivo}")
                print(f"Número de registros: {len(df)}")
                print(f"Columnas: {df.columns.tolist()}")
                
            except Exception as e:
                print(f"Error al cargar {archivo}: {str(e)}")
                continue
        
        if not dfs:
            return pd.DataFrame()
        
        # Combinar todos los DataFrames
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Mostrar información de depuración
        print("\nDataFrame final:")
        print(f"Número total de registros: {len(df_final)}")
        print(f"Registros por provincia: {df_final['Provincia'].value_counts().to_dict()}")
        
        return df_final
    
    def process_preferences(self, 
                          df: pd.DataFrame, 
                          ciudades_preferencia: List[str]) -> List[Dict]:
        """
        Procesa las preferencias y ordena los centros según la proximidad.
        
        Args:
            df: DataFrame con los datos de los centros
            ciudades_preferencia: Lista de ciudades en orden de preferencia
            
        Returns:
            Lista de diccionarios con los centros ordenados
        """
        # TODO: Implementar la lógica de ordenamiento usando el LLM
        return []
    
    def save_configuration(self, 
                          config: Dict, 
                          nombre: str) -> bool:
        """
        Guarda la configuración actual.
        
        Args:
            config: Diccionario con la configuración
            nombre: Nombre para guardar la configuración
            
        Returns:
            bool indicando si se guardó correctamente
        """
        try:
            config_dir = Path("saved_configs")
            config_dir.mkdir(exist_ok=True)
            
            with open(config_dir / f"{nombre}.yaml", "w") as f:
                yaml.dump(config, f)
            return True
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")
            return False
    
    def load_configuration(self, nombre: str) -> Dict:
        """
        Carga una configuración guardada.
        
        Args:
            nombre: Nombre de la configuración a cargar
            
        Returns:
            Diccionario con la configuración
        """
        try:
            config_path = Path("saved_configs") / f"{nombre}.yaml"
            if config_path.exists():
                with open(config_path, "r") as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            return {} 