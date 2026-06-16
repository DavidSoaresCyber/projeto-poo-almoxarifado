from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.models.models import Usuario, CARGO_NIVEL
from app.schemas.schemas import UsuarioResponse, UsuarioUpdate, MessageResponse
from app.security.auth import get_current_user, require_permission, get_user_permissions
from app.services.helpers import registrar_log

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _to_response(u: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=u.id,
        nome_completo=u.nome_completo,
        email=u.email,
        telefone=u.telefone,
        cargo=u.cargo,
        foto_perfil=u.foto_perfil,
        ativo=u.ativo,
        ultimo_acesso=u.ultimo_acesso,
        permissoes=get_user_permissions(u),
        nivel_acesso=CARGO_NIVEL.get(u.cargo, 0),
        status="online" if u.ativo else "offline",
    )


@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("usuarios")),
):
    usuarios = db.query(Usuario).order_by(Usuario.nome_completo).all()
    return [_to_response(u) for u in usuarios]


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("usuarios")),
):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _to_response(u)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def atualizar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("usuarios")),
):
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(u, field, value)

    db.commit()
    db.refresh(u)
    registrar_log(db, user.id, f"Usuário atualizado: {u.nome_completo}", "usuarios")
    return _to_response(u)


@router.delete("/{usuario_id}", response_model=MessageResponse)
def desativar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("usuarios")),
):
    if usuario_id == user.id:
        raise HTTPException(status_code=400, detail="Não é possível desativar sua própria conta")
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    u.ativo = False
    db.commit()
    registrar_log(db, user.id, f"Usuário desativado: {u.nome_completo}", "usuarios")
    return MessageResponse(message="Usuário desativado")
