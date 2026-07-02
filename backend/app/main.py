from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas, auth, crud
from app.database import engine, get_db, SessionLocal

models.Base.metadata.create_all(bind=engine)

# Usuario admin por defecto para desarrollo/pruebas del curso.
# En un entorno real esto se gestionaría con un endpoint de registro.
DEFAULT_ADMIN_USER = "admin_fisi"
DEFAULT_ADMIN_PASSWORD = "smat2026"

def _sembrar_usuario_admin():
    db = SessionLocal()
    try:
        auth.crear_usuario_si_no_existe(db, DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD)
    finally:
        db.close()

_sembrar_usuario_admin()

app = FastAPI(
    title="SMAT - Sistema de Monitoreo de Alerta Temprana",
    description="""
API para gestión y monitoreo de desastres naturales.
Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.

**Entidades principales:**
* **Estaciones:** Puntos de monitoreo físico.
* **Lecturas:** Datos capturados por sensores.
* **Riesgos:** Análisis de criticidad basado en umbrales.
    """,
    version="1.0.0",
    contact={
        "name": "Soporte Técnico SMAT - FISI",
        "url": "http://fisi.unmsm.edu.pe",
        "email": "desarrollo.smat@unmsm.edu.pe",
    },
    license_info={"name": "Apache 2.0"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SEGURIDAD ---

@app.post(
    "/token",
    tags=["Seguridad"],
    summary="Obtener token de acceso",
    description="Valida usuario y contraseña contra la base de datos y devuelve un JWT. "
                 f"Usuario de prueba: '{DEFAULT_ADMIN_USER}' / contraseña: '{DEFAULT_ADMIN_PASSWORD}'.",
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = auth.autenticar_usuario(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {
        "access_token": auth.crear_token_acceso({"sub": usuario.username}),
        "token_type": "bearer"
    }

# --- ESTACIONES ---

@app.get(
    "/estaciones/",
    response_model=list[schemas.Estacion],
    tags=["Gestión de Infraestructura"],
    summary="Listar todas las estaciones",
    description="Devuelve la lista completa de estaciones registradas en la base de datos."
)
def listar_estaciones(db: Session = Depends(get_db)):
    return crud.listar_estaciones(db)

@app.post(
    "/estaciones/",
    response_model=schemas.Estacion,
    status_code=201,
    tags=["Gestión de Infraestructura"],
    summary="Registrar una nueva estación",
    description="Inserta una estación física (río, volcán, zona sísmica) en la base de datos.",
    responses={404: {"description": "No encontrada"}}
)
def crear_estacion(
    estacion: schemas.EstacionCreate,
    db: Session = Depends(get_db),
    user: str = Depends(auth.validar_token)
):
    return crud.crear_estacion(db, estacion)

@app.put(
    "/estaciones/{id}",
    response_model=schemas.Estacion,
    tags=["Gestión de Infraestructura"],
    summary="Editar una estación existente",
    description="Actualiza el nombre y la ubicación de una estación registrada.",
    responses={404: {"description": "Estación no encontrada"}}
)
def editar_estacion(
    id: int,
    estacion: schemas.EstacionCreate,
    db: Session = Depends(get_db),
    user: str = Depends(auth.validar_token)
):
    actualizada = crud.editar_estacion(db, id, estacion)
    if not actualizada:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return actualizada

@app.delete(
    "/estaciones/{id}",
    tags=["Gestión de Infraestructura"],
    summary="Eliminar una estación",
    description="Elimina una estación y su historial de lecturas asociado.",
    responses={404: {"description": "Estación no encontrada"}}
)
def eliminar_estacion(
    id: int,
    db: Session = Depends(get_db),
    user: str = Depends(auth.validar_token)
):
    eliminada = crud.eliminar_estacion(db, id)
    if not eliminada:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return {"status": "Estación eliminada con éxito"}

# --- LECTURAS ---

@app.post(
    "/lecturas/",
    status_code=201,
    tags=["Telemetría de Sensores"],
    summary="Recibir datos de telemetría",
    description="Recibe el valor de un sensor y lo vincula a una estación existente.",
    responses={404: {"description": "Estación no encontrada"}}
)
def registrar_lectura(
    lectura: schemas.LecturaCreate,
    db: Session = Depends(get_db),
    user: str = Depends(auth.validar_token)
):
    estacion = crud.obtener_estacion(db, lectura.estacion_id)
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    crud.registrar_lectura(db, lectura)
    return {"status": "Lectura registrada con éxito"}

# --- ANÁLISIS ---

@app.get(
    "/estaciones/{id}/riesgo",
    tags=["Análisis de Riesgo"],
    summary="Evaluar nivel de peligro actual",
    description="Analiza la última lectura de una estación y determina si el estado es NORMAL, ALERTA o PELIGRO.",
    responses={404: {"description": "Estación no encontrada"}}
)
def obtener_riesgo(id: int, db: Session = Depends(get_db)):
    estacion = crud.obtener_estacion(db, id)
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    lecturas = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    if not lecturas:
        return {"id": id, "nivel": "SIN DATOS", "valor": 0}
    ultima = lecturas[-1].valor
    if ultima > 20.0:
        nivel = "PELIGRO"
    elif ultima > 10.0:
        nivel = "ALERTA"
    else:
        nivel = "NORMAL"
    return {"id": id, "valor": ultima, "nivel": nivel}

@app.get(
    "/estaciones/{id}/historial",
    tags=["Reportes Históricos"],
    summary="Ver historial y promedio de lecturas",
    description="Devuelve todas las lecturas de una estación con su conteo y promedio aritmético.",
    responses={404: {"description": "Estación no encontrada"}}
)
def obtener_historial(id: int, db: Session = Depends(get_db)):
    estacion = crud.obtener_estacion(db, id)
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")
    return crud.obtener_historial(db, id)

@app.get(
    "/estaciones/stats",
    tags=["Auditoría"],
    summary="Resumen ejecutivo del sistema",
    description="Devuelve el total de estaciones, lecturas procesadas y la estación con el valor más alto."
)
def obtener_stats(db: Session = Depends(get_db)):
    return crud.obtener_stats(db)