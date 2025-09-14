-- Esquema de base de datos para Supabase PostgreSQL
-- Ejecutar estos comandos en el SQL Editor de Supabase

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

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at en ciudades
CREATE TRIGGER update_ciudades_updated_at 
    BEFORE UPDATE ON ciudades 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Habilitar Row Level Security (RLS) para seguridad
ALTER TABLE ciudades ENABLE ROW LEVEL SECURITY;
ALTER TABLE distancias ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso (permitir lectura y escritura a usuarios autenticados y anónimos)
CREATE POLICY "Allow all operations on ciudades" ON ciudades
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on distancias" ON distancias
    FOR ALL USING (true);

-- Comentarios para documentación
COMMENT ON TABLE ciudades IS 'Almacena coordenadas de ciudades para geocodificación';
COMMENT ON TABLE distancias IS 'Caché de distancias calculadas entre ciudades';
COMMENT ON COLUMN ciudades.latitud IS 'Latitud en grados decimales';
COMMENT ON COLUMN ciudades.longitud IS 'Longitud en grados decimales';
COMMENT ON COLUMN distancias.distancia IS 'Distancia en kilómetros';
