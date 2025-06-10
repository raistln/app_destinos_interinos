import pytest
from unittest.mock import patch, MagicMock
from distance_calculator import DistanceCalculator
import pandas as pd

@pytest.fixture
def calculator():
    return DistanceCalculator()

def test_get_coordinates_cache(calculator):
    # Simular que ya hay coordenadas en el caché
    calculator.coordinates_cache['Granada, Granada, España'] = (37.18, -3.6)
    coords = calculator._get_coordinates('Granada', 'Granada')
    assert coords == (37.18, -3.6)

@patch('src.distance_calculator.Nominatim')
def test_get_coordinates_external(mock_nominatim, calculator):
    # Simular respuesta de la API externa
    instance = mock_nominatim.return_value
    instance.geocode.return_value = MagicMock(latitude=37.18, longitude=-3.6)
    calculator.coordinates_cache = {}
    coords = calculator._get_coordinates('Granada', 'Granada')
    assert coords[0] == pytest.approx(37.18, abs=0.01)
    assert coords[1] == pytest.approx(-3.6, abs=0.01)

@patch('src.distance_calculator.DistanceCalculator._get_coordinates')
@patch('src.distance_calculator.requests.get')
def test_get_distance_osrm(mock_requests_get, mock_get_coords, calculator):
    # Simular coordenadas
    mock_get_coords.side_effect = [(37.18, -3.6), (36.72, -4.42)]
    # Simular respuesta OSRM
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'code': 'Ok', 'routes': [{'distance': 100000}]}
    mock_requests_get.return_value = mock_response
    dist = calculator.get_distance('Granada', 'Granada', 'Malaga', 'Malaga')
    assert abs(dist - 100.0) < 0.01

@patch('src.distance_calculator.DistanceCalculator._get_coordinates')
def test_get_distance_fallback_geodesic(mock_get_coords, calculator):
    # Simular coordenadas
    mock_get_coords.side_effect = [(37.18, -3.6), (36.72, -4.42)]
    # Simular fallo en OSRM
    with patch('src.distance_calculator.requests.get', side_effect=Exception()):
        dist = calculator.get_distance('Granada', 'Granada', 'Malaga', 'Malaga')
        assert dist > 0

def test_normalize_column_names(calculator):
    df = pd.DataFrame({
        'codigo': [1],
        'nombre': ['Centro'],
        'provincia': ['Granada']
    })
    norm = calculator._normalize_column_names(df)
    assert 'Código' in norm.columns
    assert 'Nombre' in norm.columns
    assert 'Provincia' in norm.columns

def test_load_centers_data(tmp_path):
    # Crear estructura de carpetas y archivo CSV
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    prov_dir = data_dir / "Granada"
    prov_dir.mkdir()
    csv_path = prov_dir / "institutos.csv"
    df = pd.DataFrame({'codigo': [1], 'nombre': ['Centro'], 'provincia': ['Granada']})
    df.to_csv(csv_path, index=False)
    calc = DistanceCalculator()
    result = calc.load_centers_data(str(data_dir), ['Granada'])
    assert not result.empty
    assert 'Provincia' in result.columns

def test_normalize_city_name(calculator):
    assert calculator._normalize_city_name('granada') == 'Granada'
    assert calculator._normalize_city_name('SAN SEBASTIAN') == 'San Sebastian'
    assert calculator._normalize_city_name('la-zubia') == 'La Zubia'

def test_get_unique_localities(calculator):
    df = pd.DataFrame({
        'Localidad': ['Granada', 'Motril'],
        'Provincia': ['Granada', 'Granada']
    })
    result = calculator.get_unique_localities(df)
    assert isinstance(result, list)
    assert {'Localidad': 'Granada', 'Provincia': 'Granada'} in result

def test_sort_localities_by_distance(calculator):
    refs = [{'nombre': 'Granada', 'Provincia': 'Granada', 'radio': 50}]
    localities = [
        {'Localidad': 'Granada', 'Provincia': 'Granada'},
        {'Localidad': 'Motril', 'Provincia': 'Granada'}
    ]
    # Mock distances: Granada is within radius (10km), Motril is outside (60km)
    # We need to provide values for Granada->Granada, Granada->Motril, and potentially others
    with patch.object(calculator, 'get_distance', side_effect=[10.0, 60.0, 10.0, 60.0, 10.0]):
        sorted_locs = calculator.sort_localities_by_distance(refs, localities)
        # Should only include Granada since it's within radius
        assert len(sorted_locs) == 1
        assert sorted_locs[0]['Localidad'] == 'Granada'
        assert sorted_locs[0]['Provincia'] == 'Granada'