import streamlit as st
import pandas as pd
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os
from processor import DataProcessor
from llm_connector import LLMConnector
from styles import apply_custom_styles

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Selección de Destinos Educativos - Andalucía",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos personalizados
apply_custom_styles()

# Constantes
PROVINCIAS = [
    "Almería", "Cádiz", "Córdoba", "Granada",
    "Huelva", "Jaén", "Málaga", "Sevilla"
]

def ejecutar_proceso(df, tipo_centro, provincias_seleccionadas, ciudades_lista):
    """Función que procesa los datos y genera el resultado."""
    try:
        datos_centros = df.to_dict("records")
        llm_connector = LLMConnector()
        prompt = llm_connector.generate_prompt(
            tipo_centro,
            provincias_seleccionadas,
            ciudades_lista,
            datos_centros
        )
        return llm_connector.process_with_llm(prompt)
    except Exception as e:
        return f"Error en el proceso: {str(e)}"

def load_or_create_settings(api_key=None):
    """Carga o crea el archivo de configuración."""
    settings_path = Path("config/settings.yaml")
    example_path = Path("config/settings.example.yaml")
    
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f) or {}
    else:
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f) or {}
        else:
            st.error("No se encontró el archivo settings.example.yaml")
            return None
    
    if api_key:
        if 'api' not in settings:
            settings['api'] = {}
        settings['api']['mistral_api_key'] = api_key
        with open(settings_path, 'w', encoding='utf-8') as f:
            yaml.dump(settings, f, allow_unicode=True)
    
    return settings

