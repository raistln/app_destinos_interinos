.PHONY: install test lint clean run

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
FLAKE8 = flake8
BLACK = black

# Instalación
install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt

# Testing
test:
	$(PYTEST) tests/

test-coverage:
	$(PYTEST) --cov=src --cov-report=html tests/

# Linting
lint:
	$(FLAKE8) src/ tests/
	$(BLACK) --check src/ tests/

format:
	$(BLACK) src/ tests/

# Limpieza
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

# Ejecución
run:
	$(PYTHON) main.py

# Desarrollo
dev-install: install
	pre-commit install

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make install      - Instala las dependencias"
	@echo "  make test         - Ejecuta los tests"
	@echo "  make test-coverage- Ejecuta los tests con cobertura"
	@echo "  make lint         - Ejecuta el linter"
	@echo "  make format       - Formatea el código"
	@echo "  make clean        - Limpia archivos temporales"
	@echo "  make run          - Ejecuta la aplicación"
	@echo "  make dev-install  - Instala dependencias de desarrollo" 