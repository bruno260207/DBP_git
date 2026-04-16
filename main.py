from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import engine, get_db

# Crear tablas en la DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SMAT Persistente")


# =========================
# SCHEMAS (Pydantic)
# =========================
class EstacionCreate(BaseModel):
    id: int
    nombre: str
    ubicacion: str


class LecturaCreate(BaseModel):
    estacion_id: int
    valor: float


# =========================
# ENDPOINTS
# =========================

# Crear estación
@app.post("/estaciones/", status_code=201)
def crear_estacion(estacion: EstacionCreate, db: Session = Depends(get_db)):
    nueva_estacion = models.EstacionDB(
        id=estacion.id,
        nombre=estacion.nombre,
        ubicacion=estacion.ubicacion
    )

    db.add(nueva_estacion)
    db.commit()
    db.refresh(nueva_estacion)

    return {
        "msj": "Estación guardada en DB",
        "data": {
            "id": nueva_estacion.id,
            "nombre": nueva_estacion.nombre,
            "ubicacion": nueva_estacion.ubicacion
        }
    }


# Registrar lectura
@app.post("/lecturas/", status_code=201)
def registrar_lectura(lectura: LecturaCreate, db: Session = Depends(get_db)):
    estacion = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == lectura.estacion_id
    ).first()

    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no existe")

    nueva_lectura = models.LecturaDB(
        valor=lectura.valor,
        estacion_id=lectura.estacion_id
    )

    db.add(nueva_lectura)
    db.commit()

    return {"status": "Lectura guardada en DB"}


# Listar estaciones
@app.get("/estaciones/")
def listar_estaciones(db: Session = Depends(get_db)):
    estaciones = db.query(models.EstacionDB).all()

    return [
        {
            "id": e.id,
            "nombre": e.nombre,
            "ubicacion": e.ubicacion
        }
        for e in estaciones
    ]


# Historial de lecturas
@app.get("/estaciones/{id}/historial")
def historial(id: int, db: Session = Depends(get_db)):

    estacion = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == id
    ).first()

    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    lecturas = db.query(models.LecturaDB).filter(
        models.LecturaDB.estacion_id == id
    ).all()

    if not lecturas:
        return {
            "estacion_id": id,
            "lecturas": [],
            "conteo": 0,
            "promedio": 0
        }

    valores = [l.valor for l in lecturas]
    promedio = sum(valores) / len(valores)

    return {
        "estacion_id": id,
        "lecturas": [
            {
                "valor": l.valor,
                "estacion_id": l.estacion_id
            }
            for l in lecturas
        ],
        "conteo": len(lecturas),
        "promedio": promedio
    }