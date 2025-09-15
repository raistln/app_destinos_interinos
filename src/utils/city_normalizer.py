"""
Utilidades para normalizar nombres de ciudades y evitar duplicados en la base de datos.
"""

import re
import unicodedata
from typing import List, Dict


class CityNameNormalizer:
    """
    Clase para normalizar nombres de ciudades eliminando variaciones comunes
    que pueden causar duplicados en la base de datos.
    """
    
    # Prefijos comunes en español que se deben eliminar
    PREFIJOS_COMUNES = [
        'la ', 'el ', 'las ', 'los ',
        'de ', 'del ', 'de la ', 'de las ', 'de los ',
        'san ', 'santa ', 'santo ',
        'puerto ', 'villa ', 'ciudad '
    ]
    
    # Sufijos comunes que se pueden normalizar
    SUFIJOS_COMUNES = [
        ' de la frontera', ' de la sierra', ' del mar',
        ' de arriba', ' de abajo', ' alto', ' bajo'
    ]
    
    @staticmethod
    def normalize_city_name(city_name: str) -> str:
        """
        Normaliza un nombre de ciudad eliminando variaciones comunes.
        
        Args:
            city_name (str): Nombre original de la ciudad
            
        Returns:
            str: Nombre normalizado de la ciudad
            
        Examples:
            >>> CityNameNormalizer.normalize_city_name("La Zubia")
            'zubia'
            >>> CityNameNormalizer.normalize_city_name("EL PUERTO DE SANTA MARÍA")
            'puerto de santa maria'
            >>> CityNameNormalizer.normalize_city_name("San Fernando")
            'fernando'
        """
        if not city_name or not isinstance(city_name, str):
            return ""
        
        # Paso 1: Convertir a minúsculas
        normalized = city_name.lower().strip()
        
        # Paso 2: Eliminar acentos y caracteres especiales
        normalized = CityNameNormalizer._remove_accents(normalized)
        
        # Paso 3: Eliminar caracteres especiales y normalizar espacios
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Paso 4: Eliminar prefijos comunes
        normalized = CityNameNormalizer._remove_prefixes(normalized)
        
        # Paso 5: Eliminar sufijos comunes (opcional)
        normalized = CityNameNormalizer._remove_suffixes(normalized)
        
        # Paso 6: Limpiar espacios finales
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def _remove_accents(text: str) -> str:
        """
        Elimina acentos y caracteres diacríticos del texto.
        
        Args:
            text (str): Texto con posibles acentos
            
        Returns:
            str: Texto sin acentos
        """
        # Normalizar usando NFD (Canonical Decomposition)
        nfd = unicodedata.normalize('NFD', text)
        # Filtrar solo caracteres que no sean marcas diacríticas
        without_accents = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
        return without_accents
    
    @staticmethod
    def _remove_prefixes(text: str) -> str:
        """
        Elimina prefijos comunes del nombre de la ciudad.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            str: Texto sin prefijos comunes
        """
        for prefix in CityNameNormalizer.PREFIJOS_COMUNES:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break  # Solo eliminar el primer prefijo encontrado
        
        return text
    
    @staticmethod
    def _remove_suffixes(text: str) -> str:
        """
        Elimina sufijos comunes del nombre de la ciudad.
        
        Args:
            text (str): Texto normalizado
            
        Returns:
            str: Texto sin sufijos comunes
        """
        for suffix in CityNameNormalizer.SUFIJOS_COMUNES:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()
                break  # Solo eliminar el primer sufijo encontrado
        
        return text
    
    @staticmethod
    def get_city_variations(city_name: str) -> List[str]:
        """
        Genera posibles variaciones de un nombre de ciudad para búsquedas.
        
        Args:
            city_name (str): Nombre de la ciudad
            
        Returns:
            List[str]: Lista de posibles variaciones
        """
        if not city_name:
            return []
        
        variations = set()
        normalized = CityNameNormalizer.normalize_city_name(city_name)
        
        # Agregar la versión normalizada
        variations.add(normalized)
        
        # Agregar versiones con prefijos comunes
        for prefix in ['la ', 'el ', 'san ', 'santa ']:
            variations.add(f"{prefix}{normalized}")
        
        # Agregar la versión original normalizada (sin eliminar prefijos)
        original_normalized = CityNameNormalizer._remove_accents(city_name.lower().strip())
        original_normalized = re.sub(r'[^\w\s]', ' ', original_normalized)
        original_normalized = re.sub(r'\s+', ' ', original_normalized).strip()
        variations.add(original_normalized)
        
        return list(variations)
    
    @staticmethod
    def find_similar_cities(city_name: str, city_list: List[str], threshold: float = 0.8) -> List[Dict[str, str]]:
        """
        Encuentra ciudades similares en una lista basándose en la normalización.
        
        Args:
            city_name (str): Nombre de ciudad a buscar
            city_list (List[str]): Lista de ciudades existentes
            threshold (float): Umbral de similitud (no usado en esta implementación básica)
            
        Returns:
            List[Dict[str, str]]: Lista de ciudades similares con sus versiones normalizadas
        """
        normalized_target = CityNameNormalizer.normalize_city_name(city_name)
        similar_cities = []
        
        for city in city_list:
            normalized_city = CityNameNormalizer.normalize_city_name(city)
            if normalized_city == normalized_target:
                similar_cities.append({
                    'original': city,
                    'normalized': normalized_city,
                    'match_type': 'exact'
                })
        
        return similar_cities


# Función de conveniencia para uso directo
def normalize_city_name(city_name: str) -> str:
    """
    Función de conveniencia para normalizar nombres de ciudades.
    
    Args:
        city_name (str): Nombre original de la ciudad
        
    Returns:
        str: Nombre normalizado de la ciudad
    """
    return CityNameNormalizer.normalize_city_name(city_name)


# Ejemplos de uso y tests
if __name__ == "__main__":
    # Ejemplos de prueba
    test_cities = [
        "La Zubia",
        "zubia",
        "ZUBIA",
        "El Puerto de Santa María",
        "Puerto de Santa María", 
        "puerto de santa maria",
        "San Fernando",
        "Santa Fe",
        "Las Palmas",
        "Los Barrios",
        "Vélez-Málaga",
        "Jerez de la Frontera"
    ]
    
    print("=== Pruebas de Normalización ===")
    for city in test_cities:
        normalized = normalize_city_name(city)
        print(f"'{city}' -> '{normalized}'")
    
    print("\n=== Pruebas de Variaciones ===")
    test_city = "Zubia"
    variations = CityNameNormalizer.get_city_variations(test_city)
    print(f"Variaciones de '{test_city}': {variations}")
