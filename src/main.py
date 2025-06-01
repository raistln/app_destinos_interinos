import streamlit as st
import pandas as pd
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os
from processor import DataProcessor
from llm_connector import LLMConnector
import shutil

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Selección de Destinos para Interinos",
    page_icon="🏫",
    layout="wide"
)

# Función para cargar o crear settings
def load_or_create_settings(api_key=None):
    settings_path = Path("config/settings.yaml")
    example_path = Path("config/settings.example.yaml")
    
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f) or {}
            if api_key:
                if 'api' not in settings:
                    settings['api'] = {}
                settings['api']['mistral_api_key'] = api_key
                with open(settings_path, 'w', encoding='utf-8') as f:
                    yaml.dump(settings, f, allow_unicode=True)
    else:
        # Si no existe settings.yaml, crear uno nuevo desde el ejemplo
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f) or {}
                if api_key:
                    if 'api' not in settings:
                        settings['api'] = {}
                    settings['api']['mistral_api_key'] = api_key
                with open(settings_path, 'w', encoding='utf-8') as f:
                    yaml.dump(settings, f, allow_unicode=True)
        else:
            st.error("No se encontró el archivo settings.example.yaml")
            return None
    
    return settings

# Inicializar procesadores
data_processor = DataProcessor()
llm_connector = LLMConnector()

# Título de la aplicación
st.title("Selección de Destinos para Interinos de Educación en Andalucía")

# Provincias de Andalucía
PROVINCIAS = [
    "Almería", "Cádiz", "Córdoba", "Granada",
    "Huelva", "Jaén", "Málaga", "Sevilla"
]

# Sidebar para configuración
with st.sidebar:
    st.header("Configuración")
    
    # Campo para la API key de Mistral
    st.subheader("API Key de Mistral")
    mistral_api_key = st.text_input("API Key:", type="password", value="")
    
    # Si el usuario no introduce la clave, intentar cargarla de .env
    if not mistral_api_key:
        mistral_api_key = os.getenv("MISTRAL_API_KEY", "")
    
    # Si sigue sin haber clave, mostrar error y detener la app
    if not mistral_api_key:
        st.error("Por favor, introduce tu API key de Mistral para continuar.")
        st.stop()
    
    # Cargar o crear settings
    settings = load_or_create_settings(mistral_api_key if mistral_api_key else None)
    
    if settings:
        # Usar la API key del settings si no se proporcionó una nueva
        if not mistral_api_key:
            mistral_api_key = settings.get('api', {}).get('mistral_api_key', '')
    
    # Modo test
    modo_test = st.checkbox("Modo test (10 centros aleatorios)", help="Selecciona 10 centros al azar para pruebas")
    
    # Selección de provincias
    st.subheader("Provincias")
    provincias_seleccionadas = []
    for provincia in PROVINCIAS:
        if st.checkbox(provincia):
            provincias_seleccionadas.append(provincia)
    
    # Tipo de centro
    st.subheader("Tipo de Centro")
    tipo_centro = st.radio(
        "Selecciona el tipo de centro:",
        ["Institutos (IES)", "Colegios (CEIP)"]
    )
    
    # Ciudades de preferencia
    st.subheader("Ciudades de Preferencia")
    
    # Inicializar la lista de ciudades en session_state si no existe
    if 'ciudades_preferencia' not in st.session_state:
        st.session_state.ciudades_preferencia = []
    
    # Campo para añadir nueva ciudad
    col1, col2 = st.columns([3, 1])
    with col1:
        nueva_ciudad = st.text_input("Nueva ciudad:")
    with col2:
        if st.button("➕", help="Añadir ciudad"):
            if nueva_ciudad.strip():
                st.session_state.ciudades_preferencia.append({
                    'nombre': nueva_ciudad.strip(),
                    'radio': 50  # Radio por defecto en km
                })
                st.rerun()
    
    # Mostrar lista de ciudades con sus radios
    for i, ciudad in enumerate(st.session_state.ciudades_preferencia):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"{i+1}. {ciudad['nombre']}")
        with col2:
            ciudad['radio'] = st.number_input(
                "Radio (km)",
                min_value=0,
                max_value=200,
                value=ciudad['radio'],
                key=f"radio_{i}",
                help="0 = Sin límite de distancia"
            )
        with col3:
            if st.button("❌", key=f"delete_{i}"):
                st.session_state.ciudades_preferencia.pop(i)
                st.rerun()
    
    # Guardar/Cargar configuración
    st.subheader("Guardar/Cargar Configuración")
    config_name = st.text_input("Nombre de la configuración:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Guardar"):
            if config_name:
                config = {
                    "provincias": provincias_seleccionadas,
                    "tipo_centro": tipo_centro,
                    "ciudades": st.session_state.ciudades_preferencia
                }
                if data_processor.save_configuration(config, config_name):
                    st.success("Configuración guardada")
                else:
                    st.error("Error al guardar la configuración")
            else:
                st.warning("Introduce un nombre para la configuración")
    
    with col2:
        if st.button("Cargar"):
            if config_name:
                config = data_processor.load_configuration(config_name)
                if config:
                    st.session_state.provincias = config.get("provincias", [])
                    st.session_state.tipo_centro = config.get("tipo_centro", "")
                    st.session_state.ciudades_preferencia = config.get("ciudades", [])
                    st.success("Configuración cargada")
                else:
                    st.error("Configuración no encontrada")
            else:
                st.warning("Introduce un nombre para cargar la configuración")

# Área principal
if not mistral_api_key and not settings:
    st.warning("Por favor, introduce tu API key de Mistral o configúrala en el archivo settings.yaml")
elif not provincias_seleccionadas:
    st.warning("Por favor, selecciona al menos una provincia.")
elif not st.session_state.ciudades_preferencia:
    st.warning("Por favor, añade al menos una ciudad de preferencia.")
else:
    if st.button("Calcular Destinos"):
        with st.spinner("Procesando..."):
            # Configurar la API key
            os.environ["MISTRAL_API_KEY"] = mistral_api_key
            
            # Cargar datos
            df = data_processor.load_data(provincias_seleccionadas, tipo_centro)
            
            if df.empty:
                st.error("No se encontraron datos para las provincias seleccionadas.")
            else:
                # Si está en modo test, seleccionar 10 centros al azar
                if modo_test:
                    df = df.sample(n=min(10, len(df)))
                    st.info("Modo test activado: usando 10 centros aleatorios")
                
                # Mostrar información de depuración
                st.write(f"Provincias seleccionadas: {provincias_seleccionadas}")
                st.write(f"Número total de registros: {len(df)}")
                st.write(f"Registros por provincia: {df['Provincia'].value_counts().to_dict()}")
                
                # Procesar preferencias
                ciudades_lista = st.session_state.ciudades_preferencia
                datos_centros = df.to_dict("records")
                
                # Generar y procesar prompt
                prompt = llm_connector.generate_prompt(
                    tipo_centro,
                    provincias_seleccionadas,
                    ciudades_lista,
                    datos_centros
                )
                
                resultado = llm_connector.process_with_llm(prompt)
                
                # Mostrar resultados
                st.subheader("Resultados")
                st.markdown(resultado)
                
                # Opción para exportar
                if st.button("Exportar Resultados"):
                    st.download_button(
                        label="Descargar como TXT",
                        data=resultado,
                        file_name="destinos_ordenados.txt",
                        mime="text/plain"
                    )

# Footer
st.markdown("---")
st.markdown("Desarrollado para interinos de educación en Andalucía") 