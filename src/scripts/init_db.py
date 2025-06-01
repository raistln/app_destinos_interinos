import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager
from src.services.geocoding_service import GeocodingService
from src.services.distance_service import OptimizedDistanceService

def setup_logging(config):
    """Set up logging configuration."""
    log_dir = os.path.dirname(config['logging']['file'])
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=config['logging']['level'],
        format=config['logging']['format'],
        handlers=[
            logging.FileHandler(config['logging']['file']),
            logging.StreamHandler()
        ]
    )

def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'database.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)

def init_database(config):
    """Initialize database and create necessary directories."""
    # Create data directory
    os.makedirs(os.path.dirname(config['database']['path']), exist_ok=True)
    os.makedirs(config['database']['backup_path'], exist_ok=True)
    
    # Initialize database
    db_manager = DatabaseManager(config['database']['path'])
    return db_manager

def main():
    """Main initialization function."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        db_manager = init_database(config)
        
        # Initialize services
        geocoding_service = GeocodingService(db_manager)
        distance_service = OptimizedDistanceService(db_manager)
        
        # Create backup
        backup_path = os.path.join(
            config['database']['backup_path'],
            f"initial_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        db_manager.backup_database(backup_path)
        
        logger.info("Database initialization completed successfully")
        logger.info(f"Database backup created at: {backup_path}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 