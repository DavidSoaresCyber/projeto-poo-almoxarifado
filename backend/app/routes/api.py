from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.database.connection import get_db
from app.models.models import Usuario, Produto, Fornecedor, Categoria, Movimentacao, Notificacao, LogAtividade, Auditoria
from app.schemas.schemas import (
    UsuarioResponse, UsuarioUpdate, ProdutoCreate, ProdutoUpdate, ProdutoResponse,
    FornecedorCreate, FornecedorResponse, CategoriaCreate, CategoriaResponse,
    MovimentacaoCreate, MovimentacaoResponse, DashboardStats, NotificacaoResponse,
    ChatRequest, ChatResponse
)
from app.security.auth import get_current_user, require_permission, require_admin
from app.services.services import (
    usuario_to_response, get_dashboard_stats, status_validade,
    gerar_notificacoes_automaticas, processar_morangia, registrar_log
)
from app.models.models import ConversaIA
import json

router = APIRouter(prefix="/api", tags=["API"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(user=Depends(require_permission("dashboard")), db: Session = Depends(get_db)):
    gerar_notificacoes_automaticas(db)
    return get_dashboard_stats(db)


@router.get("/dashboard/graficos")
def graficos(user=Depends(require_permission("dashboard")), db: Session = Depends(get_db)):
    from datetime import timedelta
    hoje = datetime.utcnow()
    dias = []
    entradas = []
    saidas = []
    DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    for i in range(6, -1, -1):
        dia = (hoje - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        fim = dia + timedelta(days=1)
        dias.append(DIAS_PT[dia.weekday()])
        entradas.append(db.query(Movimentacao).filter(Movimentacao.tipo == "entrada", Movimentacao.criado_em >= dia, Movimentacao.criado_em < fim).count())
        saidas.append(db.query(Movimentacao).filter(Movimentacao.tipo == "saida", Movimentacao.criado_em >= dia, Movimentacao.criado_em < fim).count())

    cats = db.query(Categoria).all()
    cat_labels = [c.nome for c in cats]
    cat_data = []
    for c in cats:
        cat_data.append(db.query(Produto).filter(Produto.categoria_id == c.id).count())

    return {"dias": dias, "entradas": entradas, "saidas": saidas, "categorias": cat_labels, "cat_data": cat_data}


# --- Produtos ---
@router.get("/produtos", response_model=list[ProdutoResponse])
def listar_produtos(
    busca: str = "", categoria_id: int = None,
    user=Depends(require_permission("produtos")), db: Session = Depends(get_db)
):
    q = db.query(Produto).filter(Produto.ativo == True)
    if busca:
        q = q.filter(or_(Produto.nome.ilike(f"%{busca}%"), Produto.sku.ilike(f"%{busca}%"), Produto.codigo_barras.ilike(f"%{busca}%")))
    if categoria_id:
        q = q.filter(Produto.categoria_id == categoria_id)
    produtos = q.order_by(Produto.nome).all()
    result = []
    for p in produtos:
        r = ProdutoResponse.model_validate(p)
        r.status_validade = status_validade(p.validade)
        result.append(r)
    return result


@router.post("/produtos", response_model=ProdutoResponse)
def criar_produto(data: ProdutoCreate, user=Depends(require_permission("produtos")), db: Session = Depends(get_db)):
    if db.query(Produto).filter(Produto.sku == data.sku).first():
        raise HTTPException(400, "SKU já existe")
    p = Produto(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    registrar_log(db, user.id, "produto_criado", f"Produto {p.nome} criado")
    r = ProdutoResponse.model_validate(p)
    r.status_validade = status_validade(p.validade)
    return r


@router.put("/produtos/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(produto_id: int, data: ProdutoUpdate, user=Depends(require_permission("produtos")), db: Session = Depends(get_db)):
    p = db.query(Produto).get(produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado")
    antes = json.dumps({"nome": p.nome, "quantidade": p.quantidade})
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    db.add(Auditoria(tabela="produtos", registro_id=p.id, acao="update", dados_antes=antes,
                     dados_depois=json.dumps({"nome": p.nome, "quantidade": p.quantidade}), usuario_id=user.id))
    db.commit()
    r = ProdutoResponse.model_validate(p)
    r.status_validade = status_validade(p.validade)
    return r


@router.delete("/produtos/{produto_id}")
def excluir_produto(produto_id: int, user=Depends(require_permission("produtos")), db: Session = Depends(get_db)):
    p = db.query(Produto).get(produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado")
    p.ativo = False
    db.commit()
    registrar_log(db, user.id, "produto_excluido", f"Produto {p.nome} desativado")
    return {"ok": True}


@router.get("/produtos/barcode/{codigo}")
def buscar_barcode(codigo: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(Produto).filter(or_(Produto.codigo_barras == codigo, Produto.sku == codigo)).first()
    if not p:
        raise HTTPException(404, "Produto não encontrado")
    r = ProdutoResponse.model_validate(p)
    r.status_validade = status_validade(p.validade)
    return r


# --- Estoque / Movimentações ---
@router.get("/movimentacoes", response_model=list[MovimentacaoResponse])
def listar_movimentacoes(tipo: str = None, user=Depends(require_permission("movimentacoes")), db: Session = Depends(get_db)):
    q = db.query(Movimentacao).order_by(Movimentacao.criado_em.desc())
    if tipo:
        q = q.filter(Movimentacao.tipo == tipo)
    movs = q.limit(100).all()
    result = []
    for m in movs:
        r = MovimentacaoResponse.model_validate(m)
        r.produto_nome = m.produto.nome if m.produto else None
        r.usuario_nome = m.usuario.nome_completo if m.usuario else None
        result.append(r)
    return result


@router.post("/movimentacoes", response_model=MovimentacaoResponse)
def registrar_movimentacao(data: MovimentacaoCreate, user=Depends(require_permission("movimentacoes")), db: Session = Depends(get_db)):
    p = db.query(Produto).get(data.produto_id)
    if not p:
        raise HTTPException(404, "Produto não encontrado")
    if data.tipo == "saida" and p.quantidade < data.quantidade:
        raise HTTPException(400, "Estoque insuficiente")
    if data.tipo == "entrada":
        p.quantidade += data.quantidade
    else:
        p.quantidade -= data.quantidade
    mov = Movimentacao(produto_id=data.produto_id, usuario_id=user.id, tipo=data.tipo,
                       quantidade=data.quantidade, observacao=data.observacao)
    db.add(mov)
    db.commit()
    db.refresh(mov)
    registrar_log(db, user.id, f"movimentacao_{data.tipo}", f"{data.quantidade}x {p.nome}")
    r = MovimentacaoResponse.model_validate(mov)
    r.produto_nome = p.nome
    r.usuario_nome = user.nome_completo
    return r


# --- Fornecedores ---
@router.get("/fornecedores", response_model=list[FornecedorResponse])
def listar_fornecedores(user=Depends(require_permission("fornecedores")), db: Session = Depends(get_db)):
    return db.query(Fornecedor).filter(Fornecedor.ativo == True).order_by(Fornecedor.nome).all()


@router.post("/fornecedores", response_model=FornecedorResponse)
def criar_fornecedor(data: FornecedorCreate, user=Depends(require_permission("fornecedores")), db: Session = Depends(get_db)):
    f = Fornecedor(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.delete("/fornecedores/{fid}")
def excluir_fornecedor(fid: int, user=Depends(require_permission("fornecedores")), db: Session = Depends(get_db)):
    f = db.query(Fornecedor).get(fid)
    if f:
        f.ativo = False
        db.commit()
    return {"ok": True}


# --- Categorias ---
@router.get("/categorias", response_model=list[CategoriaResponse])
def listar_categorias(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.nome).all()


@router.post("/categorias", response_model=CategoriaResponse)
def criar_categoria(data: CategoriaCreate, user=Depends(require_admin), db: Session = Depends(get_db)):
    c = Categoria(**data.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


# --- Usuários ---
@router.get("/usuarios", response_model=list[UsuarioResponse])
def listar_usuarios(user=Depends(require_permission("usuarios")), db: Session = Depends(get_db)):
    users = db.query(Usuario).order_by(Usuario.nome_completo).all()
    return [usuario_to_response(u) for u in users]


@router.put("/usuarios/{uid}", response_model=UsuarioResponse)
def atualizar_usuario(uid: int, data: UsuarioUpdate, user=Depends(require_admin), db: Session = Depends(get_db)):
    u = db.query(Usuario).get(uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return usuario_to_response(u)


# --- Notificações ---
@router.get("/notificacoes", response_model=list[NotificacaoResponse])
def listar_notificacoes(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notificacao).order_by(Notificacao.criado_em.desc()).limit(20).all()


@router.patch("/notificacoes/{nid}/lida")
def marcar_lida(nid: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notificacao).get(nid)
    if n:
        n.lida = True
        db.commit()
    return {"ok": True}


# --- Logs ---
@router.get("/logs")
def listar_logs(user=Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(LogAtividade).order_by(LogAtividade.criado_em.desc()).limit(50).all()
    return [{"id": l.id, "acao": l.acao, "detalhes": l.detalhes, "usuario": l.usuario.nome_completo if l.usuario else None, "criado_em": l.criado_em.isoformat()} for l in logs]


# --- Auditoria ---
@router.get("/auditoria")
def listar_auditoria(user=Depends(require_admin), db: Session = Depends(get_db)):
    items = db.query(Auditoria).order_by(Auditoria.criado_em.desc()).limit(50).all()
    return [{"id": a.id, "tabela": a.tabela, "acao": a.acao, "antes": a.dados_antes, "depois": a.dados_depois, "criado_em": a.criado_em.isoformat()} for a in items]


# --- MorangIA ---
@router.post("/morangia/chat", response_model=ChatResponse)
def chat_morangia(data: ChatRequest, user=Depends(require_permission("morangia")), db: Session = Depends(get_db)):
    resposta, sugestoes = processar_morangia(db, data.mensagem, user)
    conv = ConversaIA(usuario_id=user.id, mensagem=data.mensagem, resposta=resposta)
    db.add(conv)
    db.commit()
    return ChatResponse(resposta=resposta, sugestoes=sugestoes)


# --- Backup ---
@router.get("/backup/info")
def backup_info(user=Depends(require_admin), db: Session = Depends(get_db)):
    return {
        "produtos": db.query(Produto).count(),
        "usuarios": db.query(Usuario).count(),
        "movimentacoes": db.query(Movimentacao).count(),
        "gerado_em": datetime.utcnow().isoformat(),
    }
