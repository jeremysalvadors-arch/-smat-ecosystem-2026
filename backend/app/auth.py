from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models

# En un entorno real esto debe venir de una variable de entorno,
# nunca quedar hardcodeado en el repositorio.
SECRET_KEY = "UNMSM_FISI_SMAT_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    return pwd_context.verify(password_plano, password_hash)


def autenticar_usuario(db: Session, username: str, password: str):
    """Busca al usuario en la BD y valida su contraseña. Devuelve el usuario o None."""
    usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.username == username).first()
    if not usuario:
        return None
    if not verificar_password(password, usuario.hashed_password):
        return None
    return usuario


def crear_usuario_si_no_existe(db: Session, username: str, password: str):
    """Usado en el arranque de la app para sembrar un usuario admin por defecto."""
    existente = db.query(models.UsuarioDB).filter(models.UsuarioDB.username == username).first()
    if existente:
        return existente
    nuevo = models.UsuarioDB(username=username, hashed_password=hashear_password(password))
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def crear_token_acceso(data: dict):
    para_encriptar = data.copy()
    expiracion = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    para_encriptar.update({"exp": expiracion})
    return jwt.encode(para_encriptar, SECRET_KEY, algorithm=ALGORITHM)


def validar_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")