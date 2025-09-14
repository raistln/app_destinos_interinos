# 🗄️ Configuración de Supabase para App Destinos Interinos

Esta guía te ayudará a configurar Supabase PostgreSQL para tu aplicación.

## 📋 Pasos de Configuración

### 1. Crear Proyecto en Supabase

1. Ve a [supabase.com](https://supabase.com)
2. Crea una cuenta o inicia sesión
3. Crea un nuevo proyecto
4. Anota la **URL del proyecto** y la **clave anon/public**

### 2. Crear las Tablas

1. Ve al **SQL Editor** en tu dashboard de Supabase
2. Ejecuta el siguiente script SQL:

```sql
-- Tabla para almacenar coordenadas de ciudades
CREATE TABLE IF NOT EXISTS ciudades (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    provincia VARCHAR(100) NOT NULL,
    latitud DECIMAL(10, 8) NOT NULL,
    longitud DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(nombre, provincia)
);

-- Tabla para caché de distancias entre ciudades
CREATE TABLE IF NOT EXISTS distancias (
    id SERIAL PRIMARY KEY,
    ciudad1 VARCHAR(255) NOT NULL,
    ciudad2 VARCHAR(255) NOT NULL,
    distancia DECIMAL(8, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ciudad1, ciudad2)
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_ciudades_nombre ON ciudades(nombre);
CREATE INDEX IF NOT EXISTS idx_ciudades_provincia ON ciudades(provincia);
CREATE INDEX IF NOT EXISTS idx_distancias_ciudades ON distancias(ciudad1, ciudad2);

-- Habilitar Row Level Security (RLS)
ALTER TABLE ciudades ENABLE ROW LEVEL SECURITY;
ALTER TABLE distancias ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso (permitir operaciones a todos)
CREATE POLICY "Allow all operations on ciudades" ON ciudades
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on distancias" ON distancias
    FOR ALL USING (true);
```

### 3. Configurar Variables de Entorno

#### Para desarrollo local (.env):
```env
SUPABASE_URL=https://tu-proyecto-id.supabase.co
SUPABASE_KEY=tu-clave-anon-aqui
MISTRAL_API_KEY=tu-clave-mistral-aqui
```

#### Para Streamlit Cloud (secrets):
En la configuración de tu app en Streamlit Cloud, añade:
```toml
SUPABASE_URL = "https://tu-proyecto-id.supabase.co"
SUPABASE_KEY = "tu-clave-anon-aqui"
MISTRAL_API_KEY = "tu-clave-mistral-aqui"
```

### 4. Obtener las Credenciales

1. **URL del proyecto**: En Settings → API → Project URL
2. **Clave anon**: En Settings → API → Project API keys → anon/public

## 🔧 Configuración de Seguridad

### Row Level Security (RLS)
Las tablas tienen RLS habilitado con políticas que permiten:
- ✅ Lectura pública (para consultar coordenadas y distancias)
- ✅ Escritura pública (para guardar nuevas coordenadas y distancias)

### Políticas Recomendadas para Producción
Si quieres mayor seguridad, puedes modificar las políticas:

```sql
-- Política más restrictiva (solo lectura pública, escritura autenticada)
DROP POLICY "Allow all operations on ciudades" ON ciudades;
DROP POLICY "Allow all operations on distancias" ON distancias;

-- Permitir lectura a todos
CREATE POLICY "Allow read on ciudades" ON ciudades
    FOR SELECT USING (true);

CREATE POLICY "Allow read on distancias" ON distancias
    FOR SELECT USING (true);

-- Permitir escritura solo a usuarios autenticados
CREATE POLICY "Allow insert on ciudades" ON ciudades
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Allow insert on distancias" ON distancias
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

## 📊 Monitoreo

### Consultas Útiles

**Ver estadísticas de la base de datos:**
```sql
SELECT 
    'ciudades' as tabla,
    COUNT(*) as registros
FROM ciudades
UNION ALL
SELECT 
    'distancias' as tabla,
    COUNT(*) as registros
FROM distancias;
```

**Ver ciudades más consultadas:**
```sql
SELECT 
    ciudad1,
    COUNT(*) as veces_consultada
FROM distancias
GROUP BY ciudad1
ORDER BY veces_consultada DESC
LIMIT 10;
```

## 🚀 Ventajas de Supabase

- ✅ **Base de datos persistente** (no se pierde al reiniciar)
- ✅ **Compartida entre usuarios** (caché global)
- ✅ **Escalable** (PostgreSQL en la nube)
- ✅ **Gratuita** hasta 500MB y 2GB de transferencia
- ✅ **Tiempo real** (opcional para futuras funcionalidades)
- ✅ **Dashboard web** para monitoreo

## 🔍 Troubleshooting

### Error de conexión
- Verifica que las URLs y claves sean correctas
- Asegúrate de que las políticas RLS permitan las operaciones
- Revisa los logs en Supabase Dashboard → Logs

### Tablas no encontradas
- Ejecuta el script SQL completo en el SQL Editor
- Verifica que las tablas aparezcan en Table Editor

### Rendimiento lento
- Los índices están creados automáticamente
- Considera añadir más índices si necesario
- Monitorea las consultas en el dashboard
