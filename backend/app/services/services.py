from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.models import (
    Usuario, Produto, Fornecedor, Movimentacao, Categoria,
    LogAtividade, Notificacao, Auditoria, ConversaIA, CargoEnum
)
from app.schemas.schemas import UsuarioCreate, UsuarioResponse
from app.security.auth import hash_password, get_user_permissions, get_cargo_nivel


def registrar_log(db: Session, usuario_id: int | None, acao: str, detalhes: str = "", ip: str = ""):
    log = LogAtividade(usuario_id=usuario_id, acao=acao, detalhes=detalhes, ip=ip)
    db.add(log)
    db.commit()


def usuario_to_response(user: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=user.id,
        nome_completo=user.nome_completo,
        email=user.email,
        telefone=user.telefone,
        cargo=user.cargo,
        foto_perfil=user.foto_perfil,
        ativo=user.ativo,
        ultimo_acesso=user.ultimo_acesso,
        permissoes=get_user_permissions(user.cargo),
        nivel_acesso=get_cargo_nivel(user.cargo),
        status="online",
    )


def criar_usuario(db: Session, data: UsuarioCreate) -> Usuario:
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise ValueError("Email já cadastrado")
    user = Usuario(
        nome_completo=data.nome_completo,
        email=data.email,
        telefone=data.telefone,
        cargo=data.cargo,
        senha_hash=hash_password(data.senha),
        foto_perfil=data.foto_perfil,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def status_validade(validade: datetime | None) -> str:
    if not validade:
        return "sem_validade"
    hoje = datetime.utcnow()
    if validade < hoje:
        return "vencido"
    if validade <= hoje + timedelta(days=7):
        return "vencendo"
    if validade <= hoje + timedelta(days=30):
        return "atencao"
    return "ok"


def get_dashboard_stats(db: Session) -> dict:
    hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    semana = hoje + timedelta(days=7)

    produtos = db.query(Produto).filter(Produto.ativo == True).all()
    total = len(produtos)
    baixo = sum(1 for p in produtos if p.quantidade <= p.quantidade_minima)
    vencendo = sum(1 for p in produtos if p.validade and hoje <= p.validade <= semana)
    vencidos = sum(1 for p in produtos if p.validade and p.validade < hoje)
    valor = sum(p.quantidade * p.preco for p in produtos)

    mov_hoje = db.query(Movimentacao).filter(Movimentacao.criado_em >= hoje).count()
    entradas = db.query(Movimentacao).filter(Movimentacao.tipo == "entrada", Movimentacao.criado_em >= hoje).count()
    saidas = db.query(Movimentacao).filter(Movimentacao.tipo == "saida", Movimentacao.criado_em >= hoje).count()

    return {
        "total_produtos": total,
        "estoque_baixo": baixo,
        "produtos_vencendo": vencendo,
        "produtos_vencidos": vencidos,
        "total_fornecedores": db.query(Fornecedor).filter(Fornecedor.ativo == True).count(),
        "movimentacoes_hoje": mov_hoje,
        "valor_estoque": round(valor, 2),
        "entradas_recentes": entradas,
        "saidas_recentes": saidas,
    }


def gerar_notificacoes_automaticas(db: Session):
    hoje = datetime.utcnow()
    semana = hoje + timedelta(days=7)
    produtos_baixo = db.query(Produto).filter(
        Produto.ativo == True, Produto.quantidade <= Produto.quantidade_minima
    ).all()
    for p in produtos_baixo:
        existe = db.query(Notificacao).filter(
            Notificacao.titulo == f"Estoque baixo: {p.nome}",
            Notificacao.lida == False,
        ).first()
        if not existe:
            db.add(Notificacao(
                titulo=f"Estoque baixo: {p.nome}",
                mensagem=f"Produto {p.nome} com apenas {p.quantidade} unidades.",
                tipo="alerta",
            ))
    produtos_venc = db.query(Produto).filter(
        Produto.validade != None, Produto.validade <= semana, Produto.validade >= hoje
    ).all()
    for p in produtos_venc:
        existe = db.query(Notificacao).filter(
            Notificacao.titulo == f"Validade próxima: {p.nome}",
            Notificacao.lida == False,
        ).first()
        if not existe:
            db.add(Notificacao(
                titulo=f"Validade próxima: {p.nome}",
                mensagem=f"Validade em {p.validade.strftime('%d/%m/%Y')}.",
                tipo="validade",
            ))
    db.commit()


def processar_morangia(db: Session, mensagem: str, usuario: Usuario) -> tuple[str, list[str]]:
    msg = mensagem.lower().strip()
    sugestoes = [
        "Quantos produtos estão com estoque baixo?",
        "Produtos vencendo esta semana",
        "Mostrar movimentações de hoje",
        "Como cadastrar um produto?",
    ]

    perms = get_user_permissions(usuario.cargo)

    if "estoque baixo" in msg or "falta" in msg:
        if "dashboard" not in perms and "*" not in perms:
            return "Seu cargo não possui acesso a dados de estoque.", sugestoes
        stats = get_dashboard_stats(db)
        return f"Atualmente temos {stats['estoque_baixo']} produto(s) com estoque baixo.", sugestoes

    if "vencendo" in msg or "validade" in msg:
        stats = get_dashboard_stats(db)
        return f"Existem {stats['produtos_vencendo']} produto(s) vencendo nos próximos 7 dias e {stats['produtos_vencidos']} vencido(s).", sugestoes

    if "movimenta" in msg or "hoje" in msg:
        if "movimentacoes" not in perms and "*" not in perms:
            return "Você não tem permissão para consultar movimentações.", sugestoes
        hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        movs = db.query(Movimentacao).filter(Movimentacao.criado_em >= hoje).count()
        return f"Hoje foram registradas {movs} movimentação(ões) no almoxarifado.", sugestoes

    if "fornecedor" in msg or "arroz" in msg:
        if "fornecedores" not in perms and "*" not in perms:
            return "Consulta de fornecedores restrita ao seu cargo.", sugestoes
        if "arroz" in msg:
            prod = db.query(Produto).filter(Produto.nome.ilike("%arroz%")).first()
            if prod and prod.fornecedor_id:
                f = db.query(Fornecedor).get(prod.fornecedor_id)
                return f"O arroz ({prod.nome}) é fornecido por {f.nome if f else 'fornecedor não informado'}.", sugestoes
        total = db.query(Fornecedor).filter(Fornecedor.ativo == True).count()
        return f"Temos {total} fornecedor(es) ativos cadastrados.", sugestoes

    if "relatório" in msg or "relatorio" in msg:
        if "relatorios" not in perms and "*" not in perms:
            return "Relatórios disponíveis para Gerentes e Administradores.", sugestoes
        return "Acesse o módulo Relatórios para exportar PDF ou Excel com logo Moranguinho.", sugestoes

    if "cadastr" in msg or "produto" in msg:
        return "Para cadastrar: vá em Produtos → Novo Produto. Preencha SKU, categoria, fornecedor e validade.", sugestoes

    if "olá" in msg or "ola" in msg or "oi" in msg:
        return f"Olá, {usuario.nome_completo.split()[0]}! Sou a MorangIA, assistente do almoxarifado Moranguinho. Como posso ajudar?", sugestoes

    stats = get_dashboard_stats(db)
    return (
        f"MorangIA online. Resumo: {stats['total_produtos']} produtos, "
        f"{stats['estoque_baixo']} em estoque baixo. Pergunte sobre estoque, validade ou movimentações.",
        sugestoes,
    )
