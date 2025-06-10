import pytest
import pandas as pd
from processor import DataProcessor
import os
import yaml
from pathlib import Path
from unittest.mock import patch

def test_load_data(tmp_path):
    # Crear estructura de carpetas y archivo CSV
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    prov_dir = data_dir / "Granada"
    prov_dir.mkdir()
    csv_path = prov_dir / "institutos.csv"
    df = pd.DataFrame({'codigo': [1], 'nombre': ['Centro'], 'provincia': ['Granada']})
    df.to_csv(csv_path, index=False)
    processor = DataProcessor(str(data_dir))
    result = processor.load_data(['Granada'], 'Institutos (IES)')
    assert not result.empty
    assert 'provincia' in result.columns

def test_save_and_load_configuration(tmp_path, monkeypatch):
    config = {'provincias': ['Granada'], 'tipo_centro': 'IES', 'ciudades': [{'nombre': 'Granada', 'radio': 50}]}
    # Use the temporary directory directly for saving configurations
    save_dir = tmp_path / "saved_configs"
    save_dir.mkdir()
    processor = DataProcessor() # Initialize with default data_dir
    
    # Mock the configuration directory to the temporary directory
    monkeypatch.setattr('src.processor.Path', lambda *args: save_dir)

    nombre = "test_config"
    # Guardar
    assert processor.save_configuration(config, nombre)

    # Check if the file exists before loading
    config_path = save_dir / f"{nombre}.yaml"
    assert config_path.exists() # Assert the file was created
    
    # Cargar (use the same processor instance as the directory is mocked globally)
    loaded = processor.load_configuration(nombre)
    assert loaded == config # Compare the loaded config with the original

def test_load_configuration_not_found(tmp_path, monkeypatch):
    processor = DataProcessor()
    nombre = "no_existe"
    # Use the temporary directory directly for saving configurations
    save_dir = tmp_path / "saved_configs"
    save_dir.mkdir()
    
    # Mock the configuration directory to the temporary directory
    monkeypatch.setattr('src.processor.Path', lambda *args: save_dir)

    result = processor.load_configuration(nombre)
    assert result == {} 