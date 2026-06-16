from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Fornecedor, Usuario
from app.schemas.schemas import FornecedorCreate, FornecedorResponse, MessageResponse
from app.security.auth import require_permission
from app.services.helpers import registrar_log

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])


@router.get("/", response_model=list[FornecedorResponse])
def listar(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("fornecedores"))):
    return db.query(Fornecedor).filter(Fornecedor.ativo == True).order_by(Fornecedor.nome).all()


@router.get("/{fornecedor_id}", response_model=FornecedorResponse)
def obter(fornecedor_id: int, db: Session = Depends(get_db), user: Usuario = Depends(require_permission("fornecedores"))):
    f = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return f


@router.post("/", response_model=FornecedorResponse)
def criar(data: FornecedorCreate, db: Session = Depends(get_db), user: Usuario = Depends(require_permission("fornecedores"))):
    if db.query(Fornecedor).filter(Fornecedor.cnpj == data.cnpj).first():
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado")
    f = Fornecedor(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    registrar_log(db, user.id, f"Fornecedor cadastrado: {f.nome}", "fornecedores")
    return f


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
def atualizar(fornecedor_id: int, data: FornecedorCreate, db: Session = Depends(get_db), user: Usuario = Depends(require_permission("fornecedores"))):
    f = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    for k, v in data.model_dump().items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    registrar_log(db, user.id, f"Fornecedor atualizado: {f.nome}", "fornecedores")
    return f


@router.delete("/{fornecedor_id}", response_model=MessageResponse)
def excluir(fornecedor_id: int, db: Session = Depends(get_db), user: Usuario = Depends(require_permission("fornecedores"))):
    f = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    f.ativo = False
    db.commit()
    registrar_log(db, user.id, f"Fornecedor removido: {f.nome}", "fornecedores")
    return MessageResponse(message="Fornecedor removido")
