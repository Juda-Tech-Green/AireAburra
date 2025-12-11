from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware # <--- 1. IMPORTAR ESTO
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from . import models, schemas, database

app = FastAPI(title="Aire Aburrá API")

# --- 2. CONFIGURACIÓN DE CORS (VITAL PARA EL FRONTEND) ---
origins = [
    "http://localhost:3000",    # React / Next.js
    "http://localhost:5173",    # Vite / Astro (Probablemente usaremos este)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # Qué dominios pueden pedir datos
    allow_credentials=True,
    allow_methods=["*"],        # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],        # Permitir todos los headers
)
# ---------------------------------------------------------

@app.get("/estaciones", response_model=List[schemas.EstacionResponse])
def obtener_estaciones(db: Session = Depends(database.get_db)):
    """
    Obtiene todas las estaciones disponibles para pintar en el mapa.
    """
    return db.query(models.Estacion).all()

@app.get("/estaciones/{estacion_id}", response_model=schemas.EstacionResponse)
def obtener_estacion(estacion_id: int, db: Session = Depends(database.get_db)):
    estacion = db.query(models.Estacion).filter(models.Estacion.id == estacion_id).first()
    if estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return estacion

@app.get("/mediciones/historico/{estacion_id}", response_model=List[schemas.MedicionResponse])
def obtener_historico(
    estacion_id: int,
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(database.get_db)
):
    """
    Obtiene la serie de tiempo filtrada por fechas.
    """
    consulta = db.query(models.Medicion).filter(models.Medicion.estacion_id == estacion_id)

    if fecha_inicio:
        consulta = consulta.filter(models.Medicion.fecha >= fecha_inicio)
    
    if fecha_fin:
        consulta = consulta.filter(models.Medicion.fecha <= fecha_fin)

    resultados = consulta.order_by(models.Medicion.fecha.asc()).all()

    if not resultados:
        return []
        
    return resultados