from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models, schemas

def crear_estacion(db: Session, estacion: schemas.EstacionCreate):
    nueva = models.EstacionDB(**estacion.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_estaciones(db: Session):
    return db.query(models.EstacionDB).all()

def obtener_estacion(db: Session, id: int):
    return db.query(models.EstacionDB).filter(models.EstacionDB.id == id).first()

def registrar_lectura(db: Session, lectura: schemas.LecturaCreate):
    nueva = models.LecturaDB(**lectura.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def obtener_historial(db: Session, id: int):
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    valores = [l.valor for l in lecturas]
    promedio = round(sum(valores) / len(valores), 2) if valores else 0.0
    return {
        "estacion_id": id,
        "lecturas": valores,
        "conteo": len(valores),
        "promedio": promedio
    }

def obtener_stats(db: Session):
    total_estaciones = db.query(func.count(models.EstacionDB.id)).scalar()
    total_lecturas = db.query(func.count(models.LecturaDB.id)).scalar()
    max_lectura = db.query(models.LecturaDB).order_by(models.LecturaDB.valor.desc()).first()
    return {
        "total_estaciones": total_estaciones,
        "total_lecturas": total_lecturas,
        "max_valor": max_lectura.valor if max_lectura else None,
        "estacion_critica_id": max_lectura.estacion_id if max_lectura else None
    }