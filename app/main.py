from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app import models, schemas, crud
from app.database import engine, get_db
from sqlalchemy import func

# Crear tablas en la DB
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SMAT - Backend Profesional",
    description="""
    API robusta para la gestión y monitoreo de desastres naturales.
    Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.
    **Entidades principales:**
    * **Estaciones:** Puntos de monitoreo físico.
    * **Lecturas:** Datos capturados por sensores.
    * **Riesgos:** Análisis de criticidad basado en umbrales.
    """,
    version="1.0.0",
    terms_of_service="http://unmsm.edu.pe/terms/",
    contact={
    "name": "Soporte Técnico SMAT - FISI",
    "url": "http://fisi.unmsm.edu.pe",
    "email": "desarrollo.smat@unmsm.edu.pe",
    },
    license_info={
    "name": "Apache 2.0",
    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    )
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ENDPOINTS
# =========================

# Crear estación
@app.post(
    "/estaciones/",
    status_code=201,
    tags=["Gestión de Infraestructura"],
    summary="Registrar una nueva estación de monitoreo",
    description="Inserta una estación física (ej. río, volcán, zona sísmica) en la base de datos relacional."
    )
def crear_estacion(estacion: schemas.EstacionCreate, db: Session = Depends(get_db)):
    return crud.crear_estacion(db, estacion)


# Registrar lectura
@app.post(
    "/lecturas/",
    status_code=201,
    tags=["Telemetría de Sensores"],
    summary="Recibir datos de telemetría",
    description="Recibe el valor capturado por un sensor y lo vincula a una estación existente mediante su ID."
    )
def registrar_lectura(lectura: schemas.LecturaCreate, db: Session = Depends(get_db)):
    return crud.crear_lectura(db, lectura)


# Listar estaciones
@app.get(
    "/estaciones/",
    tags=["Gestión de Infraestructura"],
    summary="Listar estaciones registradas",
    description="Devuelve todas las estaciones almacenadas en la base de datos en formato JSON."
)
def listar_estaciones(db: Session = Depends(get_db)):
    return crud.obtener_estaciones(db)


# Historial de lecturas
@app.get(
    "/estaciones/{id}/historial",
    tags=["Reportes Históricos"],
    summary="Obtener historial de lecturas",
    description="Devuelve todas las lecturas de una estación, incluyendo el conteo total y el promedio de valores registrados.",
    responses={404: {"description": "Estación no encontrada"}}
)
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


#obetener riesgo
@app.get(
    "/estaciones/{id}/riesgo",
    tags=["Análisis de Riesgo"],
    summary="Evaluar nivel de peligro actual",
    description="Analiza la última lectura recibida de una estación y determina si el estado es NORMAL, ALERTA o PELIGRO.",
    responses={404: {"description": "Estación no encontrada"}}
)
def obtener_riesgo(id: int, db: Session = Depends(get_db)):

    estacion = db.query(models.EstacionDB).filter(
        models.EstacionDB.id == id
    ).first()

    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    lecturas = db.query(models.LecturaDB).filter(
        models.LecturaDB.estacion_id == id
    ).all()

    if not lecturas:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}

    ultima_lectura = lecturas[-1].valor

    if ultima_lectura > 20:
        nivel = "PELIGRO"
    elif ultima_lectura > 10:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"

    return {
        "id": id,
        "valor": ultima_lectura,
        "nivel": nivel
    }


#reporte critico
@app.get(
    "/reportes/criticos",
    tags=["Auditoría"],
    summary="Reporte de estaciones críticas",
    description="Devuelve estaciones cuya última lectura supera un umbral definido. El parámetro opcional 'umbral' permite ajustar el nivel mínimo de alerta (por defecto 20.0)."
)
def reporte_criticos(umbral: float = 20.0, db: Session = Depends(get_db)):

    estaciones = db.query(models.EstacionDB).all()
    resultado = []

    for e in estaciones:
        lecturas = db.query(models.LecturaDB).filter(
            models.LecturaDB.estacion_id == e.id
        ).all()

        if lecturas:
            ultima = lecturas[-1].valor
            if ultima > umbral:
                resultado.append({
                    "estacion_id": e.id,
                    "nombre": e.nombre,
                    "valor": ultima
                })

    return {
        "umbral": umbral,
        "estaciones_criticas": resultado
    }


#stats
@app.get(
    "/estaciones/stats",
    tags=["Reportes Históricos"],
    summary="Resumen general del sistema",
    description="Proporciona un resumen ejecutivo del sistema SMAT, incluyendo número total de estaciones, total de lecturas y el valor máximo registrado."
)
def stats(db: Session = Depends(get_db)):

    total_estaciones = db.query(func.count(models.EstacionDB.id)).scalar()
    total_lecturas = db.query(func.count(models.LecturaDB.id)).scalar()
    max_valor = db.query(func.max(models.LecturaDB.valor)).scalar()

    return {
        "total_estaciones": total_estaciones,
        "total_lecturas": total_lecturas,
        "max_valor": max_valor
    }