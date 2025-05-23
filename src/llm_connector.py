import os
from typing import List, Dict
import yaml
import requests
import openai
import pandas as pd
from distance_calculator import DistanceCalculator
from dotenv import load_dotenv

class LLMConnector:
    def __init__(self, config_path: str = "config/settings.yaml"):
        # Cargar configuración
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Configurar el modelo
        self.model = self.config['llm']['models']['mistral']['name']
        self.api_url = self.config['llm']['models']['mistral']['api_url']
        self.headers = {
            "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        # Inicializar el calculador de distancias
        self.distance_calculator = DistanceCalculator()
        self.reference_locations = []
    
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

    def generate_prompt(self, tipo_centro, provincias, ciudades_preferencia, datos_centros):
        """
        Genera un prompt para el LLM con los datos de los centros y las preferencias.
        
        Args:
            tipo_centro (str): Tipo de centro (IES o CEIP)
            provincias (list): Lista de provincias seleccionadas
            ciudades_preferencia (list): Lista de diccionarios con ciudades de preferencia y sus radios
            datos_centros (list): Lista de diccionarios con datos de los centros
        """
        # Normalizar nombres de ciudades de referencia
        ciudades_referencia = []
        for ciudad in ciudades_preferencia:
            ciudad_normalizada = self._normalize_city_name(ciudad['nombre'])
            # Usar la primera provincia seleccionada como referencia
            # Si la ciudad no está en el CSV, usaremos esta provincia para los cálculos
            ciudades_referencia.append({
                'nombre': ciudad['nombre'],
                'provincia': provincias[0],  # Usamos la primera provincia seleccionada
                'radio': ciudad['radio']
            })
            print(f"Ciudad de referencia: {ciudad['nombre']} (usando provincia {provincias[0]})")
        
        # Crear diccionario de distancias para cada centro
        distancias_centros = {}
        for centro in datos_centros:
            localidad = centro['Localidad']
            provincia = centro['Provincia']
            distancias = {}
            
            # Calcular distancia a cada ciudad de referencia
            for ref in ciudades_referencia:
                distancia = self.distance_calculator.get_distance(
                    location1=localidad,
                    province1=provincia,
                    location2=ref['nombre'],
                    province2=ref['provincia']
                )
                distancias[ref['nombre']] = distancia
            
            distancias_centros[f"{localidad} ({provincia})"] = distancias
        
        # Crear el prompt
        prompt = f"""Analiza los siguientes centros educativos de tipo {tipo_centro} en las provincias de {', '.join(provincias)} y ordénalos según su proximidad a las siguientes ciudades de referencia:

"""
        # Añadir información de las ciudades de referencia
        for ciudad in ciudades_referencia:
            radio_info = "sin límite de distancia" if ciudad['radio'] == 0 else f"dentro de {ciudad['radio']} km"
            prompt += f"- {ciudad['nombre']} - {radio_info}\n"
        
        prompt += "\nCentros ordenados por proximidad a cada ciudad de referencia:\n\n"
        
        # Crear una lista de todos los centros con su ciudad de referencia más cercana
        centros_ordenados = []
        centros_asignados = set()  # Para evitar duplicados
        
        # Si alguna ciudad tiene radio 0, todos los centros se asignan a su ciudad más cercana
        hay_radio_sin_limite = any(ref['radio'] == 0 for ref in ciudades_referencia)
        
        # Para cada centro, encontrar su ciudad de referencia más cercana
        for centro, distancias in distancias_centros.items():
            # Encontrar la ciudad de referencia más cercana
            ciudad_mas_cercana = min(ciudades_referencia, key=lambda x: distancias[x['nombre']])
            distancia = distancias[ciudad_mas_cercana['nombre']]
            
            # Si el radio es 0 o la distancia está dentro del radio
            if ciudad_mas_cercana['radio'] == 0 or distancia <= ciudad_mas_cercana['radio']:
                centros_ordenados.append({
                    'centro': centro,
                    'ciudad_ref': ciudad_mas_cercana['nombre'],
                    'distancia': distancia
                })
            elif not hay_radio_sin_limite:  # Solo añadir si ninguna ciudad tiene radio 0
                centros_ordenados.append({
                    'centro': centro,
                    'ciudad_ref': None,  # Fuera del radio de todas las ciudades
                    'distancia': min(distancias.values())
                })
        
        # Ordenar primero por ciudad de referencia y luego por distancia
        centros_ordenados.sort(key=lambda x: (
            x['ciudad_ref'] if x['ciudad_ref'] else 'ZZZ',  # 'ZZZ' para que los sin referencia vayan al final
            x['distancia']
        ))
        
        # Agrupar y mostrar los centros
        ciudad_actual = None
        for centro in centros_ordenados:
            if centro['ciudad_ref'] != ciudad_actual:
                ciudad_actual = centro['ciudad_ref']
                if ciudad_actual:
                    prompt += f"\n### Centros cercanos a {ciudad_actual}:\n"
                else:
                    prompt += "\n### Centros fuera del radio de todas las ciudades de referencia:\n"
            
            prompt += f"- {centro['centro']} - {centro['distancia']:.1f} km\n"
        
        return prompt
    
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
                        ref_loc['nombre'], ref_loc['Provincia'],
                        loc['Localidad'], loc['Provincia']
                    )
                    if distance <= ref_loc.get('radio', 50):
                        distances.append((ref_loc['nombre'], distance, ref_loc.get('radio', 50)))
                except Exception as e:
                    print(f"Error calculando distancia: {str(e)}")
                    continue
            
            if distances:
                # Encontrar la ciudad de referencia más cercana
                closest_ref = min(distances, key=lambda x: x[1])
                
                # Formatear la línea con la información de distancia y radio
                formatted_list.append(
                    f"{i+1}. {loc['Localidad']} ({loc['Provincia']}) - "
                    f"Cerca de {closest_ref[0]} ({closest_ref[1]:.1f} km, radio: {closest_ref[2]} km)"
                )
            else:
                # Si no está dentro del radio de ninguna ciudad de referencia
                formatted_list.append(
                    f"{i+1}. {loc['Localidad']} ({loc['Provincia']}) - "
                    f"Fuera del radio de todas las ciudades de referencia"
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
    
    def _format_ciudades_preferencia(self, ciudades: List[Dict]) -> str:
        """Formatea la lista de ciudades de preferencia para el prompt."""
        return "\n".join([
            f"{i+1}. {ciudad['nombre']} (radio: {ciudad.get('radio', 50)} km)"
            for i, ciudad in enumerate(ciudades)
        ])
    
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