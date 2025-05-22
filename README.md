# Aplicación de Selección de Destinos para Interinos de Educación en Andalucía

Esta aplicación ayuda a los profesores interinos de Andalucía a ordenar sus preferencias de destinos durante o después de los procesos de oposición. Permite seleccionar provincias específicas, indicar localidades de preferencia, y generar una lista ordenada de posibles destinos basados en proximidad geográfica.

## Características

- Selección de provincias andaluzas
- Elección entre Institutos (IES) o Colegios (CEIP)
- Ordenamiento de destinos según proximidad geográfica
- Guardado y carga de configuraciones
- Exportación de resultados
- Interfaz intuitiva y fácil de usar

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Cuenta de OpenAI o Mistral (para el procesamiento con LLM)

## Instalación

1. Clona este repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd [NOMBRE_DEL_DIRECTORIO]
```

2. Crea un entorno virtual e instálalo:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

4. Configura el entorno:
   - Copia el archivo de ejemplo de configuración:
     ```bash
     cp config/settings.example.yaml config/settings.yaml
     ```
   - Crea un archivo `.env` en la raíz del proyecto con tus API keys:
     ```
     MISTRAL_API_KEY=tu_api_key_de_mistral
     OPENAI_API_KEY=tu_api_key_de_openai
     ```
   - Edita `config/settings.yaml` según tus necesidades

## Estructura de Datos

La aplicación espera encontrar los datos de los centros educativos en la siguiente estructura:

```
/data
  /Almeria
    - institutos.csv
    - colegios.csv
  /Cadiz
    - institutos.csv
    - colegios.csv
  ...
```

Cada archivo CSV debe contener al menos las siguientes columnas:
- Código
- Denominación
- Nombre
- Dependencia
- Localidad
- Municipio
- Provincia
- Código Postal

Las siguientes columnas son opcionales y no se utilizarán en el procesamiento:
- Domicilio
- Teléfono
- Enseñanzas
- Servicios
- Biling

## Uso

1. Inicia la aplicación:
```bash
streamlit run src/main.py
```

2. En el navegador, selecciona:
   - Las provincias de interés
   - El tipo de centro (IES o CEIP)
   - Las ciudades de preferencia (una por línea, en orden de prioridad)

3. Haz clic en "Calcular Destinos" para procesar la información

4. Opcionalmente:
   - Guarda tu configuración para uso futuro
   - Exporta los resultados como archivo de texto

## Configuración

La aplicación soporta tanto Mistral como OpenAI para el procesamiento de la proximidad geográfica. La configuración se realiza en el archivo `config/settings.yaml`:

1. Selecciona el proveedor de LLM:
   ```yaml
   llm:
     provider: mistral  # o 'openai'
   ```

2. Configura los parámetros del modelo:
   ```yaml
   llm:
     temperature: 0.7  # Ajusta según necesites
     max_tokens: 1000  # Ajusta según necesites
   ```

3. Personaliza la interfaz:
   ```yaml
   ui:
     theme: light  # o 'dark'
     language: es
   ```

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

La Licencia MIT es una licencia de software permisiva que permite:
- Uso comercial
- Modificación
- Distribución
- Uso privado

Con las siguientes condiciones:
- Incluir el aviso de copyright y la licencia en todas las copias
- No hay garantía de ningún tipo

## Contacto

[Tu información de contacto aquí]
