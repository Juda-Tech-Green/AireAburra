import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

# Cargar variables del archivo .env al entorno
load_dotenv()

def get_db_connection():
    """
    Establece y devuelve una conexión activa a la base de datos PostgreSQL.
    Las credenciales son cargadas desde las variables de entorno (o el archivo .env).
    Returns:
        psycopg2.connection: Un objeto de conexión a la base de datos.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        print("✅ Conexión a la base de datos establecida correctamente.")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error al conectar con la base de datos:")
        print(f"  {e}")
        
        return None


def execute_schema_script(script_path):
    """
    Ejecuta un script SQL completo (para crear tablas) en la base de datos.
    """
    conn = get_db_connection()
    if conn is None:
        print("No se puede ejecutar el script sin conexión a la DB.")
        return False
        
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        cursor = conn.cursor()
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()
        print(f"✅ Script SQL '{os.path.basename(script_path)}' ejecutado correctamente.")
        return True
    except psycopg2.Error as e:
        print(f"❌ Error ejecutando script SQL:")
        print(f"  {e}")
        conn.rollback() # Deshacer si hubo error
        return False
    finally:
        if conn:
            conn.close()


#? Ejecución de carga y creación del schema
if __name__ == '__main__':
    # 1. Ejecutar el esquema SQL del archivo
    Ruta_a_esquema = "./schema.sql" 
    execute_schema_script(Ruta_a_esquema) 

    # 2. Probar la conexión
    test_conn = get_db_connection()
    if test_conn:
        # Si la conexión existe, la cerramos
        test_conn.close()
        print("La conexión de prueba fue exitosa y se cerró.")