# Preferencia Interinos Programa

Aplicación para ayudar a los interinos de educación en Andalucía a seleccionar sus destinos preferidos basándose en la proximidad a ciudades de referencia.

## Características

- Selección de provincias andaluzas
- Elección entre Institutos (IES) y Colegios (CEIP)
- Configuración de ciudades de referencia con radios personalizables
- Cálculo de distancias por carretera entre centros y ciudades de referencia
- Ordenación de centros por proximidad a cada ciudad de referencia
- Modo test para pruebas rápidas con 10 centros aleatorios
- Guardado y carga de configuraciones
- Exportación de resultados

## Requisitos

- Python 3.8 o superior
- Cuenta en Mistral AI para obtener una API key
- Archivo `.env` en la raíz del proyecto para cargar la API key (opcional si se ingresa directamente en la interfaz)

## Instalación

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd preferencia_interinos_programa
```

2. Instalar las dependencias:
```bash
poetry install
```

3. Configurar la API key de Mistral:
   - Obtén tu API key de Mistral (ver sección "Obtener API Key de Mistral")
   - Crea un archivo `.env` en la raíz del proyecto.
   - Añade tu API key en el archivo `.env` con el formato:
     ```
     MISTRAL_API_KEY="tu-api-key-aquí"
     ```
   - Alternativamente, puedes ingresar la API key directamente en el campo de texto de la aplicación al ejecutarla.

## Obtener API Key de Mistral

1. Regístrate en [Mistral AI](https://console.mistral.ai/)
2. Una vez registrado, ve a la sección "API Keys"
3. Crea una nueva API key
4. Copia la API key generada
5. Puedes usar la API key de dos formas:
   - Añadirla directamente en la aplicación a través de la interfaz (prioritario).
   - Configurarla en el archivo `.env` en la raíz del proyecto con el formato `MISTRAL_API_KEY="tu-api-key-aquí"`.

## Uso

1. Ejecutar la aplicación:
```bash
poetry run streamlit run src/main.py
```

2. En la interfaz:
   - Introduce tu API key de Mistral en el campo de texto. Si este campo está vacío, la aplicación intentará cargar la key automáticamente desde el archivo `.env`.
   - Selecciona las provincias deseadas
   - Elige el tipo de centro (IES o CEIP)
   - Añade ciudades de referencia:
     - Escribe el nombre de la ciudad
     - Establece el radio en kilómetros (0 = sin límite)
     - Usa el botón "+" para añadirla
   - Opcionalmente, activa el "Modo test" para pruebas rápidas
   - Haz clic en "Calcular Destinos"

3. Los resultados mostrarán:
   - Centros ordenados por proximidad a cada ciudad de referencia
   - Distancias en kilómetros
   - Opción para exportar los resultados

## Configuración

### Guardar Configuración
1. Introduce un nombre para la configuración
2. Haz clic en "Guardar"

### Cargar Configuración
1. Introduce el nombre de la configuración guardada
2. Haz clic en "Cargar"

## Estructura del Proyecto

```
preferencia_interinos_programa/
├── config/
│   ├── settings.example.yaml
│   └── settings.yaml
├── data/
│   └── centros_educativos.csv
├── src/
│   ├── main.py
│   ├── llm_connector.py
│   ├── distance_calculator.py
│   └── processor.py
├── requirements.txt
└── README.md
```

## Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Samuel - [@tutwitter](https://twitter.com/tutwitter) - email@example.com

Link del proyecto: [https://github.com/tuusuario/preferencia_interinos_programa](https://github.com/tuusuario/preferencia_interinos_programa)
