from app import models

def crear_estacion(db, estacion):
    nueva = models.EstacionDB(**estacion.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return {
        "id": nueva.id,
        "nombre": nueva.nombre,
        "ubicacion": nueva.ubicacion
    }

def obtener_estaciones(db):
    return db.query(models.EstacionDB).all()

def crear_lectura(db, lectura):
    nueva = models.LecturaDB(**lectura.model_dump())
    db.add(nueva)
    db.commit()
    return nueva