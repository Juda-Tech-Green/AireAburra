import pandas as pd
import os
import glob
import psycopg2.extras as extras
from psycopg2 import sql
import sys

# Ajuste de rutas para importar db_connection desde la carpeta hermana
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_connection import get_db_connection

# Mapeo: { "nombre_columna_pandas": "nombre_columna_sql" }
COLUMNAS_SQL = {
    'pm2.5': 'pm25', 'pm10': 'pm10', 
    'no': 'no', 'no2': 'no2', 'nox': 'nox', 
    'so2': 'so2', 'co': 'co', 'o3': 'o3', 
    'haire2': 'haire2', 'haire10': 'haire10', 
    'taire2': 'taire2', 'taire10': 'taire10', 
    'tmpr air 10cm': 'tmpr_air_10cm',
    'p': 'p', 'rglobal': 'rglobal', 
    'vviento': 'vviento', 'dviento': 'dviento'
}

def limpiar_nombre(nombre):
    """
    Replica la limpieza que usa el bot para generar nombres de carpeta/archivo.
    Quita tildes, espacios y caracteres raros.
    """
    return "".join(x for x in nombre if x.isalnum() or x in " _-").strip().replace(" ", "_")

def load_estaciones(csv_path, conn):
    """
    1. Lee stations_db.csv.
    2. Elimina duplicados (porque hay una fila por parámetro).
    3. Inserta estaciones únicas en la DB.
    4. Devuelve un diccionario inteligente para buscar IDs.
    """
    if not os.path.exists(csv_path):
        print(f"❌ Error: No se encuentra {csv_path}")
        return {}

    print("🔄 Procesando maestro de estaciones...")
    # Leemos el CSV
    df = pd.read_csv(csv_path)
    # Normalizamos encabezados
    df.columns = [c.strip().lower() for c in df.columns]

    # --- PASO CLAVE: ELIMINAR DUPLICADOS ---
    # Nos quedamos con la primera aparición de cada nombre de estación.
    # Esto resuelve tu duda: ignoramos las filas repetidas por parámetro.
    df_unicas = df.drop_duplicates(subset=['nombre_estacion']).copy()
    
    print(f"   📋 Estaciones únicas detectadas: {len(df_unicas)}")

    cursor = conn.cursor()
    
    # Este diccionario nos permitirá encontrar el ID tanto si buscamos
    # "CASA DE JUSTICIA" como "CASA_DE_JUSTICIA"
    mapa_ids = {} 

    insertados = 0
    for _, row in df_unicas.iterrows():
        try:
            nombre_real = row['nombre_estacion']
            lat = row['latitud']
            lon = row['longitud']
            municipio = row.get('municipio', 'Desconocido') # .get por si la columna falta

            # Inserción con "Upsert" (Si existe, actualiza coordenadas)
            query = sql.SQL("""
                INSERT INTO estaciones (nombre_estacion, municipio, latitud, longitud, geom)
                VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                ON CONFLICT (nombre_estacion) 
                DO UPDATE SET latitud=EXCLUDED.latitud, longitud=EXCLUDED.longitud
                RETURNING id;
            """)
            
            cursor.execute(query, (nombre_real, municipio, lat, lon, lon, lat))
            estacion_id = cursor.fetchone()[0]
            
            # --- ESTRATEGIA DOBLE LLAVE ---
            # Guardamos el nombre original (tal cual viene en el CSV)
            mapa_ids[nombre_real] = estacion_id
            
            # Guardamos también la versión "limpia" (con guiones bajos)
            # Esto asegura que encontremos el ID sin importar cómo se llame el archivo
            nombre_limpio = limpiar_nombre(nombre_real)
            mapa_ids[nombre_limpio] = estacion_id
            
            insertados += 1

        except Exception as e:
            print(f"   ❌ Error con estación {nombre_real}: {e}")
            conn.rollback()

    conn.commit()
    cursor.close()
    print(f"✅ Estaciones sincronizadas: {insertados}")
    return mapa_ids

