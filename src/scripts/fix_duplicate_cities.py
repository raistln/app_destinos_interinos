"""
Script para limpiar ciudades duplicadas en la base de datos.
Este script identifica y elimina duplicados basándose en nombres normalizados.
"""

import sys
import os
from pathlib import Path

# Añadir el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.supabase_manager import SupabaseManager
from utils.city_normalizer import normalize_city_name
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_duplicate_cities():
    """
    Encuentra ciudades duplicadas en la base de datos basándose en nombres normalizados.
    
    Returns:
        dict: Diccionario con ciudades duplicadas agrupadas por nombre normalizado
    """
    db = SupabaseManager()
    
    try:
        # Obtener todas las ciudades
        result = db.supabase.table('ciudades').select('id, nombre, provincia, latitud, longitud, created_at').order('created_at').execute()
        cities = result.data
        
        if not cities:
            logger.info("No se encontraron ciudades en la base de datos")
            return {}
        
        # Agrupar por nombre normalizado
        normalized_groups = {}
        
        for city in cities:
            normalized_name = normalize_city_name(city['nombre'])
            
            if normalized_name not in normalized_groups:
                normalized_groups[normalized_name] = []
            
            normalized_groups[normalized_name].append({
                'id': city['id'],
                'nombre': city['nombre'],
                'provincia': city['provincia'],
                'latitud': city['latitud'],
                'longitud': city['longitud'],
                'created_at': city['created_at'],
                'normalized': normalized_name
            })
        
        # Filtrar solo los grupos con duplicados
        duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}
        
        return duplicates
        
    except Exception as e:
        logger.error(f"Error al buscar duplicados: {e}")
        return {}


def fix_duplicate_cities(dry_run=True):
    """
    Corrige las ciudades duplicadas manteniendo la más antigua y actualizando referencias.
    
    Args:
        dry_run (bool): Si True, solo muestra lo que haría sin hacer cambios
    """
    db = DatabaseManager()
    duplicates = find_duplicate_cities()
    
    if not duplicates:
        logger.info("✅ No se encontraron ciudades duplicadas")
        return
    
    logger.info(f"🔍 Encontrados {len(duplicates)} grupos de ciudades duplicadas:")
    
    total_removed = 0
    
    for normalized_name, cities in duplicates.items():
        logger.info(f"\n📍 Grupo '{normalized_name}':")
        
        # Ordenar por fecha de creación (más antigua primero)
        cities.sort(key=lambda x: x['created_at'])
        
        # La primera (más antigua) es la que mantenemos
        keep_city = cities[0]
        remove_cities = cities[1:]
        
        logger.info(f"  ✅ Mantener: ID {keep_city['id']} - '{keep_city['nombre']}' ({keep_city['created_at']})")
        
        for city in remove_cities:
            logger.info(f"  ❌ Eliminar: ID {city['id']} - '{city['nombre']}' ({city['created_at']})")
            
            if not dry_run:
                try:
                    # Actualizar referencias en distancias si existen
                    # Buscar distancias que referencien la ciudad a eliminar
                    dist_result = db.supabase.table('distancias').select('*').or_(f'ciudad1.eq.{city["nombre"]},ciudad2.eq.{city["nombre"]}').execute()
                    
                    # Actualizar referencias a la ciudad que mantenemos
                    for dist in dist_result.data:
                        update_data = {}
                        if dist['ciudad1'] == city['nombre']:
                            update_data['ciudad1'] = keep_city['nombre']
                        if dist['ciudad2'] == city['nombre']:
                            update_data['ciudad2'] = keep_city['nombre']
                        
                        if update_data:
                            db.supabase.table('distancias').update(update_data).eq('id', dist['id']).execute()
                    
                    # Eliminar la ciudad duplicada
                    db.supabase.table('ciudades').delete().eq('id', city['id']).execute()
                    
                    total_removed += 1
                    logger.info(f"    ✅ Eliminada ciudad ID {city['id']}")
                    
                except Exception as e:
                    logger.error(f"    ❌ Error al eliminar ciudad ID {city['id']}: {e}")
    
    if dry_run:
        logger.info(f"\n🧪 DRY RUN: Se eliminarían {sum(len(cities) - 1 for cities in duplicates.values())} ciudades duplicadas")
        logger.info("Para ejecutar los cambios, ejecuta: python fix_duplicate_cities.py --execute")
    else:
        logger.info(f"\n✅ Proceso completado. Eliminadas {total_removed} ciudades duplicadas")


def update_existing_cities_to_normalized():
    """
    Actualiza los nombres de las ciudades existentes a su versión normalizada.
    """
    db = SupabaseManager()
    
    try:
        # Obtener todas las ciudades
        result = db.supabase.table('ciudades').select('id, nombre').execute()
        cities = result.data
        
        if not cities:
            logger.info("No se encontraron ciudades para actualizar")
            return
        
        updated_count = 0
        
        for city in cities:
            normalized_name = normalize_city_name(city['nombre'])
            
            # Solo actualizar si el nombre cambió
            if normalized_name != city['nombre']:
                db.supabase.table('ciudades').update({'nombre': normalized_name}).eq('id', city['id']).execute()
                logger.info(f"Actualizado: '{city['nombre']}' -> '{normalized_name}'")
                updated_count += 1
        
        logger.info(f"✅ Actualizados {updated_count} nombres de ciudades")
        
    except Exception as e:
        logger.error(f"Error al actualizar nombres: {e}")


def main():
    """Función principal del script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Limpiar ciudades duplicadas en la base de datos")
    parser.add_argument("--execute", action="store_true", help="Ejecutar los cambios (por defecto es dry-run)")
    parser.add_argument("--normalize", action="store_true", help="Normalizar nombres de ciudades existentes")
    parser.add_argument("--show-duplicates", action="store_true", help="Solo mostrar duplicados sin hacer cambios")
    
    args = parser.parse_args()
    
    if args.show_duplicates:
        duplicates = find_duplicate_cities()
        if duplicates:
            print(f"\n🔍 Encontrados {len(duplicates)} grupos de ciudades duplicadas:")
            for normalized_name, cities in duplicates.items():
                print(f"\n📍 '{normalized_name}':")
                for city in cities:
                    print(f"  - ID {city['id']}: '{city['nombre']}' ({city['created_at']})")
        else:
            print("✅ No se encontraron ciudades duplicadas")
        return
    
    if args.normalize:
        logger.info("🔄 Normalizando nombres de ciudades existentes...")
        update_existing_cities_to_normalized()
    
    logger.info("🧹 Iniciando limpieza de ciudades duplicadas...")
    fix_duplicate_cities(dry_run=not args.execute)


if __name__ == "__main__":
    main()
