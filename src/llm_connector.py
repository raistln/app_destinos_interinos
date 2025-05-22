import os
from typing import List, Dict
import yaml
import requests
import openai
import pandas as pd
from distance_calculator import DistanceCalculator

class LLMConnector:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.provider = self.config['llm']['provider']
        self._setup_provider()
        self.distance_calculator = DistanceCalculator()
    
    def _load_config(self, config_path: str) -> Dict:
        """Carga la configuración desde el archivo YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_provider(self):
        """Configura el proveedor de LLM seleccionado."""
        provider_config = self.config['llm']['models'][self.provider]
        
        if self.provider == 'mistral':
            self.api_key = provider_config['api_key']
            if not self.api_key:
                raise ValueError("API key de Mistral no encontrada en la configuración")
            self.api_url = provider_config['api_url']
            self.model = provider_config['name']
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == 'openai':
            self.api_key = provider_config['api_key']
            if not self.api_key:
                raise ValueError("API key de OpenAI no encontrada en la configuración")
            openai.api_key = self.api_key
            self.model = provider_config['name']
        else:
            raise ValueError(f"Proveedor no soportado: {self.provider}")
    
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

    def generate_prompt(self, 
                       tipo_centro: str,
                       provincias: List[str],
                       ciudades_preferencia: List[str],
                       datos_centros: List[Dict]) -> str:
        """
        Genera la lista ordenada de localidades.
        
        Args:
            tipo_centro: Tipo de centro educativo
            provincias: Lista de provincias seleccionadas
            ciudades_preferencia: Lista de ciudades en orden de preferencia
            datos_centros: Lista de diccionarios con datos de los centros
            
        Returns:
            str con la lista ordenada
        """
        # Convertir los datos a DataFrame y asegurarnos de que tiene las columnas correctas
        df = pd.DataFrame(datos_centros)
        
        # Normalizar los nombres de las ciudades en el DataFrame
        df['Localidad'] = df['Localidad'].apply(self._normalize_city_name)
        
        # Verificar que tenemos datos de todas las provincias seleccionadas
        provincias_en_datos = df['Provincia'].unique()
        print(f"Provincias en los datos: {provincias_en_datos}")
        print(f"Provincias seleccionadas: {provincias}")
        
        # Asegurarnos de que las columnas tienen los nombres correctos
        df = df.rename(columns={
            'codigo': 'Código',
            'denominacion': 'Denominación',
            'nombre': 'Nombre',
            'dependencia': 'Dependencia',
            'localidad': 'Localidad',
            'municipio': 'Municipio',
            'provincia': 'Provincia',
            'codigo_postal': 'Código Postal'
        })
        
        # Crear las localidades de referencia con sus provincias correctas
        self.reference_locations = []
        for ciudad in ciudades_preferencia:
            # Normalizar el nombre de la ciudad
            ciudad_normalizada = self._normalize_city_name(ciudad)
            # Buscar la ciudad en el DataFrame para obtener su provincia
            ciudad_data = df[df['Localidad'].str.lower() == ciudad_normalizada.lower()]
            if not ciudad_data.empty:
                provincia = ciudad_data.iloc[0]['Provincia']
            else:
                # Si no se encuentra en el DataFrame, buscar en las provincias seleccionadas
                provincia = next((p for p in provincias if ciudad_normalizada.lower() in p.lower()), provincias[0])
            self.reference_locations.append({'Localidad': ciudad_normalizada, 'Provincia': provincia})
            print(f"Ciudad de referencia: {ciudad_normalizada} ({provincia})")
        
        # Ordenar las localidades usando el DistanceCalculator
        all_localities = self.distance_calculator.get_unique_localities(df)
        print(f"Número total de localidades a ordenar: {len(all_localities)}")
        
        # Verificar que tenemos localidades de todas las provincias
        localidades_por_provincia = {}
        for loc in all_localities:
            prov = loc['Provincia']
            if prov not in localidades_por_provincia:
                localidades_por_provincia[prov] = []
            localidades_por_provincia[prov].append(loc['Localidad'])
        
        print("Localidades por provincia:")
        for prov, locs in localidades_por_provincia.items():
            print(f"{prov}: {len(locs)} localidades")
        
        sorted_localities = self.distance_calculator.sort_localities_by_distance(self.reference_locations, all_localities)
        
        # Devolver solo la lista ordenada
        return self._format_sorted_localities(sorted_localities)
    
    def _format_sorted_localities(self, sorted_localities: List[Dict]) -> str:
        """
        Formatea la lista ordenada de localidades incluyendo la ciudad de referencia y la distancia.
        
        Args:
            sorted_localities: Lista de diccionarios con localidades ordenadas
            
        Returns:
            str con la lista formateada
        """
        formatted_list = []
        for i, loc in enumerate(sorted_localities):
            # Calcular la distancia a cada ciudad de referencia
            distances = []
            for ref_loc in self.reference_locations:
                try:
                    distance = self.distance_calculator.get_distance(
                        ref_loc['Localidad'], ref_loc['Provincia'],
                        loc['Localidad'], loc['Provincia']
                    )
                    distances.append((ref_loc['Localidad'], distance))
                except Exception as e:
                    print(f"Error calculando distancia: {str(e)}")
                    distances.append((ref_loc['Localidad'], float('inf')))
            
            # Encontrar la ciudad de referencia más cercana
            closest_ref = min(distances, key=lambda x: x[1])
            
            # Formatear la línea con la información de distancia
            formatted_list.append(
                f"{i+1}. {loc['Localidad']} ({loc['Provincia']}) - "
                f"Cerca de {closest_ref[0]} ({closest_ref[1]:.1f} km)"
            )
        
        return "\n".join(formatted_list)
    
    def _format_centros_data(self, datos_centros: List[Dict]) -> str:
        """Formatea los datos de los centros para el prompt."""
        if not datos_centros:
            return "No hay datos de centros disponibles."
        
        ejemplo = datos_centros[0]
        return f"""
