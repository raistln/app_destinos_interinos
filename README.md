# 🎓 Selección de Destinos para Interinos de Educación - Andalucía

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Samuel%20Martín%20Fonseca-blue)](https://www.linkedin.com/in/samuel-mart%C3%ADn-fonseca-74014b17/)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow)](https://www.buymeacoffee.com/samumarfon)

Una aplicación web interactiva que ayuda a los **interinos de educación en Andalucía** a seleccionar sus destinos preferidos basándose en la proximidad a ciudades de referencia. Desarrollada con Streamlit y optimizada para facilitar la toma de decisiones en el proceso de selección de plazas educativas.

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

## 🛠️ Instalación Local

1. **Clonar el repositorio:**
```bash
git clone https://github.com/tuusuario/app_destinos_interinos.git
cd app_destinos_interinos
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

O con Poetry:
```bash
poetry install
```

3. **Configurar API Key:**
   - Obtén tu API key **gratuita** de [Mistral AI](https://console.mistral.ai/)
   - Opción 1: Crear archivo `.env`:
     ```
     MISTRAL_API_KEY="tu-api-key-aquí"
     ```
   - Opción 2: Introducir directamente en la aplicación
   - Opción 3: Para Streamlit Cloud, usar `.streamlit/secrets.toml`

## Obtener API Key de Mistral

1. Regístrate en [Mistral AI](https://console.mistral.ai/)
2. Una vez registrado, ve a la sección "API Keys"
3. Crea una nueva API key
4. Copia la API key generada
5. Puedes usar la API key de dos formas:
   - Añadirla directamente en la aplicación a través de la interfaz (prioritario).
   - Configurarla en el archivo `.env` en la raíz del proyecto con el formato `MISTRAL_API_KEY="tu-api-key-aquí"`.

## 🚀 Demo en Vivo

**[Prueba la aplicación aquí](https://your-app-url.streamlit.app)** 👈

## 💻 Uso Local

1. Ejecutar la aplicación:
```bash
streamlit run app.py
```

O con Poetry:
```bash
poetry run streamlit run app.py
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

## 📁 Estructura del Proyecto

```
app_destinos_interinos/
├── 📁 config/              # Configuraciones
├── 📁 data/               # Datos de centros educativos por provincia
├── 📁 src/                # Código fuente
│   ├── 📁 database/       # Gestión de base de datos SQLite
│   ├── 📁 services/       # Servicios de geocodificación y distancias
│   ├── distance_calculator.py  # Cálculo de distancias
│   ├── llm_connector.py   # Conexión con Mistral AI
│   └── styles.py          # Estilos CSS personalizados
├── 📁 tests/              # Tests unitarios
├── 📁 .streamlit/         # Configuración de Streamlit
├── app.py                 # 🚀 Aplicación principal
├── requirements.txt       # Dependencias
└── README.md             # Este archivo
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

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar la aplicación:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## ☕ Apoya el Proyecto

Si esta aplicación te ha sido útil, considera invitarme a un café:

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/samumarfon)

## 📞 Contacto

**Samuel Martín Fonseca**
- 💼 [LinkedIn](https://www.linkedin.com/in/samuel-mart%C3%ADn-fonseca-74014b17/)
- 📧 samumarfon@gmail.com
- 🌐 [Proyecto en GitHub](https://github.com/tuusuario/app_destinos_interinos)

---

<div align="center">
  <p><strong>Desarrollado con ❤️ para la comunidad educativa de Andalucía</strong></p>
  <p><em>© 2024 Samuel Martín Fonseca - Todos los derechos reservados</em></p>
</div>