def render_metric_card(title, value, icon, color="primary"):
    """Renderiza una tarjeta de métrica con estilo personalizado."""
    st.markdown(f"""
        <div class="metric-card">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
                <h3 style="margin: 0;">{title}</h3>
            </div>
            <div style="font-size: 1.5rem; font-weight: bold; color: var(--{color}-color);">
                {value}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_result_card(centro, distancia=None):
    """Renderiza una tarjeta de resultado con estilo personalizado."""
    st.markdown(f"""
        <div class="result-card">
            <h3 style="margin-top: 0;">{centro['nombre']}</h3>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 1rem;">
                <span class="badge badge-primary">{centro['tipo']}</span>
                {f'<span class="badge badge-secondary">{distancia} km</span>' if distancia else ''}
            </div>
            <p style="margin: 0.5rem 0;"><strong>📍 Dirección:</strong> {centro['direccion']}</p>
            <p style="margin: 0.5rem 0;"><strong>📞 Teléfono:</strong> {centro.get('telefono', 'No disponible')}</p>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <button class="stButton">Ver Detalles</button>
                <button class="stButton">Ver en Mapa</button>
                <button class="stButton">⭐ Favorito</button>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renderiza la barra lateral con la configuración."""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h2 style="color: var(--primary-color);">⚙️ Configuración</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # API Key
        st.markdown("### 🔑 API Key de Mistral")
        mistral_api_key = st.text_input("API Key:", type="password", value="")
        if not mistral_api_key:
            mistral_api_key = os.getenv("MISTRAL_API_KEY", "")
        if not mistral_api_key:
            st.error("Por favor, introduce tu API key de Mistral para continuar.")
            st.stop()
        
        # Cargar configuración
        settings = load_or_create_settings(mistral_api_key if mistral_api_key else None)
        if settings and not mistral_api_key:
            mistral_api_key = settings.get('api', {}).get('mistral_api_key', '')
        
        # Modo test
        modo_test = st.checkbox("🧪 Modo test (10 centros aleatorios)", help="Selecciona 10 centros al azar para pruebas")
        
        # Provincias
        st.markdown("### 📍 Provincias")
        provincias_seleccionadas = [p for p in PROVINCIAS if st.checkbox(p)]
        
        # Tipo de centro
        st.markdown("### 🏫 Tipo de Centro")
        tipo_centro = st.radio(
            "Selecciona el tipo de centro:",
            ["Institutos (IES)", "Colegios (CEIP)"]
        )
        
        # Ciudades de preferencia
        st.markdown("### 🌆 Ciudades de Preferencia")
        if 'ciudades_preferencia' not in st.session_state:
            st.session_state.ciudades_preferencia = []
        
        # Añadir ciudad
        col1, col2 = st.columns([3, 1])
        with col1:
            nueva_ciudad = st.text_input("Nueva ciudad:")
        with col2:
            if st.button("➕", help="Añadir ciudad"):
                if nueva_ciudad.strip():
                    if not any(c['nombre'].lower() == nueva_ciudad.strip().lower() for c in st.session_state.ciudades_preferencia):
                        st.session_state.ciudades_preferencia.append({
                            'nombre': nueva_ciudad.strip(),
                            'radio': 50
                        })
                        st.rerun()
                    else:
                        st.warning("Esta ciudad ya está en la lista")
        
        # Lista de ciudades
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
        st.markdown("### 💾 Guardar/Cargar Configuración")
        config_name = st.text_input("Nombre de la configuración:")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Guardar"):
                if config_name:
                    config = {
                        "provincias": provincias_seleccionadas,
                        "tipo_centro": tipo_centro,
                        "ciudades": st.session_state.ciudades_preferencia
                    }
                    if DataProcessor().save_configuration(config, config_name):
                        st.success("✅ Configuración guardada")
                    else:
                        st.error("❌ Error al guardar la configuración")
                else:
                    st.warning("⚠️ Introduce un nombre para la configuración")
        
        with col2:
            if st.button("📂 Cargar"):
                if config_name:
                    config = DataProcessor().load_configuration(config_name)
                    if config:
                        st.session_state.provincias = config.get("provincias", [])
                        st.session_state.tipo_centro = config.get("tipo_centro", "")
                        st.session_state.ciudades_preferencia = config.get("ciudades", [])
                        st.success("✅ Configuración cargada")
                    else:
                        st.error("❌ Configuración no encontrada")
                else:
                    st.warning("⚠️ Introduce un nombre para cargar la configuración")
        
        return mistral_api_key, provincias_seleccionadas, tipo_centro, modo_test

def main():
    """Función principal de la aplicación."""
    st.title("🎓 Selección de Destinos para Interinos de Educación en Andalucía")
    
    # Renderizar sidebar y obtener configuración
    mistral_api_key, provincias_seleccionadas, tipo_centro, modo_test = render_sidebar()
    
    # Validar configuración
    if not mistral_api_key and not load_or_create_settings():
        st.warning("⚠️ Por favor, introduce tu API key de Mistral o configúrala en el archivo settings.yaml")
    elif not provincias_seleccionadas:
        st.warning("⚠️ Por favor, selecciona al menos una provincia.")
    elif not st.session_state.ciudades_preferencia:
        st.warning("⚠️ Por favor, añade al menos una ciudad de preferencia.")
    else:
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            render_metric_card("Provincias Seleccionadas", len(provincias_seleccionadas), "📍")
        with col2:
            render_metric_card("Tipo de Centro", tipo_centro, "🏫")
        with col3:
            render_metric_card("Ciudades de Preferencia", len(st.session_state.ciudades_preferencia), "🌆")
        
        if st.button("🔍 Calcular Destinos", use_container_width=True):
            with st.spinner("⏳ Procesando..."):
                try:
                    os.environ["MISTRAL_API_KEY"] = mistral_api_key
                    df = DataProcessor().load_data(provincias_seleccionadas, tipo_centro)
                    
                    if df.empty:
                        st.error("❌ No se encontraron datos para las provincias seleccionadas.")
                    else:
                        if modo_test:
                            df = df.sample(n=min(10, len(df)))
                            st.info("🧪 Modo test activado: usando 10 centros aleatorios")
                        
                        # Mostrar estadísticas
                        st.markdown("### 📊 Estadísticas")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Provincias seleccionadas:**", ", ".join(provincias_seleccionadas))
                            st.write("**Número total de registros:**", len(df))
                        with col2:
                            st.write("**Registros por provincia:**")
                            for provincia, count in df['Provincia'].value_counts().items():
                                st.write(f"- {provincia}: {count}")
                        
                        resultado = ejecutar_proceso(df, tipo_centro, provincias_seleccionadas, st.session_state.ciudades_preferencia)
                        
                        # Guardar el resultado en el estado de la sesión
                        st.session_state.resultado_actual = resultado
                        
                        st.markdown("### 🎯 Resultados")
                        st.markdown(resultado)
                            
                except Exception as e:
                    st.error(f"❌ Error durante el procesamiento: {str(e)}")
    
    # Mover el botón de exportación fuera del bloque try/except
    if 'resultado_actual' in st.session_state and st.session_state.resultado_actual:
        st.download_button(
            label="📥 Exportar Resultados",
            data=st.session_state.resultado_actual,
            file_name="destinos_ordenados.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: var(--text-color);">
            <p>Desarrollado para interinos de educación en Andalucía</p>
            <p style="font-size: 0.8rem;">© 2024 - Todos los derechos reservados</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 