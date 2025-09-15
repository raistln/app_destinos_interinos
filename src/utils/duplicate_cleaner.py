"""
Utilidad para limpiar duplicados de ciudades directamente desde Streamlit.
"""

import streamlit as st
import logging
from typing import Dict, List
from .city_normalizer import normalize_city_name

logger = logging.getLogger(__name__)


class DuplicateCleaner:
    """Limpiador de ciudades duplicadas para usar en Streamlit."""
    
    def __init__(self, db_manager):
        """
        Inicializa el limpiador con un gestor de base de datos.
        
        Args:
            db_manager: Instancia del gestor de base de datos (SupabaseManager)
        """
        self.db = db_manager
    
    def find_duplicates(self) -> Dict[str, List[Dict]]:
        """
        Encuentra ciudades duplicadas basándose en nombres normalizados.
        
        Returns:
            Dict con grupos de ciudades duplicadas
        """
        try:
            # Obtener todas las ciudades
            result = self.db.supabase.table('ciudades').select('*').order('created_at').execute()
            cities = result.data
            
            if not cities:
                return {}
            
            # Agrupar por nombre normalizado
            normalized_groups = {}
            
            for city in cities:
                normalized_name = normalize_city_name(city['nombre'])
                
                if normalized_name not in normalized_groups:
                    normalized_groups[normalized_name] = []
                
                normalized_groups[normalized_name].append(city)
            
            # Filtrar solo los grupos con duplicados
            duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Error buscando duplicados: {e}")
            return {}
    
    def remove_duplicate(self, city_id: int, keep_city_name: str) -> bool:
        """
        Elimina una ciudad duplicada y actualiza referencias.
        
        Args:
            city_id: ID de la ciudad a eliminar
            keep_city_name: Nombre de la ciudad que se mantiene
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            # Obtener información de la ciudad a eliminar
            city_result = self.db.supabase.table('ciudades').select('*').eq('id', city_id).execute()
            if not city_result.data:
                return False
            
            city_to_remove = city_result.data[0]
            
            # Actualizar referencias en tabla de distancias si existe
            try:
                # Buscar distancias que referencien la ciudad a eliminar
                dist_result = self.db.supabase.table('distancias').select('*').or_(
                    f'ciudad1.eq.{city_to_remove["nombre"]},ciudad2.eq.{city_to_remove["nombre"]}'
                ).execute()
                
                # Actualizar referencias
                for dist in dist_result.data:
                    update_data = {}
                    if dist['ciudad1'] == city_to_remove['nombre']:
                        update_data['ciudad1'] = keep_city_name
                    if dist['ciudad2'] == city_to_remove['nombre']:
                        update_data['ciudad2'] = keep_city_name
                    
                    if update_data:
                        self.db.supabase.table('distancias').update(update_data).eq('id', dist['id']).execute()
            except Exception as e:
                logger.warning(f"Error actualizando referencias de distancias: {e}")
            
            # Eliminar la ciudad
            self.db.supabase.table('ciudades').delete().eq('id', city_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando ciudad {city_id}: {e}")
            return False


def render_duplicate_cleaner_ui():
    """
    Renderiza la interfaz de usuario para limpiar duplicados.
    Debe llamarse desde una página de Streamlit.
    """
    st.header("🧹 Limpiador de Ciudades Duplicadas")
    
    # Importar aquí para evitar problemas de dependencias circulares
    try:
        from database.supabase_manager import SupabaseManager
        db = SupabaseManager()
        cleaner = DuplicateCleaner(db)
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {e}")
        return
    
    # Buscar duplicados
    if st.button("🔍 Buscar Duplicados"):
        with st.spinner("Buscando ciudades duplicadas..."):
            duplicates = cleaner.find_duplicates()
            st.session_state.duplicates = duplicates
    
    # Mostrar duplicados si existen
    if 'duplicates' in st.session_state and st.session_state.duplicates:
        duplicates = st.session_state.duplicates
        
        st.success(f"✅ Encontrados {len(duplicates)} grupos de ciudades duplicadas")
        
        for normalized_name, cities in duplicates.items():
            st.subheader(f"📍 Grupo: '{normalized_name}'")
            
            # Ordenar por fecha de creación (más antigua primero)
            cities.sort(key=lambda x: x.get('created_at', ''))
            
            # Mostrar información de cada ciudad
            cols = st.columns(len(cities))
            
            for i, city in enumerate(cities):
                with cols[i]:
                    # Determinar si es la más antigua (recomendada para mantener)
                    is_oldest = i == 0
                    
                    if is_oldest:
                        st.success("✅ **MANTENER** (más antigua)")
                    else:
                        st.warning("⚠️ Duplicado")
                    
                    st.write(f"**ID:** {city['id']}")
                    st.write(f"**Nombre:** {city['nombre']}")
                    st.write(f"**Provincia:** {city['provincia']}")
                    st.write(f"**Creada:** {city.get('created_at', 'N/A')}")
                    
                    # Botón para eliminar (solo para duplicados)
                    if not is_oldest:
                        if st.button(f"🗑️ Eliminar", key=f"delete_{city['id']}"):
                            with st.spinner(f"Eliminando ciudad {city['nombre']}..."):
                                success = cleaner.remove_duplicate(city['id'], cities[0]['nombre'])
                                
                                if success:
                                    st.success(f"✅ Ciudad eliminada: {city['nombre']}")
                                    # Actualizar la lista de duplicados
                                    del st.session_state.duplicates
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error eliminando ciudad: {city['nombre']}")
            
            st.divider()
    
    elif 'duplicates' in st.session_state:
        st.info("🎉 No se encontraron ciudades duplicadas")
    
    # Información adicional
    with st.expander("ℹ️ Información sobre la limpieza"):
        st.markdown("""
        **¿Cómo funciona?**
        
        1. **Detección:** Busca ciudades con nombres que se normalizan al mismo valor
        2. **Recomendación:** Sugiere mantener la ciudad más antigua
        3. **Limpieza:** Elimina duplicados y actualiza referencias en otras tablas
        
        **Ejemplos de duplicados detectados:**
        - "La Zubia" y "zubia" → se normalizan a "zubia"
        - "San Fernando" y "fernando" → se normalizan a "fernando"
        - "El Puerto" y "Puerto" → se normalizan a "puerto"
        
        **⚠️ Precaución:** Esta operación no se puede deshacer. Asegúrate de mantener la ciudad correcta.
        """)


# Función de conveniencia para usar en otras partes de la app
def get_duplicate_count() -> int:
    """
    Obtiene el número de grupos de ciudades duplicadas.
    
    Returns:
        Número de grupos de duplicados encontrados
    """
    try:
        from database.supabase_manager import SupabaseManager
        db = SupabaseManager()
        cleaner = DuplicateCleaner(db)
        duplicates = cleaner.find_duplicates()
        return len(duplicates)
    except Exception as e:
        logger.error(f"Error obteniendo conteo de duplicados: {e}")
        return 0
