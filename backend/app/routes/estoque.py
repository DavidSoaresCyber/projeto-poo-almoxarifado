from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Produto, Movimentacao, Usuario, TipoMovimentacao
from app.schemas.schemas import MovimentacaoCreate, MovimentacaoResponse, MessageResponse
from app.security.auth import require_permission
from app.services.helpers import registrar_log, verificar_alertas_estoque

router = APIRouter(prefix="/estoque", tags=["Estoque"])


def _mov_response(m: Movimentacao) -> MovimentacaoResponse:
    return MovimentacaoResponse(
        id=m.id,
        produto_id=m.produto_id,
        usuario_id=m.usuario_id,
        tipo=m.tipo,
        quantidade=m.quantidade,
        quantidade_anterior=m.quantidade_anterior,
        quantidade_atual=m.quantidade_atual,
        observacao=m.observacao,
        criado_em=m.criado_em,
        produto_nome=m.produto.nome if m.produto else None,
        usuario_nome=m.usuario.nome_completo if m.usuario else None,
    )


@router.post("/movimentar", response_model=MovimentacaoResponse)
def movimentar(
    data: MovimentacaoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("estoque")),
):
    produto = db.query(Produto).filter(Produto.id == data.produto_id, Produto.ativo == True).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    qtd_anterior = produto.quantidade

    if data.tipo == TipoMovimentacao.ENTRADA:
        qtd_atual = qtd_anterior + data.quantidade
    elif data.tipo == TipoMovimentacao.SAIDA:
        if qtd_anterior < data.quantidade:
            raise HTTPException(status_code=400, detail="Estoque insuficiente para saída")
        qtd_atual = qtd_anterior - data.quantidade
    else:
        qtd_atual = data.quantidade

    if qtd_atual < 0:
        raise HTTPException(status_code=400, detail="Operação resultaria em estoque negativo")

    produto.quantidade = qtd_atual

    mov = Movimentacao(
        produto_id=produto.id,
        usuario_id=user.id,
        tipo=data.tipo,
        quantidade=data.quantidade,
        quantidade_anterior=qtd_anterior,
        quantidade_atual=qtd_atual,
        observacao=data.observacao,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    verificar_alertas_estoque(db)
    registrar_log(db, user.id, f"{data.tipo.value.upper()}: {produto.nome} ({data.quantidade} un.)", "estoque")
    return _mov_response(mov)


@router.get("/movimentacoes", response_model=list[MovimentacaoResponse])
def listar_movimentacoes(
    tipo: Optional[str] = Query(None),
    produto_id: Optional[int] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("movimentacoes")),
):
    q = db.query(Movimentacao)
    if tipo:
        q = q.filter(Movimentacao.tipo == tipo)
    if produto_id:
        q = q.filter(Movimentacao.produto_id == produto_id)
    if data_inicio:
        q = q.filter(Movimentacao.criado_em >= datetime.fromisoformat(data_inicio))
    if data_fim:
        q = q.filter(Movimentacao.criado_em <= datetime.fromisoformat(data_fim))
    movs = q.order_by(Movimentacao.criado_em.desc()).limit(200).all()
    return [_mov_response(m) for m in movs]


@router.get("/alertas")
def alertas_estoque(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("estoque"))):
    baixo = db.query(Produto).filter(Produto.ativo == True, Produto.quantidade <= Produto.quantidade_minima).all()
    return {
        "estoque_baixo": [{"id": p.id, "nome": p.nome, "sku": p.sku, "quantidade": p.quantidade} for p in baixo],
        "total": len(baixo),
    }
