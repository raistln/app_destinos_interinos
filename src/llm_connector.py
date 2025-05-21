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
        prompt = f"""# Generación de Lista Ordenada de Localidades

## Tarea Principal
Genera UNA LISTA NUMERADA de todas las localidades que tienen {tipo_centro} públicos en las provincias de {', '.join(provincias)} de Andalucía, ordenadas por proximidad geográfica a mis localidades de referencia.

## Datos Disponibles
Información de los centros:
{self._format_centros_data(datos_centros)}

## Puntos de Referencia (en orden de prioridad)
{self._format_ciudades_preferencia(ciudades_preferencia)}

## Instrucciones de Ordenamiento
1. Comienza con {ciudades_preferencia[0]} y lista TODAS las localidades por proximidad a ella
2. Cuando una localidad esté más lejos de {ciudades_preferencia[0]} que de {ciudades_preferencia[1]}, cambia a ordenar por proximidad a {ciudades_preferencia[1]}
3. Repite el proceso para cada punto de referencia
4. Cada localidad debe aparecer SOLO UNA VEZ en la lista

## Ejemplo de Ordenamiento (Zona de Granada)
Si {ciudades_preferencia[0]} es La Zubia, el orden debería ser aproximadamente así:
1. La Zubia (Granada)
2. Cájar (Granada) - pueblo contiguo
3. Monachil (Granada) - pueblo contiguo
4. Huétor Vega (Granada) - pueblo contiguo
5. Granada (Granada) - ciudad capital
6. Armilla (Granada) - área metropolitana
7. Maracena (Granada) - área metropolitana
8. Albolote (Granada) - área metropolitana
9. Churriana de la Vega (Granada) - área metropolitana
10. Ogíjares (Granada) - área metropolitana
...y así sucesivamente con el resto de localidades

## Formato de Respuesta Requerido
RESPONDE ÚNICAMENTE CON UNA LISTA NUMERADA en este formato:
1. [Localidad] ([Provincia])
2. [Localidad] ([Provincia])
...

IMPORTANTE:
- NO incluyas explicaciones ni comentarios
- NO incluyas el proceso de ordenamiento en la respuesta
- SOLO genera la lista numerada de localidades
- Al final de la lista, puedes añadir una breve nota sobre localidades cercanas sin {tipo_centro} públicos
- Asegúrate de que las localidades del área metropolitana aparezcan PRIMERO si están más cerca del punto de referencia

Asume que tienes acceso a coordenadas geográficas para calcular las distancias."""
        
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