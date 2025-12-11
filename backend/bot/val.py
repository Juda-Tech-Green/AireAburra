from sisaire_bot import SisaireBot
from scripts.standardize import unificar_datos_estacion
from scripts.clean_data import limpiar_serie
from time import sleep
import pandas as pd
import os

ruta_1 = 'http://sisaire.ideam.gov.co/ideam-sisaire-web/calidad_aire_estaciones.xhtml?tipo=svca&id=37'
ruta_2 = 'http://sisaire.ideam.gov.co/ideam-sisaire-web/consultas.xhtml'

#¿ Asignar bot a SISAIRE-BOT
#val_bot = SisaireBot()

#! Actualizar base de datos aproximadamente 5 min
#val_bot.init_browser(ruta_1)
#val_bot.scan_all_stations()

#! Descargar datos de SISAIRE a partir de base de datos creada aproximadamente 3-4 h

#val_bot.init_browser(ruta_2)
#val_bot.descargar_datos_estacion()
  
#? Estandarizar datos
def estandarizar_datos():
    ruta_raw = "../data/raw"
    ruta_processed = "../data/processed"
    carpetas_vacias = []
    # Listar todas las carpetas de estaciones
    estaciones = [f for f in os.listdir(ruta_raw) if os.path.isdir(os.path.join(ruta_raw, f))]
    for estacion in estaciones:
        ruta_estacion = os.path.join(ruta_raw, estacion)

        df_consolidado = unificar_datos_estacion(ruta_estacion)
        if df_consolidado is not None:
            ruta_salida = os.path.join(ruta_processed, f"{estacion}_consolidado.csv")
            df_consolidado.to_csv(ruta_salida, index=True)
            print(f"💾 Guardado consolidado en: {ruta_salida}\n")
        else:
            carpetas_vacias.append(ruta_estacion.split(sep='raw')[1])
            
    print(f" 📂 Las siguientes carpetas no tienen archivos: \n {carpetas_vacias}")
#! Estandarizar datos
estandarizar_datos()