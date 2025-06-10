import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from .db_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class DistanceCache:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.distances_df = pd.DataFrame()  # Inicializar DataFrame vacío
        self._load_distances()
    
    def _load_distances(self):
        """Carga todas las distancias de la base de datos a un DataFrame."""
        try:
            with self.db_manager.get_connection() as conn:
                # Obtener todas las ciudades de referencia
                query = """
                    SELECT id, nombre_normalizado 
                    FROM ciudades_referencia 
                    ORDER BY nombre_normalizado
                """
                ciudades_df = pd.read_sql_query(query, conn)
                
                if ciudades_df.empty:
                    logger.warning("No hay ciudades de referencia en la base de datos")
                    return
                
                # Crear DataFrame vacío con las ciudades de referencia como columnas
                self.distances_df = pd.DataFrame(columns=ciudades_df['nombre_normalizado'])
                
                # Obtener todas las distancias calculadas
                query = """
                    SELECT 
                        c1.nombre_normalizado as origen,
                        c2.nombre_normalizado as destino,
                        d.distancia_km,
                        d.tipo_calculo
                    FROM distancias_calculadas d
                    JOIN ciudades_referencia c1 ON d.centro_id = c1.id
                    JOIN ciudades_referencia c2 ON d.ciudad_id = c2.id
                """
                distancias_df = pd.read_sql_query(query, conn)
                
                if not distancias_df.empty:
                    # Crear matriz de distancias
                    pivot_df = distancias_df.pivot(
                        index='origen',
                        columns='destino',
                        values='distancia_km'
                    )
                    # Actualizar el DataFrame con las distancias existentes
                    self.distances_df = self.distances_df.combine_first(pivot_df)
                    logger.info(f"Matriz de distancias cargada con {len(self.distances_df)} orígenes y {len(self.distances_df.columns)} destinos")
                else:
                    logger.info("No hay distancias en la base de datos. DataFrame vacío creado.")
                
        except Exception as e:
            logger.error(f"Error cargando distancias: {str(e)}")
            self.distances_df = pd.DataFrame()
    
    def get_distance(self, origen: str, destino: str) -> Optional[float]:
        """Obtiene la distancia entre dos ciudades desde el DataFrame."""
        try:
            if origen in self.distances_df.index and destino in self.distances_df.columns:
                return self.distances_df.loc[origen, destino]
            return None
        except (KeyError, ValueError):
            return None
    
    def save_distance(self, origen: str, destino: str, distancia: float, tipo_calculo: str = 'osrm'):
        """Guarda una distancia tanto en el DataFrame como en la base de datos."""
        try:
            # Asegurarse de que el origen existe como índice
            if origen not in self.distances_df.index:
                self.distances_df.loc[origen] = np.nan
            
            # Guardar en el DataFrame
            self.distances_df.loc[origen, destino] = distancia
            
            # Guardar en la base de datos
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Obtener IDs de las ciudades
                cursor.execute("SELECT id FROM ciudades_referencia WHERE nombre_normalizado = ?", (origen,))
                origen_id = cursor.fetchone()
                cursor.execute("SELECT id FROM ciudades_referencia WHERE nombre_normalizado = ?", (destino,))
                destino_id = cursor.fetchone()
                
                if origen_id and destino_id:
                    cursor.execute("""
                        INSERT INTO distancias_calculadas (centro_id, ciudad_id, distancia_km, tipo_calculo)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(centro_id, ciudad_id) DO UPDATE SET
                            distancia_km = excluded.distancia_km,
                            tipo_calculo = excluded.tipo_calculo,
                            fecha_calculo = CURRENT_TIMESTAMP
                    """, (origen_id[0], destino_id[0], distancia, tipo_calculo))
                    conn.commit()
                    logger.info(f"Distancia guardada: {origen} -> {destino}: {distancia:.1f} km")
                else:
                    logger.warning(f"No se encontraron IDs para {origen} o {destino}")
                    
        except Exception as e:
            logger.error(f"Error guardando distancia: {str(e)}")
    
    def get_missing_distances(self) -> List[Tuple[str, str]]:
        """Obtiene la lista de pares de ciudades que no tienen distancia calculada."""
        missing = []
        for origen in self.distances_df.index:
            for destino in self.distances_df.columns:
                if pd.isna(self.distances_df.loc[origen, destino]):
                    missing.append((origen, destino))
        return missing
    
    def export_to_csv(self, filename: str = "distancias.csv"):
        """Exporta la matriz de distancias a un archivo CSV."""
        try:
            self.distances_df.to_csv(filename)
            logger.info(f"Matriz de distancias exportada a {filename}")
        except Exception as e:
            logger.error(f"Error exportando a CSV: {str(e)}")
    
    def print_stats(self):
        """Imprime estadísticas sobre las distancias almacenadas."""
        if self.distances_df.empty:
            print("\nNo hay distancias almacenadas en la caché.")
            return
            
        total = len(self.distances_df.index) * len(self.distances_df.columns)
        calculadas = self.distances_df.count().sum()
        print(f"\nEstadísticas de distancias:")
        print(f"Total de pares posibles: {total}")
        print(f"Distancias calculadas: {calculadas}")
        print(f"Distancias faltantes: {total - calculadas}")
        print(f"Porcentaje completado: {(calculadas/total)*100:.1f}%") 