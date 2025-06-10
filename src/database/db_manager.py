import sqlite3
import os
from typing import Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def adapt_datetime(dt: datetime) -> str:
    """Adapta un objeto datetime a string para SQLite."""
    return dt.isoformat()

def convert_datetime(s: str) -> datetime:
    """Convierte un string de SQLite a datetime."""
    return datetime.fromisoformat(s)

# Registrar los adaptadores de fecha/hora
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("datetime", convert_datetime)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info(f"Initializing database at path: {self.db_path}")
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        logger.info(f"Database directory ensured at: {os.path.dirname(self.db_path)}")

    def _init_db(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            
            # Create ciudades_referencia table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ciudades_referencia (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_normalizado TEXT UNIQUE NOT NULL,
                    latitud REAL NOT NULL,
                    longitud REAL NOT NULL,
                    fecha_geocodificacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create centros_educativos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS centros_educativos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    direccion TEXT,
                    municipio TEXT NOT NULL,
                    provincia TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    latitud REAL,
                    longitud REAL,
                    fecha_geocodificacion DATETIME,
                    geocodificado BOOLEAN DEFAULT FALSE
                )
            """)

            # Create distancias_calculadas table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS distancias_calculadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    centro_id INTEGER NOT NULL,
                    ciudad_id INTEGER NOT NULL,
                    distancia_km REAL NOT NULL,
                    tipo_calculo TEXT NOT NULL,
                    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP,
                    necesita_actualizacion BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (centro_id) REFERENCES centros_educativos(id),
                    FOREIGN KEY (ciudad_id) REFERENCES ciudades_referencia(id),
                    UNIQUE(centro_id, ciudad_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_distancias_centro_ciudad 
                ON distancias_calculadas(centro_id, ciudad_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_distancias_tipo 
                ON distancias_calculadas(tipo_calculo)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_centros_municipio 
                ON centros_educativos(municipio, provincia)
            """)

            conn.commit()
            logger.info("Database initialized successfully with required tables and indexes.")

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def backup_database(self, backup_path: str):
        """Create a backup of the database."""
        import shutil
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(self.db_path, backup_path)
        logger.info(f"Database backed up to {backup_path}")

    def restore_database(self, backup_path: str):
        """Restore database from backup."""
        import shutil
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        shutil.copy2(backup_path, self.db_path)
        logger.info(f"Database restored from {backup_path}")

    def validate_spain_coordinates(self, lat: float, lon: float) -> bool:
        """Validate if coordinates are within Spain's bounds."""
        return (36 <= lat <= 44) and (-10 <= lon <= 5) 