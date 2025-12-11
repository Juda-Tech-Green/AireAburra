from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# --- ESQUEMAS PARA ESTACIONES ---

class EstacionBase(BaseModel):
    nombre_estacion: str
    municipio: Optional[str] = None
    latitud: float
    longitud: float

class EstacionResponse(EstacionBase):
    id: int
    
    # Configuración necesaria para que Pydantic lea objetos de SQLAlchemy (ORM)
    class Config:
        from_attributes = True

# --- ESQUEMAS PARA MEDICIONES ---
from pydantic import BaseModel
from typing import Optional
from datetime import date

# ... (Tus esquemas de Estacion siguen igual) ...

class MedicionBase(BaseModel):
    fecha: date
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    
    # Variables meteorológicas (nombres del modelo SQLAlchemy)
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    velocidad_viento: Optional[float] = None
    direccion_viento: Optional[float] = None
    precipitacion: Optional[float] = None
    rglobal: Optional[float] = None

class MedicionResponse(MedicionBase):
    id: int
    estacion_id: int

    class Config:
        from_attributes = True