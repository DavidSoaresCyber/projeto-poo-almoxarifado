from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Notificacao, LogAtividade, Auditoria, Usuario
from app.schemas.schemas import NotificacaoResponse, LogResponse, MessageResponse
from app.security.auth import get_current_user, require_permission

router = APIRouter(tags=["Sistema"])


@router.get("/notificacoes", response_model=list[NotificacaoResponse])
def listar_notificacoes(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return db.query(Notificacao).filter(
        (Notificacao.usuario_id == user.id) | (Notificacao.usuario_id == None)
    ).order_by(Notificacao.criado_em.desc()).limit(50).all()


@router.put("/notificacoes/{notif_id}/ler", response_model=MessageResponse)
def marcar_lida(notif_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    n = db.query(Notificacao).filter(Notificacao.id == notif_id).first()
    if n:
        n.lida = True
        db.commit()
    return MessageResponse(message="Notificação marcada como lida")


@router.put("/notificacoes/ler-todas", response_model=MessageResponse)
def marcar_todas_lidas(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    db.query(Notificacao).filter(Notificacao.lida == False).update({"lida": True})
    db.commit()
    return MessageResponse(message="Todas notificações marcadas como lidas")


@router.get("/logs", response_model=list[LogResponse])
def listar_logs(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("auditoria"))):
    logs = db.query(LogAtividade).order_by(LogAtividade.criado_em.desc()).limit(100).all()
    return [
        LogResponse(
            id=l.id, acao=l.acao, modulo=l.modulo, detalhes=l.detalhes,
            criado_em=l.criado_em, usuario_nome=l.usuario.nome_completo if l.usuario else "Sistema"
        ) for l in logs
    ]


@router.get("/auditoria")
def listar_auditoria(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("auditoria"))):
    items = db.query(Auditoria).order_by(Auditoria.criado_em.desc()).limit(100).all()
    return [
        {
            "id": a.id, "tabela": a.tabela, "registro_id": a.registro_id,
            "acao": a.acao, "dados_anteriores": a.dados_anteriores,
            "dados_novos": a.dados_novos, "criado_em": a.criado_em.isoformat(),
        } for a in items
    ]
