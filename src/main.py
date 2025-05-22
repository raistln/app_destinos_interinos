import streamlit as st
import pandas as pd
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os
from processor import DataProcessor
from llm_connector import LLMConnector

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Selección de Destinos para Interinos",
    page_icon="🏫",
    layout="wide"
)

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
    ciudades = st.text_area(
        "Introduce tus ciudades de preferencia (una por línea, en orden de prioridad):",
        height=150
    )
    
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
                    "ciudades": ciudades.split("\n")
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
                    st.session_state.ciudades = "\n".join(config.get("ciudades", []))
                    st.success("Configuración cargada")
                else:
                    st.error("Configuración no encontrada")
            else:
                st.warning("Introduce un nombre para cargar la configuración")

# Área principal
if not provincias_seleccionadas:
    st.warning("Por favor, selecciona al menos una provincia.")
elif not ciudades.strip():
    st.warning("Por favor, introduce al menos una ciudad de preferencia.")
else:
    if st.button("Calcular Destinos"):
        with st.spinner("Procesando..."):
            # Cargar datos
            df = data_processor.load_data(provincias_seleccionadas, tipo_centro)
            
            if df.empty:
                st.error("No se encontraron datos para las provincias seleccionadas.")
            else:
                # Mostrar información de depuración
                st.write(f"Provincias seleccionadas: {provincias_seleccionadas}")
                st.write(f"Número total de registros: {len(df)}")
                st.write(f"Registros por provincia: {df['Provincia'].value_counts().to_dict()}")
                
                # Procesar preferencias
                ciudades_lista = [c.strip() for c in ciudades.split("\n") if c.strip()]
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