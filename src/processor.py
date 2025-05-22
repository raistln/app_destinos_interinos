import pandas as pd
from pathlib import Path
from typing import List, Dict
import os
import yaml

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
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
        tipo_archivo = "institutos.csv" if "IES" in tipo_centro else "colegios.csv"
        
        # Mapeo de nombres de provincias con tildes a nombres de directorios sin tildes
        nombre_directorio = {
            'Almería': 'Almeria',
            'Cádiz': 'Cadiz',
            'Córdoba': 'Cordoba',
            'Granada': 'Granada',
            'Huelva': 'Huelva',
            'Jaén': 'Jaen',
            'Málaga': 'Malaga',
            'Sevilla': 'Sevilla'
        }
        
        for provincia in provincias:
            # Obtener el nombre del directorio sin tilde
            dir_name = nombre_directorio.get(provincia, provincia)
            archivo = self.data_dir / dir_name / tipo_archivo
            print(f"\nIntentando cargar archivo: {archivo}")
            
            if archivo.exists():
                try:
                    # Intentar primero con UTF-8
                    df = pd.read_csv(archivo, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        # Si falla, intentar con Windows-1252
                        df = pd.read_csv(archivo, encoding='windows-1252')
                    except UnicodeDecodeError:
                        # Si también falla, intentar con ISO-8859-1
                        df = pd.read_csv(archivo, encoding='iso-8859-1')
                
                # Asegurarnos de que la columna de provincia existe y tiene el valor correcto
                if 'provincia' not in df.columns:
                    df['provincia'] = provincia
                else:
                    # Si existe, asegurarnos de que todos los valores son correctos
                    df['provincia'] = provincia
                
                print(f"Archivo cargado: {archivo}")
                print(f"Número de registros: {len(df)}")
                print(f"Columnas: {df.columns.tolist()}")
                dfs.append(df)
            else:
                print(f"ADVERTENCIA: No se encontró el archivo {archivo}")
        
        if not dfs:
            print("ADVERTENCIA: No se encontraron archivos CSV para las provincias seleccionadas")
            return pd.DataFrame()
            
        # Concatenar todos los DataFrames
        final_df = pd.concat(dfs, ignore_index=True)
        print(f"\nDataFrame final:")
        print(f"Número total de registros: {len(final_df)}")
        print(f"Registros por provincia: {final_df['provincia'].value_counts().to_dict()}")
        return final_df
    
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