-- Habilitar la extensión geoespacial PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. TABLA MAESTRA DE ESTACIONES
CREATE TABLE estaciones (
    id SERIAL PRIMARY KEY,
    nombre_estacion VARCHAR(150) UNIQUE NOT NULL,
    municipio VARCHAR(100),
    latitud FLOAT,
    longitud FLOAT,
    -- Columna geom (Punto) para PostGIS
    geom GEOMETRY(Point, 4326) 
);

-- 2. TABLA DE MEDICIONES
CREATE TABLE mediciones (
    id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Key: Cada medición pertenece a una estación
    estacion_id INTEGER REFERENCES estaciones(id) ON DELETE CASCADE,
    
    fecha DATE NOT NULL,
    
    -- Contaminantes (FLOAT permite valores NULL si la estación no mide)
    pm25 FLOAT,
    pm10 FLOAT,
    no FLOAT,
    no2 FLOAT,
    nox FLOAT,
    so2 FLOAT,
    co FLOAT,
    o3 FLOAT,
    
    -- Variables Meteorológicas
    haire2 FLOAT,
    haire10 FLOAT,
    taire2 FLOAT,
    taire10 FLOAT,
    tmpr_air_10cm FLOAT,
    p FLOAT,
    rglobal FLOAT,
    vviento FLOAT,
    dviento FLOAT,
    
    -- Índice único: Garantiza que no haya duplicados de la misma medición en la misma fecha
    UNIQUE(estacion_id, fecha)
);

-- 3. TABLA DE EVENTOS
CREATE TABLE eventos_criticos (
    id SERIAL PRIMARY KEY,
    nombre_evento VARCHAR(255) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estacion_referencia_id INTEGER REFERENCES estaciones(id) ON DELETE SET NULL,
    causa_probable VARCHAR(255),
    noticia_titulo VARCHAR(500),
    noticia_url TEXT,
    noticia_fecha_publicacion DATE
);

-- 4. Índices para acelerar las consultas
-- Índice GIST es esencial para consultas espaciales rápidas
CREATE INDEX idx_estaciones_geom ON estaciones USING GIST (geom);

-- Índice compuesto para búsquedas por estación y rango de fechas
CREATE INDEX idx_mediciones_estacion_fecha ON mediciones (estacion_id, fecha);