def load_mediciones(ruta_processed, mapa_ids, conn):
    """
    Lee los CSV consolidados e inserta los datos.
    """
    archivos = glob.glob(os.path.join(ruta_processed, "*_consolidado.csv"))
    
    if not archivos:
        print("⚠️ No hay archivos consolidados para cargar.")
        return

    print(f"\n🔄 Cargando mediciones de {len(archivos)} archivos...")
    
    cursor = conn.cursor()
    total_filas = 0

    for archivo in archivos:
        # Extraer nombre base: "CASA_DE_JUSTICIA_consolidado.csv"
        basename = os.path.basename(archivo)
        # Quitamos el sufijo para obtener el nombre de la estación
        nombre_clave = basename.replace('_consolidado.csv', '')
        
        # Buscamos el ID en nuestro mapa (funciona con nombre limpio u original)
        estacion_id = mapa_ids.get(nombre_clave)
        
        if not estacion_id:
            print(f"   ⚠️ ID no encontrado para: '{nombre_clave}'. (¿Está en stations_db.csv?)")
            continue

        try:
            # Leemos el CSV consolidado
            # Asumimos que la primera columna es la Fecha (índice)
            df = pd.read_csv(archivo, index_col=0)
            
            # Convertir índice a datetime si no lo es
            df.index = pd.to_datetime(df.index)
            
            # Normalizar columnas del CSV
            df.columns = [c.strip().lower() for c in df.columns]

            # Filtrar solo columnas que existan en nuestro mapeo SQL
            cols_utiles = [c for c in df.columns if c in COLUMNAS_SQL]
            
            if not cols_utiles:
                print(f"   ⚠️ {nombre_clave}: Sin columnas válidas para DB. Saltando.")
                continue

            # Construir Query Dinámica
            # Ejemplo: INSERT INTO mediciones (estacion_id, fecha, pm25, no2) VALUES ...
            cols_db = ['estacion_id', 'fecha'] + [COLUMNAS_SQL[c] for c in cols_utiles]
            cols_str = ', '.join(cols_db)
            placeholders = ', '.join(['%s'] * len(cols_db))
            
            query = f"INSERT INTO mediciones ({cols_str}) VALUES ({placeholders}) ON CONFLICT (estacion_id, fecha) DO NOTHING"

            # Preparar datos para batch
            datos_batch = []
            for fecha, row in df.iterrows():
                # Iniciamos tupla con ID y Fecha
                registro = [estacion_id, fecha.date()]
                
                # Añadimos valores (convirtiendo NaN a None)
                for col in cols_utiles:
                    val = row[col]
                    if pd.isna(val):
                        val = None
                    else:
                        val = float(val)
                    registro.append(val)
                
                datos_batch.append(tuple(registro))

            # Inserción masiva (rápida)
            if datos_batch:
                extras.execute_batch(cursor, query, datos_batch, page_size=5000)
                conn.commit() # Commit por archivo para no perder todo si uno falla
                total_filas += len(datos_batch)
                print(f"   ✅ {nombre_clave}: {len(datos_batch)} días cargados.")

        except Exception as e:
            print(f"   ❌ Error crítico en archivo {basename}: {e}")
            conn.rollback()

    cursor.close()
    print(f"\n🚀 Carga finalizada. Total registros históricos: {total_filas}")

def main():
    # Rutas relativas
    BASE_DIR = os.path.dirname(__file__)
    
    # Ajusta esta ruta a donde tengas tu stations_db.csv real
    # Opción 1: En carpeta bot
    PATH_STATIONS = os.path.join(BASE_DIR, '../', 'bot', 'stations_db.csv')
    
    # Opción 2: En data/raw (descomenta si prefieres esta)
    # PATH_STATIONS = os.path.join(BASE_DIR, '..', '..', 'data', 'raw', 'stations_db.csv')

    PATH_PROCESSED = os.path.join(BASE_DIR, '../', 'data', 'processed')

    conn = get_db_connection()
    if not conn:
        return

    # 1. Cargar Estaciones Únicas
    ids = load_estaciones(PATH_STATIONS, conn)
    
    # 2. Cargar Datos Históricos
    if ids:
        load_mediciones(PATH_PROCESSED, ids, conn)
    
    conn.close()

if __name__ == "__main__":
    main()