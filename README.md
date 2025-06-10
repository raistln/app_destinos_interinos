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

## Video Tutorial

Para ver una explicación detallada de cómo usar la aplicación, puedes ver el siguiente video tutorial:

[![Video Tutorial](https://img.youtube.com/vi/1iMq3vuc5gM/0.jpg)](https://youtu.be/1iMq3vuc5gM)

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
├── config/           # Configuraciones de la aplicación
├── data/            # Datos de centros educativos
├── saved_configs/   # Configuraciones guardadas por el usuario
├── src/             # Código fuente de la aplicación
├── tests/           # Tests unitarios
├── main.py          # Punto de entrada de la aplicación
├── requirements.txt # Dependencias del proyecto
└── README.md        # Este archivo
```

## Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Desarrollo

### Instalación para desarrollo

1. Instalar dependencias de desarrollo:
```bash
poetry install --with dev
```

2. Instalar pre-commit hooks:
```bash
pre-commit install
```

### Testing

Para ejecutar los tests:
```bash
poetry run pytest
```

Para ver la cobertura de tests:
```bash
poetry run pytest --cov=src tests/
```

## Solución de problemas comunes

### Error de API Key
Si recibes un error relacionado con la API key:
1. Verifica que la API key sea válida
2. Asegúrate de que el archivo `.env` está en la raíz del proyecto
3. Intenta ingresar la API key directamente en la interfaz

### Error de conexión
Si la aplicación no puede conectarse a los servicios:
1. Verifica tu conexión a internet
2. Asegúrate de que los servicios de Mistral AI estén operativos
3. Revisa los logs en la carpeta `logs/` para más detalles

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Samuel - [LinkedIn](https://www.linkedin.com/in/samuel-mart%C3%ADn-fonseca-74014b17/) - samumarfon@gmail.com

Link del proyecto: [https://github.com/tuusuario/preferencia_interinos_programa](https://github.com/tuusuario/preferencia_interinos_programa)
