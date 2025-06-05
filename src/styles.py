"""
Estilos personalizados para la aplicación Streamlit.
"""

CUSTOM_CSS = """
<style>
/* Variables de colores */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #00b894;
    --warning-color: #fdcb6e;
    --info-color: #74b9ff;
    --background-color: #f8f9fa;
    --text-color: #2d3436;
}

/* Estilos generales */
.stApp {
    background-color: var(--background-color);
}

/* Header principal */
.main .block-container {
    padding-top: 2rem;
}

h1 {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    font-size: 2.5rem !important;
    margin-bottom: 2rem !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

/* Sidebar */
.sidebar .sidebar-content {
    background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
    border-right: 1px solid rgba(0,0,0,0.1);
}

/* Contenedores */
.stContainer {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    border-left: 4px solid var(--primary-color);
}

/* Cards de métricas */
.metric-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    border-top: 3px solid var(--primary-color);
    transition: transform 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Botones personalizados */
.stButton>button {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border: none;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

/* Inputs y selects */
.stTextInput>div>div>input,
.stSelectbox>div>div>select {
    border-radius: 5px;
    border: 1px solid #ddd;
    padding: 0.5rem;
}

/* Mensajes de estado */
.stSuccess {
    background-color: var(--success-color);
    color: white;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}

.stError {
    background-color: #ff7675;
    color: white;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}

/* Tarjetas de resultados */
.result-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}

.result-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

/* Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.25rem;
}

.badge-primary {
    background-color: var(--primary-color);
    color: white;
}

.badge-secondary {
    background-color: var(--secondary-color);
    color: white;
}

/* Footer */
footer {
    text-align: center;
    padding: 2rem 0;
    color: var(--text-color);
    font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
    .stContainer {
        padding: 1rem;
    }
    
    h1 {
        font-size: 2rem !important;
    }
}
</style>
"""

def apply_custom_styles():
    """Aplica los estilos personalizados a la aplicación."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True) 