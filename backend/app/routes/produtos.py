from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database.connection import get_db
from app.models.models import Produto, Categoria, Fornecedor, Usuario
from app.schemas.schemas import (
    ProdutoCreate, ProdutoUpdate, ProdutoResponse,
    CategoriaCreate, CategoriaResponse, MessageResponse
)
from app.security.auth import get_current_user, require_permission
from app.services.helpers import registrar_log, calcular_status_validade, verificar_alertas_estoque

router = APIRouter(prefix="/produtos", tags=["Produtos"])


def _produto_response(p: Produto) -> ProdutoResponse:
    return ProdutoResponse(
        id=p.id,
        nome=p.nome,
        sku=p.sku,
        codigo_interno=p.codigo_interno,
        codigo_barras=p.codigo_barras,
        categoria_id=p.categoria_id,
        fornecedor_id=p.fornecedor_id,
        quantidade=p.quantidade,
        quantidade_minima=p.quantidade_minima,
        preco=p.preco,
        validade=p.validade,
        ativo=p.ativo,
        status_validade=calcular_status_validade(p.validade),
        categoria_nome=p.categoria.nome if p.categoria else None,
        fornecedor_nome=p.fornecedor.nome if p.fornecedor else None,
    )


@router.get("/", response_model=list[ProdutoResponse])
def listar_produtos(
    busca: Optional[str] = Query(None),
    categoria_id: Optional[int] = Query(None),
    estoque_baixo: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    q = db.query(Produto).filter(Produto.ativo == True)
    if busca:
        q = q.filter(
            (Produto.nome.ilike(f"%{busca}%")) |
            (Produto.sku.ilike(f"%{busca}%")) |
            (Produto.codigo_barras.ilike(f"%{busca}%"))
        )
    if categoria_id:
        q = q.filter(Produto.categoria_id == categoria_id)
    if estoque_baixo:
        q = q.filter(Produto.quantidade <= Produto.quantidade_minima)
    return [_produto_response(p) for p in q.order_by(Produto.nome).all()]


@router.get("/barcode/{codigo}", response_model=ProdutoResponse)
def buscar_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    p = db.query(Produto).filter(
        (Produto.codigo_barras == codigo) | (Produto.sku == codigo)
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return _produto_response(p)


@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return _produto_response(p)


@router.post("/", response_model=ProdutoResponse)
def criar_produto(
    data: ProdutoCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    if db.query(Produto).filter(Produto.sku == data.sku).first():
        raise HTTPException(status_code=400, detail="SKU já cadastrado")

    produto = Produto(**data.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    verificar_alertas_estoque(db)
    registrar_log(db, user.id, f"Produto cadastrado: {produto.nome}", "produtos", produto.sku)
    return _produto_response(produto)


@router.put("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(
    produto_id: int,
    data: ProdutoUpdate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    verificar_alertas_estoque(db)
    registrar_log(db, user.id, f"Produto atualizado: {p.nome}", "produtos")
    return _produto_response(p)


@router.delete("/{produto_id}", response_model=MessageResponse)
def excluir_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    p = db.query(Produto).filter(Produto.id == produto_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    p.ativo = False
    db.commit()
    registrar_log(db, user.id, f"Produto excluído: {p.nome}", "produtos")
    return MessageResponse(message="Produto removido")


@router.get("/categorias/list", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return db.query(Categoria).order_by(Categoria.nome).all()


@router.post("/categorias", response_model=CategoriaResponse)
def criar_categoria(
    data: CategoriaCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_permission("produtos")),
):
    cat = Categoria(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
