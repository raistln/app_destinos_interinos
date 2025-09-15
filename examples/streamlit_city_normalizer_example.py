"""
Ejemplo de integración de la normalización de ciudades con Streamlit.
Este ejemplo muestra cómo usar st.text_input con normalización en tiempo real.
"""

import streamlit as st
import sys
import os

# Añadir el directorio src al path para importar los módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.city_normalizer import CityNameNormalizer, normalize_city_name


def main():
    """Aplicación de ejemplo para demostrar la normalización de ciudades."""
    
    st.title("🏙️ Normalizador de Nombres de Ciudades")
    st.markdown("Esta aplicación demuestra cómo normalizar nombres de ciudades para evitar duplicados en la base de datos.")
    
    # Sección 1: Normalización básica
    st.header("1. Normalización Básica")
    
    # Input del usuario
    user_input = st.text_input(
        "Introduce el nombre de una ciudad:",
        placeholder="Ej: La Zubia, El Puerto de Santa María, san fernando...",
        help="Escribe el nombre de una ciudad con cualquier formato"
    )
    
    if user_input:
        # Normalizar el nombre
        normalized_name = normalize_city_name(user_input)
        
        # Mostrar resultados
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Entrada original:**\n`{user_input}`")
        
        with col2:
            st.success(f"**Nombre normalizado:**\n`{normalized_name}`")
        
        # Mostrar el proceso paso a paso
        with st.expander("Ver proceso de normalización paso a paso"):
            steps = get_normalization_steps(user_input)
            for i, (step_name, step_result) in enumerate(steps, 1):
                st.write(f"**{i}. {step_name}:** `{step_result}`")
    
    # Sección 2: Ejemplo de integración con base de datos
    st.header("2. Integración con Base de Datos")
    st.markdown("Ejemplo de cómo usar la normalización antes de guardar en la base de datos:")
    
    # Simulación de ciudades existentes en la base de datos
    if 'cities_db' not in st.session_state:
        st.session_state.cities_db = []
    
    # Input para añadir ciudad
    new_city = st.text_input(
        "Añadir nueva ciudad a la base de datos:",
        key="new_city_input",
        placeholder="Ej: Las Palmas, el puerto..."
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("➕ Añadir Ciudad"):
            if new_city:
                normalized = normalize_city_name(new_city)
                
                # Verificar si ya existe
                existing_normalized = [normalize_city_name(city) for city in st.session_state.cities_db]
                
                if normalized in existing_normalized:
                    st.warning(f"⚠️ La ciudad '{normalized}' ya existe en la base de datos!")
                else:
                    st.session_state.cities_db.append(new_city)
                    st.success(f"✅ Ciudad añadida: '{normalized}'")
                    st.rerun()
    
    with col2:
        if st.button("🗑️ Limpiar Lista"):
            st.session_state.cities_db = []
            st.rerun()
    
    # Mostrar ciudades en la base de datos
    if st.session_state.cities_db:
        st.subheader("Ciudades en la Base de Datos:")
        
        # Crear tabla con originales y normalizadas
        data = []
        for city in st.session_state.cities_db:
            data.append({
                "Original": city,
                "Normalizada": normalize_city_name(city)
            })
        
        st.dataframe(data, use_container_width=True)
    
    # Sección 3: Búsqueda con normalización
    st.header("3. Búsqueda con Normalización")
    
    search_term = st.text_input(
        "Buscar ciudad:",
        placeholder="Busca una ciudad existente...",
        key="search_input"
    )
    
    if search_term and st.session_state.cities_db:
        search_normalized = normalize_city_name(search_term)
        
        # Buscar coincidencias
        matches = []
        for city in st.session_state.cities_db:
            if normalize_city_name(city) == search_normalized:
                matches.append(city)
        
        if matches:
            st.success(f"🎯 Encontradas {len(matches)} coincidencia(s):")
            for match in matches:
                st.write(f"- {match}")
        else:
            st.info("🔍 No se encontraron coincidencias")
    
    # Sección 4: Ejemplos de prueba
    st.header("4. Ejemplos de Prueba")
    
    if st.button("🧪 Ejecutar Pruebas de Ejemplo"):
        test_examples()


def get_normalization_steps(city_name: str) -> list:
    """
    Obtiene los pasos de normalización para mostrar el proceso.
    
    Args:
        city_name (str): Nombre original de la ciudad
        
    Returns:
        list: Lista de tuplas (nombre_paso, resultado)
    """
    steps = []
    
    # Paso 1: Minúsculas y trim
    step1 = city_name.lower().strip()
    steps.append(("Convertir a minúsculas", step1))
    
    # Paso 2: Eliminar acentos
    step2 = CityNameNormalizer._remove_accents(step1)
    steps.append(("Eliminar acentos", step2))
    
    # Paso 3: Normalizar espacios y caracteres especiales
    import re
    step3 = re.sub(r'[^\w\s]', ' ', step2)
    step3 = re.sub(r'\s+', ' ', step3).strip()
    steps.append(("Limpiar caracteres especiales", step3))
    
    # Paso 4: Eliminar prefijos
    step4 = CityNameNormalizer._remove_prefixes(step3)
    steps.append(("Eliminar prefijos comunes", step4))
    
    # Paso 5: Eliminar sufijos
    step5 = CityNameNormalizer._remove_suffixes(step4)
    steps.append(("Eliminar sufijos comunes", step5))
    
    return steps


def test_examples():
    """Ejecuta ejemplos de prueba y muestra los resultados."""
    
    test_cases = [
        "La Zubia",
        "zubia", 
        "ZUBIA",
        "El Puerto de Santa María",
        "Puerto de Santa María",
        "San Fernando",
        "Santa Fe", 
        "Las Palmas",
        "Los Barrios",
        "Vélez-Málaga",
        "Jerez de la Frontera"
    ]
    
    st.subheader("Resultados de las Pruebas:")
    
    # Crear tabla con resultados
    results = []
    for city in test_cases:
        normalized = normalize_city_name(city)
        results.append({
            "Entrada": city,
            "Normalizada": normalized,
            "Longitud Original": len(city),
            "Longitud Normalizada": len(normalized)
        })
    
    st.dataframe(results, use_container_width=True)
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unique_normalized = len(set(r["Normalizada"] for r in results))
        st.metric("Ciudades Únicas (Normalizadas)", unique_normalized)
    
    with col2:
        total_original = len(results)
        st.metric("Total de Entradas", total_original)
    
    with col3:
        duplicates_avoided = total_original - unique_normalized
        st.metric("Duplicados Evitados", duplicates_avoided)


# Función auxiliar para integración directa en tu app
def streamlit_city_input_with_normalization(
    label: str,
    key: str = None,
    placeholder: str = None,
    help: str = None,
    show_normalized: bool = True
) -> tuple:
    """
    Crea un input de ciudad con normalización automática.
    
    Args:
        label (str): Etiqueta del input
        key (str): Clave única para el widget
        placeholder (str): Texto de placeholder
        help (str): Texto de ayuda
        show_normalized (bool): Si mostrar el resultado normalizado
        
    Returns:
        tuple: (input_original, input_normalizado)
    """
    # Input del usuario
    user_input = st.text_input(
        label=label,
        key=key,
        placeholder=placeholder,
        help=help
    )
    
    # Normalizar si hay input
    normalized = ""
    if user_input:
        normalized = normalize_city_name(user_input)
        
        # Mostrar resultado normalizado si se solicita
        if show_normalized and normalized != user_input.lower().strip():
            st.caption(f"📍 Nombre normalizado: **{normalized}**")
    
    return user_input, normalized


if __name__ == "__main__":
    # Configurar la página
    st.set_page_config(
        page_title="Normalizador de Ciudades",
        page_icon="🏙️",
        layout="wide"
    )
    
    main()
