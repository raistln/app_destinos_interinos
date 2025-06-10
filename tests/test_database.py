import os
import pytest
import tempfile
import shutil
from datetime import datetime
from database.db_manager import DatabaseManager
from database.cache_manager import DistanceCacheManager
from services.geocoding_service import GeocodingService

@pytest.fixture
def temp_db():
    """Fixture para crear una base de datos temporal para testing."""
    # Crear directorio temporal para la base de datos
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    
    # Crear directorio temporal para backups
    backup_dir = os.path.join(temp_dir, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    db_manager = DatabaseManager(db_path)
    yield db_manager
    
    # Eliminar el directorio temporal y todo su contenido
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def cache_manager(temp_db):
    """Fixture para crear un gestor de caché con base de datos temporal."""
    return DistanceCacheManager(temp_db)

@pytest.fixture
def geocoding_service(temp_db):
    """Fixture para crear un servicio de geocodificación con base de datos temporal."""
    return GeocodingService(temp_db)

def test_database_initialization(temp_db):
    """Test de inicialización de la base de datos."""
    # Verificar que las tablas se crearon correctamente
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar tabla ciudades_referencia
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ciudades_referencia'")
        assert cursor.fetchone() is not None
        
        # Verificar tabla centros_educativos
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='centros_educativos'")
        assert cursor.fetchone() is not None
        
        # Verificar tabla distancias_calculadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='distancias_calculadas'")
        assert cursor.fetchone() is not None

def test_distance_cache(cache_manager):
    """Test del sistema de caché de distancias."""
    # Insertar una distancia en caché
    centro_id = 1
    ciudad_id = 1
    distancia = 100.5
    tipo_calculo = 'osrm'
    
    cache_manager.guardar_distancia(centro_id, ciudad_id, distancia, tipo_calculo)
    
    # Verificar que se puede recuperar
    cached_distance = cache_manager.obtener_distancia_cached(centro_id, ciudad_id)
    assert cached_distance == distancia
    
    # Verificar que no existe para otro par
    assert cache_manager.obtener_distancia_cached(2, 2) is None

def test_coordinate_validation(temp_db):
    """Test de validación de coordenadas."""
    # Coordenadas válidas en España
    assert temp_db.validate_spain_coordinates(40.4168, -3.7038)  # Madrid
    assert temp_db.validate_spain_coordinates(37.3891, -5.9845)  # Sevilla
    
    # Coordenadas fuera de España
    assert not temp_db.validate_spain_coordinates(48.8566, 2.3522)  # París
    assert not temp_db.validate_spain_coordinates(40.7128, -74.0060)  # Nueva York

def test_backup_restore(temp_db):
    """Test de backup y restauración de la base de datos."""
    # Crear algunos datos de prueba
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ciudades_referencia (nombre_normalizado, latitud, longitud)
            VALUES (?, ?, ?)
        """, ('madrid', 40.4168, -3.7038))
        conn.commit()
    
    # Crear backup en el directorio temporal
    backup_dir = os.path.join(os.path.dirname(temp_db.db_path), 'backups')
    backup_path = os.path.join(backup_dir, f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    
    temp_db.backup_database(backup_path)
    
    # Verificar que el backup existe
    assert os.path.exists(backup_path)
    
    # Restaurar desde backup
    temp_db.restore_database(backup_path)
    
    # Verificar que los datos se restauraron correctamente
    with temp_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre_normalizado FROM ciudades_referencia")
        assert cursor.fetchone()[0] == 'madrid'

def test_geocoding_service(geocoding_service):
    """Test del servicio de geocodificación."""
    # Test de geocodificación de ciudad
    coords = geocoding_service.geocodificar_ciudad('Madrid')
    assert coords is not None
    assert len(coords) == 2
    assert 40.0 <= coords[0] <= 41.0  # Latitud aproximada de Madrid
    assert -4.0 <= coords[1] <= -3.0  # Longitud aproximada de Madrid
    
    # Verificar que se guardó en la base de datos
    with geocoding_service.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT latitud, longitud FROM ciudades_referencia WHERE nombre_normalizado = ?", ('madrid',))
        result = cursor.fetchone()
        assert result is not None
        assert abs(result[0] - coords[0]) < 0.1
        assert abs(result[1] - coords[1]) < 0.1

def test_cache_stats(cache_manager):
    """Test de estadísticas de caché."""
    # Insertar algunas distancias de prueba
    cache_manager.guardar_distancia(1, 1, 100.0, 'osrm')
    cache_manager.guardar_distancia(1, 2, 200.0, 'geopy')
    cache_manager.guardar_distancia(2, 1, 300.0, 'osrm')
    
    # Obtener estadísticas
    stats = cache_manager.get_cache_stats()
    
    # Verificar estadísticas
    assert stats['total_cached'] == 3
    assert stats['osrm_count'] == 2
    assert stats['geopy_count'] == 1
    assert stats['pending_updates'] == 0
    assert abs(stats['osrm_percentage'] - 66.67) < 0.1  # 2/3 * 100

def test_mark_for_update(cache_manager):
    """Test de marcado para actualización."""
    # Insertar una distancia
    cache_manager.guardar_distancia(1, 1, 100.0, 'geopy')
    
    # Marcar para actualización
    cache_manager.marcar_para_actualizacion(1, 1)
    
    # Verificar que está marcada
    with cache_manager.db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT necesita_actualizacion 
            FROM distancias_calculadas 
            WHERE centro_id = ? AND ciudad_id = ?
        """, (1, 1))
        assert cursor.fetchone()[0] == 1
    
    # Verificar que aparece en la lista de pendientes
    pendientes = cache_manager.obtener_pendientes_actualizacion()
    assert (1, 1) in pendientes 