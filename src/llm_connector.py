import os
from typing import List, Dict
import yaml
from dotenv import load_dotenv
import requests
import openai

class LLMConnector:
    def __init__(self, config_path: str = "config/settings.yaml"):
        load_dotenv()
        self.config = self._load_config(config_path)
        self.provider = self.config['llm']['provider']
        self._setup_provider()
    
    def _load_config(self, config_path: str) -> Dict:
        """Carga la configuración desde el archivo YAML."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_provider(self):
        """Configura el proveedor de LLM seleccionado."""
        provider_config = self.config['llm']['models'][self.provider]
        
        if self.provider == 'mistral':
            self.api_key = os.getenv("MISTRAL_API_KEY")
            if not self.api_key:
                raise ValueError("MISTRAL_API_KEY no encontrada en las variables de entorno")
            self.api_url = provider_config['api_url']
            self.model = provider_config['name']
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == 'openai':
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY no encontrada en las variables de entorno")
            openai.api_key = self.api_key
            self.model = provider_config['name']
        else:
            raise ValueError(f"Proveedor no soportado: {self.provider}")
    
    def generate_prompt(self, 
                       tipo_centro: str,
                       provincias: List[str],
                       ciudades_preferencia: List[str],
                       datos_centros: List[Dict]) -> str:
        """
        Genera el prompt para el LLM.
        
        Args:
            tipo_centro: Tipo de centro educativo
            provincias: Lista de provincias seleccionadas
            ciudades_preferencia: Lista de ciudades en orden de preferencia
            datos_centros: Lista de diccionarios con datos de los centros
            
        Returns:
            str con el prompt generado
        """
        prompt = f"""Estoy procesando datos de centros educativos {tipo_centro} públicos en las provincias de {', '.join(provincias)} de Andalucía.

Tengo la siguiente información sobre cada centro:
{self._format_centros_data(datos_centros)}

Necesito una lista numerada y única de todas las localidades con {tipo_centro} públicos, ordenadas según su proximidad geográfica a mis localidades de preferencia, que en orden descendente de prioridad son:

{self._format_ciudades_preferencia(ciudades_preferencia)}

El ordenamiento debe funcionar así:
- Inicialmente, priorizar localidades cercanas a {ciudades_preferencia[0]}.
- Cuando una localidad es significativamente más cercana a una ciudad de menor prioridad que a {ciudades_preferencia[0]}, ordenarla según esa otra ciudad.
- Cada localidad debe aparecer solo una vez en la posición más favorable según este sistema.
- Incluir también las propias ciudades de preferencia en la lista resultante, en la posición que les corresponda.

Genera una lista numerada con el formato: "Número. Localidad (Provincia)"

Adicionalmente, si hay alguna localidad pequeña cercana a mis preferencias que NO tenga {tipo_centro} públicos, menciónala brevemente al final."""
        
        return prompt
    
    def _format_centros_data(self, datos_centros: List[Dict]) -> str:
        """Formatea los datos de los centros para el prompt."""
        if not datos_centros:
            return "No hay datos de centros disponibles."
        
        ejemplo = datos_centros[0]
        return f"""
Ejemplo de datos de centro:
- Código: {ejemplo.get('codigo', 'N/A')}
- Nombre: {ejemplo.get('nombre', 'N/A')}
- Localidad: {ejemplo.get('localidad', 'N/A')}
- Municipio: {ejemplo.get('municipio', 'N/A')}
- Provincia: {ejemplo.get('provincia', 'N/A')}
- Dirección: {ejemplo.get('direccion', 'N/A')}
- Código Postal: {ejemplo.get('codigo_postal', 'N/A')}
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
        try:
            if self.provider == 'mistral':
                return self._process_with_mistral(prompt)
            elif self.provider == 'openai':
                return self._process_with_openai(prompt)
            else:
                raise ValueError(f"Proveedor no soportado: {self.provider}")
        except Exception as e:
            return f"Error al procesar con el LLM: {str(e)}"
    
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