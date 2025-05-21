# Prompt para Desarrollar una Aplicación de Selección de Destinos para Interinos de Educación en Andalucía

## Contexto y Objetivo
Desarrollar una herramienta práctica para profesores interinos de Andalucía que les ayude a ordenar sus preferencias de destinos durante o después de los procesos de oposición. La aplicación debe permitir a los usuarios seleccionar provincias específicas, indicar sus localidades de preferencia, y generar una lista ordenada de posibles destinos (centros educativos) basados en proximidad geográfica.

## Requisitos Funcionales

### Interfaz de Usuario
- **Panel Principal**: Implementar una interfaz simple y funcional con tres secciones principales:
  1. **Selección de Provincias**: Mostrar las 8 provincias andaluzas (Almería, Cádiz, Córdoba, Granada, Huelva, Jaén, Málaga y Sevilla) con casillas de verificación.
  2. **Tipo de Centro**: Añadir selector entre "Institutos" (IES) o "Colegios" (CEIP) públicos.
  3. **Ciudades de Preferencia**: Permitir añadir/eliminar múltiples localidades de referencia en orden de prioridad.
  4. **Sección de Resultados**: Área donde se mostrará la lista ordenada de destinos.

- **Controles**:
  - Botón "Calcular" para iniciar el procesamiento.
  - Opción para guardar/cargar configuraciones previas.
  - Indicador visual del estado del procesamiento.

### Gestión de Datos
- **Estructura de Datos**:
  - Organizar archivos CSV por provincia en `/data/{provincia}/` (ej. `/data/Granada/`)
  - Separar archivos según tipo de centro: `institutos.csv` y `colegios.csv`

- **Formato de CSV** (campos mínimos necesarios):
  - Código del centro
  - Nombre
  - Localidad
  - Municipio
  - Provincia
  - Dirección (opcional para visualización)
  - Código Postal

### Motor de Procesamiento
- **Integración con LLM**:
  - Permitir configuración para usar modelos locales o APIs externas.
  - Crear un archivo de configuración simple para especificar:
    - Tipo de modelo (local/API)
    - Credenciales API (si es necesario)
    - Parámetros de procesamiento

- **Algoritmo de Proximidad**:
  - Utilizar el LLM para determinar proximidades relativas entre localidades.
  - Implementar la lógica de ordenamiento basada en prioridades:
    1. Comenzar priorizando localidades más cercanas a la primera ciudad de preferencia.
    2. Cuando una localidad es significativamente más cercana a la segunda ciudad que a la primera, comenzar a listar basándose en la segunda ciudad.
    3. Seguir este patrón con todas las ciudades de preferencia.
  - Garantizar que cada localidad aparezca solo una vez en la lista final.
  - Incluir las propias ciudades de preferencia en la lista resultante.

## Implementación Técnica

### Estructura del Proyecto
```
/app
  /src
    - main.py (punto de entrada)
    - ui.py (interfaz de usuario simple)
    - processor.py (procesamiento de datos)
    - llm_connector.py (conexión con modelos LLM)
  /data
    /Almeria
      - institutos.csv
      - colegios.csv
    /Granada
      - institutos.csv
      - colegios.csv
    /...
  /config
    - settings.yaml (configuración de modelos y preferencias)
  /saved_configs
    - (archivos de configuraciones guardadas por el usuario)
  - README.md (documentación con instrucciones de instalación y uso)
  - requirements.txt (dependencias de Python)
```

### Tecnologías Recomendadas
- **Backend**: Python con Flask para un servidor ligero o Streamlit para una solución más rápida.
- **Frontend**: HTML/CSS/JS básico o interfaz generada por Streamlit.
- **Procesamiento de CSV**: Pandas para manipulación de datos.
- **LLM**: Configuración flexible para usar OpenAI API, modelos locales como LlamaCpp, o cualquier otro modelo compatible.

### Flujo de Trabajo
1. El usuario selecciona provincias, tipo de centro (IES/CEIP) y añade sus ciudades de preferencia en orden.
2. Al pulsar "Calcular", la aplicación lee los CSV correspondientes.
3. Se construye un prompt específico para el LLM incluyendo:
   - Los datos de los centros de las provincias seleccionadas
   - Las ciudades de preferencia en orden
   - La instrucción de ordenamiento
4. El LLM procesa la solicitud y genera una lista ordenada.
5. La aplicación muestra los resultados de forma clara y legible.
6. Opcionalmente, el usuario puede guardar su configuración para uso futuro.

## Prompt específico para el LLM

```
Estoy procesando datos de centros educativos [TIPO_CENTRO] públicos en las provincias de [PROVINCIAS_SELECCIONADAS] de Andalucía. 

Tengo la siguiente información sobre cada centro:
[EXTRACTO_EJEMPLO_CSV]

Necesito una lista numerada y única de todas las localidades con [TIPO_CENTRO] públicos, ordenadas según su proximidad geográfica a mis localidades de preferencia, que en orden descendente de prioridad son:

1. [CIUDAD_1] (máxima prioridad)
2. [CIUDAD_2]
...
N. [CIUDAD_N] (mínima prioridad)

El ordenamiento debe funcionar así:
- Inicialmente, priorizar localidades cercanas a [CIUDAD_1].
- Cuando una localidad es significativamente más cercana a una ciudad de menor prioridad que a [CIUDAD_1], ordenarla según esa otra ciudad.
- Cada localidad debe aparecer solo una vez en la posición más favorable según este sistema.
- Incluir también las propias ciudades de preferencia en la lista resultante, en la posición que les corresponda.

Genera una lista numerada con el formato: "Número. Localidad (Provincia)"

Adicionalmente, si hay alguna localidad pequeña cercana a mis preferencias que NO tenga [TIPO_CENTRO] públicos, menciónala brevemente al final.
```

## Requisitos Adicionales

### Documentación
- **README.md completo** con:
  - Descripción del proyecto
  - Instrucciones de instalación y requisitos
  - Guía de configuración del LLM (local o API)
  - Ejemplos de uso
  - Notas sobre obtención y formato de los CSV

### Gestión de Errores
- Validación de datos de entrada
- Manejo de errores en la conexión con el LLM
- Mensajes de error claros y descriptivos

### Consideraciones de Usabilidad
- Interfaz minimalista pero funcional
- Tiempos de respuesta razonables
- Opción para exportar resultados (TXT, CSV)

### Extensibilidad
- Código modular que permita añadir fácilmente nuevas funcionalidades
- Comentarios claros en el código para facilitar modificaciones futuras

### Añade un gitignore