Ejemplo de datos de centro:
- Código: {ejemplo.get('Código', 'N/A')}
- Denominación: {ejemplo.get('Denominación', 'N/A')}
- Nombre: {ejemplo.get('Nombre', 'N/A')}
- Dependencia: {ejemplo.get('Dependencia', 'N/A')}
- Localidad: {ejemplo.get('Localidad', 'N/A')}
- Municipio: {ejemplo.get('Municipio', 'N/A')}
- Provincia: {ejemplo.get('Provincia', 'N/A')}
- Código Postal: {ejemplo.get('Código Postal', 'N/A')}
"""
    
    def _format_ciudades_preferencia(self, ciudades: List[str]) -> str:
        """Formatea la lista de ciudades de preferencia para el prompt."""
        return "\n".join([f"{i+1}. {ciudad}" for i, ciudad in enumerate(ciudades)])
    
    def process_with_llm(self, prompt: str) -> str:
        """
        Procesa el prompt con el LLM seleccionado.
        
        Args:
            prompt: Prompt a procesar
            
        Returns:
            str con la respuesta del LLM
        """
        # En este caso, el prompt ya es la lista ordenada, así que lo devolvemos directamente
        return prompt
    
    def _process_with_mistral(self, prompt: str) -> str:
        """Procesa el prompt usando la API de Mistral."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un asistente especializado en ordenar localidades según proximidad geográfica."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config['llm']['temperature'],
            "max_tokens": self.config['llm']['max_tokens']
        }
        
        response = requests.post(
            self.api_url,
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Error en la API de Mistral: {response.status_code} - {response.text}"
    
    def _process_with_openai(self, prompt: str) -> str:
        """Procesa el prompt usando la API de OpenAI."""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Eres un asistente especializado en ordenar localidades según proximidad geográfica."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config['llm']['temperature'],
            max_tokens=self.config['llm']['max_tokens']
        )
        return response.choices[0].message.content 