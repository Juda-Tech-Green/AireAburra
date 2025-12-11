import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# 1. Cargar variables de entorno desde la raíz del proyecto
# Ajustamos la ruta para buscar el .env dos carpetas arriba (backend/app -> backend -> root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR,'backend','database', ".env"))

# 2. Construir la URL de conexión
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3. Crear el motor (Engine)
# pool_pre_ping=True ayuda a reconectar si la base de datos cierra la conexión
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# 4. Crear la fábrica de sesiones (SessionLocal)
# Cada petición al servidor creará una nueva sesión usando esto
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. Clase Base para los modelos
Base = declarative_base()

# 6. Dependencia (Dependency)
# Esta función se usará en cada endpoint para abrir y cerrar la conexión automáticamente
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
