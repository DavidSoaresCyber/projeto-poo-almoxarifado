from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models.models import Usuario, CargoEnum
from app.schemas.schemas import UsuarioCreate, UsuarioResponse, TokenResponse, LoginRequest
from app.security.auth import (
    verify_password, create_access_token, get_current_user,
    hash_password, get_user_permissions, get_cargo_nivel
)
from app.services.services import criar_usuario, usuario_to_response, registrar_log

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None):
    user = db.query(Usuario).filter(Usuario.email == form.username).first()
    if not user or not verify_password(form.password, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    user.ultimo_acesso = datetime.utcnow()
    db.commit()
    ip = request.client.host if request else ""
    registrar_log(db, user.id, "login", f"Login realizado por {user.email}", ip)
    token = create_access_token({"sub": str(user.id), "cargo": user.cargo.value})
    return TokenResponse(access_token=token, usuario=usuario_to_response(user))


@router.post("/login/json", response_model=TokenResponse)
def login_json(data: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    user = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not user or not verify_password(data.senha, user.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuário desativado")
    user.ultimo_acesso = datetime.utcnow()
    db.commit()
    ip = request.client.host if request else ""
    registrar_log(db, user.id, "login", f"Login JSON: {user.email}", ip)
    token = create_access_token({"sub": str(user.id), "cargo": user.cargo.value})
    return TokenResponse(access_token=token, usuario=usuario_to_response(user))


@router.post("/register", response_model=UsuarioResponse)
def register(data: UsuarioCreate, db: Session = Depends(get_db)):
    from app.models.models import CargoEnum
    if data.cargo == CargoEnum.ADMINISTRADOR:
        raise HTTPException(status_code=400, detail="Cadastro de administrador não permitido por aqui")
    try:
        user = criar_usuario(db, data)
        registrar_log(db, user.id, "cadastro", f"Novo usuário: {user.email}")
        return usuario_to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UsuarioResponse)
def me(user: Usuario = Depends(get_current_user)):
    return usuario_to_response(user)


@router.get("/cargos")
def listar_cargos():
    return [{"valor": c.value, "nivel": get_cargo_nivel(c), "permissoes": get_user_permissions(c)} for c in CargoEnum]
