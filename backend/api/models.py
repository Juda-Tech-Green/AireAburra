from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry # Necesario para la columna geom
from .database import Base

class Estacion(Base):
    __tablename__ = "estaciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre_estacion = Column(String, unique=True, index=True)
    municipio = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
    
    # Columna espacial (PostGIS)
    # srid=4326 es el estándar GPS (WGS84)
    geom = Column(Geometry('POINT', srid=4326))

    # Relación: Una estación tiene muchas mediciones
    mediciones = relationship("Medicion", back_populates="estacion")

class Medicion(Base):
    __tablename__ = "mediciones"

    id = Column(Integer, primary_key=True, index=True)
    estacion_id = Column(Integer, ForeignKey("estaciones.id"))
    fecha = Column(Date, index=True)
    
    # Contaminantes
    pm25 = Column(Float)
    pm10 = Column(Float)
    no = Column(Float)
    no2 = Column(Float)
    nox = Column(Float)
    so2 = Column(Float)
    co = Column(Float)
    o3 = Column(Float)
    
    # Meteorología
    haire2 = Column(Float)
    haire10 = Column(Float)
    taire2 = Column(Float)
    taire10 = Column(Float)
    tmpr_air_10cm = Column(Float)
    p = Column(Float)
    rglobal = Column(Float)
    vviento = Column(Float)
    dviento = Column(Float)

    # Relación inversa
    estacion = relationship("Estacion", back_populates="mediciones")