from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
import pandas as pd
import os
import time
import shutil






class SisaireBot:
    def __init__(self):
        if os.path.exists('stations_db.csv'):
            self.stations_db = pd.read_csv('stations_db.csv')
        else:
            self.stations_db = pd.DataFrame(columns=['municipio','nombre_estacion', 'latitud', 'longitud','parametro'])
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../AireAburra/backend/bot
        self.project_root = os.path.dirname(os.path.dirname(current_dir)) # .../AireAburra
        self.new_data = []

    def init_browser(self,route):
        edge_options = webdriver.EdgeOptions()
        edge_options.add_experimental_option(name='detach', value=True)
        self.route=route
        self.download_temp_dir = os.path.join(self.project_root,'backend','bot','temp')
        prefs ={
            "download.default_directory":self.download_temp_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally":True
        }
        edge_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Edge(options=edge_options)
        self.driver.get(route) #? Ir a webpage SISAIRE
        time.sleep(5)


    def change_paginating(self):
        dropdown_menu = WebDriverWait(self.driver,10).until(
            EC.visibility_of_element_located((By.ID, 'j_idt54:j_idt56:calTablaResultados:j_id2'))
        )
        Select(dropdown_menu).select_by_value("100")
        print("Solicitando 100 registros, esperando actualización de tabla...")

        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, "//tbody[contains(@id, 'calTablaResultados_data')]//tr")) > 10
            )
            print("¡Tabla actualizada correctamente!")
        except:
            print("Advertencia: No se detectaron más de 10 filas (o se agotó el tiempo de espera).")

    def update_stationts_db(self):
        """
        Esta función escanea la tabla para obtener los registros disponibles, itera en cada uno de ellos 
        para obtener municipio, nombre estación, latitud, longitud, parámetro que evalúa y los acumula en un
        array
        """
        max_retries = 3
        attempts = 0
        
        while attempts < max_retries:
            try:
                
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//tbody[contains(@id, 'calTablaResultados_data')]//tr"))
                )
                
                
                rows = self.driver.find_elements(By.XPATH, "//tbody[contains(@id, 'calTablaResultados_data')]//tr")
                
                
                if len(rows) < 2: 
                    
                    print("Tabla parece vacía o cargando, esperando...")
                    time.sleep(1)
                    attempts += 1
                    continue


                print(f"Intento {attempts+1}: Procesando {len(rows)} filas...")

                # 3. Iterar filas
                for row in rows:

                    mun_raw = row.find_element(By.XPATH, ".//td[1]").get_attribute("textContent")
                    municipio = mun_raw.replace("Municipio", "").strip()
                    name = row.find_element(By.XPATH, ".//td[2]//a").text.strip()
                    lat = row.find_element(By.XPATH, ".//td[4]").get_attribute("textContent").replace("Latitud", "").strip()
                    lon = row.find_element(By.XPATH, ".//td[5]").get_attribute("textContent").replace("Longitud", "").strip()
                    parametro = row.find_element(By.XPATH, ".//td[6]").get_attribute('textContent').replace('Variables que evalúa', "").strip()
                    
                    self.new_data.append({
                        "municipio":municipio,
                        "nombre_estacion": name,
                        "latitud": float(lat),
                        "longitud": float(lon),
                        "parametro":parametro
                    })

           
                if self.new_data:         
                    df_nuevo = pd.DataFrame(self.new_data)                  
                    if self.stations_db is not None and not self.stations_db.empty:
                        self.stations_db = pd.concat([self.stations_db, df_nuevo], ignore_index=True)
                        self.stations_db = self.stations_db.drop_duplicates(subset=['nombre_estacion', 'parametro'], keep='last')
                    else:
                        self.stations_db = df_nuevo
                        self.stations_db = self.stations_db.drop_duplicates(subset=['nombre_estacion', 'parametro'], keep='last')
                    print(f"¡Éxito! Base de datos actualizada. Total acumulado: {len(self.stations_db)}")
                    self.stations_db.to_csv('stations_db.csv', index=False, encoding='utf-8-sig')
                    return # Salimos de la función exitosamente
                else:
                    print("No se extrajeron datos, reintentando...")
                    attempts += 1

            except Exception as e:
                # Si es StaleElementReferenceException, caerá aquí
                if "stale element reference" in str(e):
                    print("⚠️ Detectado cambio en el DOM (Stale Element). La tabla se refrescó mientras leíamos.")
                    print("Reiniciando lectura de esta página...")
                else:
                    print(f"Error no crítico: {e}")
                
                attempts += 1
                # Pequeña pausa para dejar que la tabla se asiente
                time.sleep(2) 
        
        print("❌ Error: No se pudo leer la tabla después de varios intentos.")

    def scan_all_stations(self):
        """ Esta funcion busca en todas las filas de la tabla de SISAIRE y crea un csv que recopila el contenido disponible en la página """
        self.change_paginating()
        actual_page = 1

        while True:
            print(f"----- Procesando página {actual_page} -----")
            self.update_stationts_db()

            try:
                next_btn = self.driver.find_element(By.CLASS_NAME, 'ui-paginator-next')
                if "ui-state-disabled" in next_btn.get_attribute("class"):
                    print("Botón 'Siguiente' deshabilitado. Hemos terminado el escaneo.")
                    time.sleep(2)
                    self.driver.quit()
                    break
                
                old_table = self.driver.find_element(By.XPATH, "//tbody[contains(@id, 'calTablaResultados_data')]")
                next_btn.click()
                print("Cambiando de página ...")

                WebDriverWait(self.driver,15).until(
                    EC.presence_of_element_located((By.XPATH, "//tbody[contains(@id, 'calTablaResultados_data')]//tr"))
                )
                actual_page +=1
            except Exception as e:
                print(f"Error o fin de paginación detectado: {e}")
                break
    def buscar_y_seleccionar_estacion(self,nombre_estacion):
        wait = WebDriverWait(self.driver, 10)
        print(f"   🔎 Buscando: {nombre_estacion}")
        try:
            dropdown_trigger = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "label.ui-selectcheckboxmenu-label, .ui-selectcheckboxmenu-trigger")
            ))
            dropdown_trigger.click()

        except Exception as e:
            print(f"   ⚠️ No se pudo entrar a la estación {nombre_estacion}: {e}")
            try:
                self.driver.refresh()
            except: pass
            return False 
        time.sleep(1)
        try:
            filtro_interno = wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.ui-selectcheckboxmenu-filter-container input")
            ))
            filtro_interno.clear()
            filtro_interno.send_keys(nombre_estacion)
            time.sleep(2)
            xpath_checkbox = f"(//li[contains(@class, 'ui-selectcheckboxmenu-item') and contains(., '{nombre_estacion.upper()}')])[1]//div[contains(@class, 'ui-chkbox-box')]"
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_checkbox)))
            if not checkbox:
                return False
            checkbox.click()
            print("   ✅ Checkbox marcado.")
            # Buscamos la 'X' en la esquina superior derecha del panel
            boton_cerrar = self.driver.find_element(By.CSS_SELECTOR, "a.ui-selectcheckboxmenu-close")
            boton_cerrar.click()
            time.sleep(1)
            return True

        except Exception as e:
            print(f"   ⚠️ Error interactuando con el panel: {e}")
            return False


        
    
    def descargar_datos_estacion(self):
        grupos = self.stations_db.groupby('nombre_estacion')
        for nombre_estacion, datos_estacion in grupos:
            print(f"📍 Entrando a la estación: {nombre_estacion}")
            new_folder_path = os.path.join(self.project_root, "data", "raw",nombre_estacion)
            os.makedirs(new_folder_path, exist_ok=True) #¿Crear carpeta
            if self.buscar_y_seleccionar_estacion(nombre_estacion): #¿ Seleccionar estación en SISAIRE
                for index,row in datos_estacion.iterrows():
                    contaminante = row['parametro']
                    nombre_archivo = f"{contaminante}.csv".replace(" ","_")
                    ruta_final = os.path.join(new_folder_path, nombre_archivo)
                    
                    max_intentos = 3
                    intento = 0
                    descarga_exitosa = False
                    while intento < max_intentos and not descarga_exitosa:
                        try:
                            self.descargar_contaminante(contaminante, ruta_final)
                            descarga_exitosa = True
                        except Exception as e:
                            intento+=1
                            print(f"⚠️ Error descargando {contaminante} (Intento {intento}/{max_intentos}): {e}")
                            if intento < max_intentos:
                                print("🔄 INICIANDO PROTOCOLO DE RECUPERACIÓN")
                                try:
                                    self.driver.get(self.route)
                                    time.sleep(3)
                                except: pass
                                if self.buscar_y_seleccionar_estacion(nombre_estacion):
                                    print("🔙 Estación recuperada. Reintentando contaminante...")
                                else:
                                    print(" ❌ No se pudo recuperar la estación. Abortando este contaminante.")
                                    break # Rompe el while y pasa al siguiente contaminante (o estación)
                    
                print("   🔙 Saliendo de la estación (Limpiando para la siguiente)...")
                self.driver.get(self.route)
            else:
                print("⚠️ No se encontró la estación")

    def descargar_contaminante(self,contaminante,ruta_destino):
        time.sleep(3)
        wait = WebDriverWait(self.driver, 10)
        print(f"➡️ Seleccionando contaminante: {contaminante}")
        wait.until(EC.element_to_be_clickable(
        (By.ID, "filtroForm:contaminanteSel")
        )).click()

        opcion = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f'//*[@id="filtroForm:contaminanteSel_filter"]')
        ))
        opcion.click()
        opcion.clear()
        opcion.send_keys(contaminante)

        time.sleep(2)
        primer_resultado = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "#filtroForm\\:contaminanteSel_items li:not([style*='none'])")
        ))
        primer_resultado.click()
        time.sleep(2)
        btn_fecha_inicio = wait.until(EC.element_to_be_clickable(
            (By.ID,'filtroForm:labelFIniLimite')
        ))
        btn_fecha_inicio.click()
        btn_fecha_fin = wait.until(EC.element_to_be_clickable(
            (By.ID,'filtroForm:labelFFinLimite')
        ))
        btn_fecha_fin.click()
        time.sleep(2)
        opcion_deseada = "Día (promedio)"


        trigger_xpath = "//div[@id='filtroForm:tipoSel']//div[contains(@class, 'ui-selectonemenu-trigger')]"
        trigger = wait.until(EC.element_to_be_clickable((By.XPATH, trigger_xpath)))
        trigger.click()
        opcion_xpath = f"//li[text()='{opcion_deseada}']"
        opcion = wait.until(EC.element_to_be_clickable((By.XPATH, opcion_xpath)))
        
        opcion.click()
        time.sleep(3)

        btn_consultar= wait.until(EC.element_to_be_clickable(
            (By.ID,'filtroForm:btnConsultar')
        ))
        btn_consultar.click()
        
        for f in os.listdir(self.download_temp_dir):
            if f.endswith('.csv'):
                os.remove(os.path.join(self.download_temp_dir,f))
        
        time.sleep(5)
        descargar_csv = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="j_idt91:j_idt93:j_idt94:tablaCons"]/div[1]/div/h3/a[2]')
        ))
        descargar_csv.click()

        tiempo_espera = 0
        max_timeout = 3

        while tiempo_espera<max_timeout:
            files = [f for f in os.listdir(self.download_temp_dir) if f.endswith('.csv')]

            if files:
                archivo_descargadp = os.path.join(self.download_temp_dir, files[0])

                shutil.move(archivo_descargadp,ruta_destino)
                print(f"      💾 Guardado: {contaminante} -> {ruta_destino}")
                return
            time.sleep(1)
            tiempo_espera +=1
        raise Exception(f"Timeout: No se pudo encontrar el archivo CSV para {contaminante} después de {max_timeout} segundos.")
            



        
        