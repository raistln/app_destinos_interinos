import os
import logging
from typing import List, Dict, Optional
import yaml
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from distance_calculator import DistanceCalculator
from dotenv import load_dotenv
from exceptions import LLMError, ConfiguracionError, ValidacionError

# Configurar logger
logger = logging.getLogger(__name__)

class LLMConnector:
    """
    Conector para interactuar con modelos de lenguaje (LLM).
    
    Esta clase maneja la comunicación con el modelo Mistral y procesa
    los datos de centros educativos y preferencias de ubicación.
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
            
        # Eliminar prefijo IES si existe
        if city_name.upper().startswith('IES '):
            city_name = city_name[4:]
        return city_name.strip()

    def generate_prompt(self, 
                       tipo_centro: str, 
                       provincias: List[str], 
                       ciudades_preferencia: List[Dict], 
                       datos_centros: List[Dict]) -> str:
        """
        Genera un prompt para el LLM con los datos procesados.
        
        Args:
            tipo_centro: Tipo de centro educativo
            provincias: Lista de provincias seleccionadas
            ciudades_preferencia: Lista de ciudades de preferencia con sus radios
            datos_centros: Lista de diccionarios con datos de los centros
            
        Returns:
            str: Prompt generado
        """
        logger.info("Generando prompt para LLM")
        
        try:
            # Normalizar nombres de ciudades de referencia
            ciudades_referencia = []
            for ciudad in ciudades_preferencia:
                ciudad_normalizada = self._normalize_city_name(ciudad['nombre'])
                # Usar la provincia de la ciudad si está especificada, sino usar la primera provincia seleccionada
                provincia = ciudad.get('provincia', provincias[0])
                ciudades_referencia.append({
                    'nombre': ciudad_normalizada,
                    'provincia': provincia,
                    'radio': ciudad.get('radio', 50)
                })
            
            # Crear diccionario de distancias para cada centro
            distancias_centros = {}
            for centro in datos_centros:
                localidad = self._normalize_city_name(centro['Localidad'])
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
        
        # Mantener un contador continuo para todos los centros
        contador = 1
        
        # Procesar cada ciudad de referencia en el orden original
        for ciudad in ciudades_referencia:
            nombre_ciudad = ciudad['nombre']
            if nombre_ciudad in centros_por_ciudad:
                prompt += f"\nCiudades cercanas a {nombre_ciudad}:\n\n"
                # Ordenar los centros de esta ciudad por distancia
                centros_ciudad = sorted(centros_por_ciudad[nombre_ciudad], key=lambda x: x['distancia'])
                for centro in centros_ciudad:
                    prompt += f"{contador}. {centro['centro']} - {centro['distancia']:.1f} km\n"
                    contador += 1
                prompt += "\n"  # Añadir línea en blanco después de cada grupo
        
        # Añadir información sobre ciudades sin centros
        ciudades_con_centros = set(centros_por_ciudad.keys())
        ciudades_sin_centros = [ciudad['nombre'] for ciudad in ciudades_referencia 
                               if ciudad['nombre'] not in ciudades_con_centros]
        
        if ciudades_sin_centros:
            prompt += "\nNo se encontraron centros dentro del radio especificado para:\n"
            for ciudad in ciudades_sin_centros:
                radio = next(c['radio'] for c in ciudades_referencia if c['nombre'] == ciudad)
                prompt += f"- {ciudad} (radio: {radio} km)\n"
        
        return prompt
    
    def _sort_centers(self, 
                     distancias_centros: Dict,
                     ciudades_referencia: List[Dict]) -> List[Dict]:
        """
        Ordena los centros según su proximidad a las ciudades de referencia.
        """
        # Lista para almacenar los centros ordenados
        centros_ordenados = []
        
        # Para cada centro, encontrar su ciudad de referencia más cercana dentro del radio
        for centro, distancias in distancias_centros.items():
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
        
        # Ordenar primero por ciudad de referencia (manteniendo el orden original)
        # y luego por distancia
        def sort_key(centro):
            # Obtener el índice de la ciudad de referencia en la lista original
            ref_index = next(i for i, c in enumerate(ciudades_referencia) 
                            if c['nombre'] == centro['ciudad_ref'])
            return (ref_index, centro['distancia'])
        
        return sorted(centros_ordenados, key=sort_key)

    def process_with_llm(self, prompt: str) -> str:
        """Procesa el prompt usando el LLM."""
        try:
            # Por ahora, simplemente devolvemos el prompt formateado
            return prompt
        except Exception as e:
            logger.error(f"Error procesando con LLM: {str(e)}")
            raise 