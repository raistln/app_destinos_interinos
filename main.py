import os
import sys
from src.llm_connector import LLMConnector
from src.distance_calculator import DistanceCalculator
import pandas as pd

def main():
    # Configurar el path para que Python pueda encontrar los módulos
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Crear instancia del LLMConnector
    llm = LLMConnector()
    
    # Ejemplo de uso
    tipo_centro = "IES"
    provincias = ["Granada", "Almería"]
    ciudades_preferencia = ["La Zubia", "Almuñécar", "Albuñol", "Campohermoso"]
    
    # Cargar datos de los centros
    distance_calc = DistanceCalculator()
    data_path = "data"
    
    try:
        # Cargar y mostrar información sobre los datos
        df = distance_calc.load_centers_data(data_path)
        print("\nDatos cargados correctamente:")
        print(f"Número de registros: {len(df)}")
        print(f"Columnas disponibles: {df.columns.tolist()}")
        print("\nPrimeras filas del DataFrame:")
        print(df.head())
        
        # Convertir a diccionario para el LLMConnector
        datos_centros = df.to_dict('records')
        
        # Generar el prompt y procesarlo
        prompt = llm.generate_prompt(
            tipo_centro=tipo_centro,
            provincias=provincias,
            ciudades_preferencia=ciudades_preferencia,
            datos_centros=datos_centros
        )
        
        # Procesar con el LLM
        result = llm.process_with_llm(prompt)
        print("\nResultado final:")
        print(result)
        
    except Exception as e:
        print(f"\nError al procesar los datos: {str(e)}")
        raise

if __name__ == "__main__":
    main() 