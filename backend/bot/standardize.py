import pandas as pd
import os
import glob

def unificar_datos_estacion(ruta_carpeta_estacion):
    """
    Lee todos los CSVs de una carpeta, detecta separadores automáticamente,
    alinea fechas y genera un único DataFrame maestro.
    """
    archivos_csv = glob.glob(os.path.join(ruta_carpeta_estacion, "*.csv"))
    
    if not archivos_csv:
        print(f"⚠️  Carpeta vacía o sin CSVs: {ruta_carpeta_estacion}")
        return None

    print(f"🔄 Unificando {len(archivos_csv)} archivos en: {os.path.basename(ruta_carpeta_estacion)}")

    dataframes_list = []
    fechas_minimas = []
    fechas_maximas = []

    for archivo in archivos_csv:
        nombre_parametro = os.path.basename(archivo).replace(".csv", "")
        
        try:
            # 1. INTENTO DE LECTURA ROBUSTA (Detectar separador)
            # Primero probamos con punto y coma (Estándar Colombia/SISAIRE)
            try:
                df = pd.read_csv(archivo, sep=';', decimal=',')
                if len(df.columns) < 2: # Si leyó todo en 1 columna, el separador falló
                    raise ValueError("Probablemente no es punto y coma")
            except:
                # Si falla, probamos con coma (Estándar Internacional)
                df = pd.read_csv(archivo, sep=',', decimal='.')

            # 2. LIMPIEZA DE NOMBRES DE COLUMNAS
            # Quitamos espacios y pasamos a minúsculas para buscar mejor
            df.columns = [c.strip().lower() for c in df.columns]
            
            # --- DETECCIÓN DE COLUMNAS ---
            
            # A. Buscar columna FECHA
            try:
                # Buscamos 'fecha', 'date' o 'tiempo'
                col_fecha = [c for c in df.columns if 'fecha' in c or 'date' in c or 'time' in c][0]
            except IndexError:
                print(f"   ⚠️  Saltando {nombre_parametro}: No encontré columna 'Fecha'. Columnas vistas: {df.columns.tolist()}")
                continue
            
            # B. Buscar columna VALOR
            # Prioridad: Nombre del parámetro > valor > concentracion
            posibles_nombres = [nombre_parametro.lower(), 'valor', 'value', 'concentracion', 'registros', 'mean']
            
            try:
                col_valor = [c for c in df.columns if any(k in c for k in posibles_nombres)][0]
            except IndexError:
                print(f"   ⚠️  Saltando {nombre_parametro}: No encontré columna de Valor. Columnas vistas: {df.columns.tolist()}")
                continue

            # ------------------------------

            # 3. PROCESAMIENTO
            # Convertir a datetime (usando dayfirst=True por formato LATAM dd/mm/yyyy)
            df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
            
            # Eliminar filas donde la fecha no se pudo leer (NaT)
            df = df.dropna(subset=[col_fecha])

            df = df.set_index(col_fecha)
            
            # Eliminar duplicados de índice
            df = df[~df.index.duplicated(keep='first')]
            
            # Convertir columna valor a numérico (a veces vienen como texto con 'ND' o vacíos)
            # errors='coerce' transformará textos raros en NaN
            df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce')

            # Renombrar y guardar
            serie = df[[col_valor]].rename(columns={col_valor: nombre_parametro})
            
            dataframes_list.append(serie)
            fechas_minimas.append(serie.index.min())
            fechas_maximas.append(serie.index.max())
            
            # print(f"   ✅ Cargado: {nombre_parametro} ({len(serie)} reg)")

        except Exception as e:
            print(f"   ❌ Error crítico leyendo {nombre_parametro}: {e}")

    # CORRECCIÓN DEL TYPO AQUÍ ABAJO (Antes decía dates_minimas)
    if not dataframes_list or not fechas_minimas: 
        print(f"   ⚠️ No se pudieron extraer datos válidos de {os.path.basename(ruta_carpeta_estacion)}")
        return None

    # 4. CREAR CALENDARIO MAESTRO
    # Filtramos NaT por si acaso
    fechas_minimas = [f for f in fechas_minimas if pd.notnull(f)]
    fechas_maximas = [f for f in fechas_maximas if pd.notnull(f)]
    
    if not fechas_minimas: return None

    fecha_inicio = min(fechas_minimas)
    fecha_fin = max(fechas_maximas)
    
    print(f"   📅 Rango: {fecha_inicio.date()} a {fecha_fin.date()}")
    
    indice_maestro = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    df_final = pd.DataFrame(index=indice_maestro)
    df_final.index.name = 'Fecha'

    # 5. UNIR TODO
    for serie in dataframes_list:
        df_final = df_final.join(serie, how='left')

    return df_final