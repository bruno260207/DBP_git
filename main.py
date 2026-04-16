from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="SMAT API")

# Modelo Estacion
class Estacion(BaseModel):
    id: int
    nombre: str
    ubicacion: str

# Modelo Lectura
class Lectura(BaseModel):
    estacion_id: int
    valor: float

# "Base de datos"
db_estaciones = []
db_lecturas = []

# Crear estación
@app.post("/estaciones/", status_code=201)
async def crear_estacion(estacion: Estacion):
    db_estaciones.append(estacion)
    return {"msj": "Estación creada", "data": estacion}

# Listar estaciones
@app.get("/estaciones/", response_model=List[Estacion])
async def listar_estaciones():
    return db_estaciones

# Registrar lectura
@app.post("/lecturas/", status_code=201)
async def registrar_lectura(lectura: Lectura):
    db_lecturas.append(lectura)
    return {"status": "Lectura recibida"}

# Obtener riesgo
@app.get("/estaciones/{id}/riesgo")
async def obtener_riesgo(id: int):

    # Validar estación
    estacion_existe = any(e.id == id for e in db_estaciones)
    if not estacion_existe:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    # Filtrar lecturas
    lecturas = [l for l in db_lecturas if l.estacion_id == id]

    if not lecturas:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}

    # Última lectura
    ultima_lectura = lecturas[-1].valor

    # Reglas
    if ultima_lectura > 20.0:
        nivel = "PELIGRO"
    elif ultima_lectura > 10.0:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"

    return {"id": id, "valor": ultima_lectura, "nivel": nivel}
@app.get("/estaciones/{id}/historial")
async def obtener_historial(id: int):

    # 1. Validar si la estación existe
    estacion_existe = any(e.id == id for e in db_estaciones)
    if not estacion_existe:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    # 2. Obtener lecturas de esa estación
    lecturas = [l for l in db_lecturas if l.estacion_id == id]

    # 3. Contar lecturas
    conteo = len(lecturas)

    # 4. Calcular promedio
    if conteo == 0:
        promedio = 0
    else:
        promedio = sum(l.valor for l in lecturas) / conteo

    # 5. Retornar datos
    return {
        "estacion_id": id,
        "lecturas": lecturas,
        "conteo": conteo,
        "promedio": promedio
    }