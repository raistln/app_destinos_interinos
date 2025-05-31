import os
import logging
from typing import List, Dict, Optional, Union
import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from distance_calculator import DistanceCalculator
from dotenv import load_dotenv
from exceptions import LLMError, ConfiguracionError, ValidacionError, APIError

# Configurar logger
logger = logging.getLogger(__name__)

class LLMConnector:
    """
    Conector para interactuar con modelos de lenguaje (LLM).
    
    Esta clase maneja la comunicación con el modelo Mistral y procesa
    los datos de centros educativos y preferencias de ubicación.
    
    Attributes:
        model (str): Nombre del modelo a utilizar
        api_url (str): URL de la API del modelo
        headers (dict): Headers para las peticiones HTTP
        distance_calculator (DistanceCalculator): Instancia para cálculos de distancia
        reference_locations (List[Dict]): Lista de ubicaciones de referencia
    """
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Inicializa el conector LLM.
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Raises:
            ConfiguracionError: Si hay error al cargar la configuración
            ValidacionError: Si faltan variables de entorno requeridas
        """
        logger.info("Inicializando LLMConnector")
        try:
            # Cargar variables de entorno
            load_dotenv()
            api_key = os.getenv('MISTRAL_API_KEY')
            if not api_key:
                raise ValidacionError("MISTRAL_API_KEY no encontrada en variables de entorno")
            
            # Cargar configuración
            try:
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                raise ConfiguracionError(f"Error al cargar configuración: {str(e)}")
            
            # Configurar el modelo
            self.model = self.config['llm']['models']['mistral']['name']
            self.api_url = self.config['llm']['models']['mistral']['api_url']
            self.headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Configurar sesión HTTP con retry
            self.session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
            
            # Inicializar el calculador de distancias
            self.distance_calculator = DistanceCalculator()
            self.reference_locations = []
            
            logger.info("LLMConnector inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error en inicialización de LLMConnector: {str(e)}")
            raise
    
    def _normalize_city_name(self, city_name: str) -> str:
        """
        Normaliza el nombre de una ciudad para que tenga el formato correcto.
        
        Args:
            city_name: Nombre de la ciudad a normalizar
            
        Returns:
            Nombre normalizado
            
        Raises:
            ValidacionError: Si el nombre de la ciudad está vacío
        """
        if not city_name or not city_name.strip():
            raise ValidacionError("El nombre de la ciudad no puede estar vacío")
            
        # Dividir por espacios y guiones
        words = city_name.replace('-', ' ').split()
        # Capitalizar cada palabra
        normalized_words = [word.capitalize() for word in words]
        # Unir las palabras
        return ' '.join(normalized_words)

    def generate_prompt(self, 
                       tipo_centro: str, 
                       provincias: List[str], 
                       ciudades_preferencia: List[Dict], 
                       datos_centros: List[Dict]) -> str:
        """
        Genera un prompt para el LLM con los datos de los centros y las preferencias.
        
        Args:
            tipo_centro: Tipo de centro (IES o CEIP)
            provincias: Lista de provincias seleccionadas
            ciudades_preferencia: Lista de diccionarios con ciudades de preferencia y sus radios
            datos_centros: Lista de diccionarios con datos de los centros
            
        Returns:
            str: Prompt generado para el LLM
            
        Raises:
            ValidacionError: Si los datos de entrada no son válidos
        """
        logger.info("Generando prompt para LLM")
        
        # Validar entradas
        if not tipo_centro or ("IES" not in tipo_centro and "CEIP" not in tipo_centro):
            raise ValidacionError("Tipo de centro debe ser 'IES' o 'CEIP'")
        if not provincias:
            raise ValidacionError("Debe especificar al menos una provincia")
        if not ciudades_preferencia:
            raise ValidacionError("Debe especificar al menos una ciudad de preferencia")
        if not datos_centros:
            raise ValidacionError("No hay datos de centros disponibles")
            
        try:
            # Normalizar nombres de ciudades de referencia
            ciudades_referencia = []
            for ciudad in ciudades_preferencia:
                ciudad_normalizada = self._normalize_city_name(ciudad['nombre'])
                ciudades_referencia.append({
                    'nombre': ciudad['nombre'],
                    'provincia': provincias[0],
                    'radio': ciudad.get('radio', 50)
                })
                logger.debug(f"Ciudad de referencia normalizada: {ciudad_normalizada}")
            
            # Crear diccionario de distancias para cada centro
            distancias_centros = {}
            for centro in datos_centros:
                localidad = centro['Localidad']
                provincia = centro['Provincia']
                distancias = {}
                
                # Calcular distancia a cada ciudad de referencia
                for ref in ciudades_referencia:
                    try:
                        distancia = self.distance_calculator.get_distance(
                            location1=localidad,
                            province1=provincia,
                            location2=ref['nombre'],
                            province2=ref['provincia']
                        )
                        distancias[ref['nombre']] = distancia
                    except Exception as e:
                        logger.warning(f"Error calculando distancia para {localidad}: {str(e)}")
                        distancias[ref['nombre']] = float('inf')
                
                distancias_centros[f"{localidad} ({provincia})"] = distancias
            
            # Generar el prompt
            prompt = self._build_prompt(
                tipo_centro=tipo_centro,
                provincias=provincias,
                ciudades_referencia=ciudades_referencia,
                distancias_centros=distancias_centros
            )
            
            logger.info("Prompt generado exitosamente")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generando prompt: {str(e)}")
            raise
    
    def _build_prompt(self, 
                     tipo_centro: str,
                     provincias: List[str],
                     ciudades_referencia: List[Dict],
                     distancias_centros: Dict) -> str:
        """
        Construye el prompt final con todos los datos procesados.
        
        Args:
            tipo_centro: Tipo de centro
            provincias: Lista de provincias
            ciudades_referencia: Lista de ciudades de referencia
            distancias_centros: Diccionario con distancias calculadas
            
        Returns:
            str: Prompt completo
        """
        # Ordenar los centros
        centros_ordenados = self._sort_centers(distancias_centros, ciudades_referencia)
        
        # Construir el prompt
        prompt = f"# Centros {tipo_centro} ordenados por proximidad\n\n"
        
        # Agrupar los centros por ciudad de referencia
        centros_por_ciudad = {}
        for centro in centros_ordenados:
            ciudad = centro['ciudad_ref']
            if ciudad not in centros_por_ciudad:
                centros_por_ciudad[ciudad] = []
            centros_por_ciudad[ciudad].append(centro)
        
        contador = 1
        for ciudad in ciudades_referencia:
            nombre_ciudad = ciudad['nombre']
            if nombre_ciudad in centros_por_ciudad:
                prompt += f"Cercanos a {nombre_ciudad}:\n"
                for centro in centros_por_ciudad[nombre_ciudad]:
                    prompt += f"{contador}. {centro['centro']} - {centro['distancia']:.1f} km\n"
                    contador += 1
                prompt += "\n"
        
        # Añadir información sobre ciudades sin centros
        ciudades_con_centros = set(centros_por_ciudad.keys())
        ciudades_sin_centros = [ciudad['nombre'] for ciudad in ciudades_referencia 
                               if ciudad['nombre'] not in ciudades_con_centros]
        
        if ciudades_sin_centros:
            prompt += "No se encontraron centros dentro del radio especificado para:\n"
            for ciudad in ciudades_sin_centros:
                radio = next(c['radio'] for c in ciudades_referencia if c['nombre'] == ciudad)
                prompt += f"- {ciudad} (radio: {radio} km)\n"
        
        return prompt
    
    def _sort_centers(self, 
                     distancias_centros: Dict,
                     ciudades_referencia: List[Dict]) -> List[Dict]:
        """
        Ordena los centros según su proximidad a las ciudades de referencia,
        implementando una lógica de clustering basada en distancias.
        
        Args:
            distancias_centros: Diccionario con distancias calculadas
            ciudades_referencia: Lista de ciudades de referencia
            
        Returns:
            List[Dict]: Lista ordenada de centros
        """
        # Lista para almacenar los centros ordenados
        centros_ordenados = []
        # Conjunto para evitar duplicados
        centros_procesados = set()
        
        # Para cada centro, encontrar su ciudad de referencia más cercana dentro del radio
        for centro, distancias in distancias_centros.items():
            if centro in centros_procesados:
                continue
            
            # Encontrar la ciudad de referencia más cercana dentro de su radio
            ciudad_mas_cercana = None
            distancia_minima = float('inf')
            
            for ciudad in ciudades_referencia:
                distancia = distancias[ciudad['nombre']]
                # Si está dentro del radio y es la más cercana hasta ahora
                if distancia <= ciudad['radio'] and distancia < distancia_minima:
                    ciudad_mas_cercana = ciudad
                    distancia_minima = distancia
            
            # Si se encontró una ciudad de referencia válida
            if ciudad_mas_cercana:
                centros_ordenados.append({
                    'centro': centro,
                    'ciudad_ref': ciudad_mas_cercana['nombre'],
                    'distancia': distancia_minima
                })
                centros_procesados.add(centro)
        
        # Ordenar primero por ciudad de referencia (manteniendo el orden original)
        # y luego por distancia
        def sort_key(centro):
            # Obtener el índice de la ciudad de referencia en la lista original
            ref_index = next(i for i, c in enumerate(ciudades_referencia) 
                            if c['nombre'] == centro['ciudad_ref'])
            return (ref_index, centro['distancia'])
        
        return sorted(centros_ordenados, key=sort_key)
    
    def process_with_llm(self, prompt: str) -> str:
        """
        Procesa el prompt con el LLM seleccionado.
        
        Args:
            prompt: Prompt a procesar
            
        Returns:
            str: Respuesta del LLM
            
        Raises:
            LLMError: Si hay error en el procesamiento
        """
        logger.info("Procesando prompt con LLM")
        try:
            return self._process_with_mistral(prompt)
        except Exception as e:
            logger.error(f"Error procesando prompt con LLM: {str(e)}")
            raise LLMError(f"Error en procesamiento LLM: {str(e)}")
    
    def _process_with_mistral(self, prompt: str) -> str:
        """
        Procesa el prompt usando la API de Mistral.
        
        Args:
            prompt: Prompt a procesar
            
        Returns:
            str: Respuesta de la API
            
        Raises:
            APIError: Si hay error en la comunicación con la API
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Eres un asistente especializado en ordenar localidades según proximidad geográfica."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config['llm']['temperature'],
                "max_tokens": self.config['llm']['max_tokens']
            }
            
            response = self.session.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en API de Mistral: {str(e)}")
            raise APIError(f"Error en comunicación con API: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error procesando respuesta de API: {str(e)}")
            raise APIError(f"Error en formato de respuesta: {str(e)}")
    
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