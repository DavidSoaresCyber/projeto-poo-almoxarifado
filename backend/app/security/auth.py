from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.database.connection import get_db
from app.models.models import Usuario, CARGO_PERMISSOES, CARGO_NIVEL, CargoEnum

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(senha: str) -> str:
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()


def verify_password(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode(), senha_hash.encode())


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    user = db.query(Usuario).filter(Usuario.id == int(user_id), Usuario.ativo == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user


def get_user_permissions(cargo: CargoEnum) -> list[str]:
    return CARGO_PERMISSOES.get(cargo, [])


def get_cargo_nivel(cargo: CargoEnum) -> int:
    return CARGO_NIVEL.get(cargo, 0)


def require_permission(modulo: str):
    def checker(user: Usuario = Depends(get_current_user)):
        perms = get_user_permissions(user.cargo)
        if "*" not in perms and modulo not in perms:
            raise HTTPException(status_code=403, detail=f"Acesso negado ao módulo: {modulo}")
        return user
    return checker


def require_admin(user: Usuario = Depends(get_current_user)) -> Usuario:
    if user.cargo != CargoEnum.ADMINISTRADOR:
        raise HTTPException(status_code=403, detail="Apenas administradores")
    return user
