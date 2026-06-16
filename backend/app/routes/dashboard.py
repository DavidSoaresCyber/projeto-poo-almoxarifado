from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Usuario
from app.schemas.schemas import DashboardStats
from app.security.auth import get_current_user, get_user_permissions
from app.services.helpers import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    data = get_dashboard_stats(db)
    return DashboardStats(**data)


@router.get("/permissoes")
def permissoes(user: Usuario = Depends(get_current_user)):
    return {
        "cargo": user.cargo.value,
        "permissoes": get_user_permissions(user),
        "nome": user.nome_completo,
        "foto": user.foto_perfil,
    }
