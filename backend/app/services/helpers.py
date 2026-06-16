from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    LogAtividade, Produto, Movimentacao, Notificacao,
    TipoMovimentacao, StatusValidade
)


def registrar_log(db: Session, usuario_id: int | None, acao: str, modulo: str = "", detalhes: str = "", ip: str = ""):
    log = LogAtividade(
        usuario_id=usuario_id,
        acao=acao,
        modulo=modulo,
        detalhes=detalhes,
        ip=ip,
    )
    db.add(log)
    db.commit()


def calcular_status_validade(validade: datetime | None) -> str:
    if not validade:
        return StatusValidade.OK.value
    hoje = datetime.utcnow()
    if validade < hoje:
        return StatusValidade.VENCIDO.value
    dias = (validade - hoje).days
    if dias <= 7:
        return StatusValidade.CRITICO.value
    if dias <= 30:
        return StatusValidade.ALERTA.value
    return StatusValidade.OK.value


def criar_notificacao(db: Session, titulo: str, mensagem: str, tipo: str = "info", usuario_id: int | None = None):
    notif = Notificacao(usuario_id=usuario_id, titulo=titulo, mensagem=mensagem, tipo=tipo)
    db.add(notif)
    db.commit()


def verificar_alertas_estoque(db: Session):
    produtos_baixo = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.quantidade <= Produto.quantidade_minima
    ).all()

    for p in produtos_baixo:
        existe = db.query(Notificacao).filter(
            Notificacao.titulo == f"Estoque baixo: {p.nome}",
            Notificacao.lida == False
        ).first()
        if not existe:
            criar_notificacao(
                db,
                f"Estoque baixo: {p.nome}",
                f"Produto {p.nome} (SKU: {p.sku}) com apenas {p.quantidade} unidades.",
                "warning",
            )

    limite = datetime.utcnow() + timedelta(days=30)
    produtos_vencendo = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.validade != None,
        Produto.validade <= limite,
        Produto.validade >= datetime.utcnow()
    ).all()

    for p in produtos_vencendo:
        existe = db.query(Notificacao).filter(
            Notificacao.titulo == f"Validade próxima: {p.nome}",
            Notificacao.lida == False
        ).first()
        if not existe:
            criar_notificacao(
                db,
                f"Validade próxima: {p.nome}",
                f"Produto {p.nome} vence em {p.validade.strftime('%d/%m/%Y')}.",
                "danger",
            )


def get_dashboard_stats(db: Session) -> dict:
    hoje_inicio = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_produtos = db.query(Produto).filter(Produto.ativo == True).count()
    estoque_baixo = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.quantidade <= Produto.quantidade_minima
    ).count()

    limite_vencendo = datetime.utcnow() + timedelta(days=30)
    produtos_vencendo = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.validade != None,
        Produto.validade <= limite_vencendo,
        Produto.validade >= datetime.utcnow()
    ).count()

    produtos_vencidos = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.validade != None,
        Produto.validade < datetime.utcnow()
    ).count()

    from app.models.models import Fornecedor
    total_fornecedores = db.query(Fornecedor).filter(Fornecedor.ativo == True).count()

    movimentacoes_hoje = db.query(Movimentacao).filter(Movimentacao.criado_em >= hoje_inicio).count()
    entradas_hoje = db.query(Movimentacao).filter(
        Movimentacao.criado_em >= hoje_inicio,
        Movimentacao.tipo == TipoMovimentacao.ENTRADA
    ).count()
    saidas_hoje = db.query(Movimentacao).filter(
        Movimentacao.criado_em >= hoje_inicio,
        Movimentacao.tipo == TipoMovimentacao.SAIDA
    ).count()

    valor_estoque = db.query(func.sum(Produto.quantidade * Produto.preco)).filter(Produto.ativo == True).scalar() or 0

    logs = db.query(LogAtividade).order_by(LogAtividade.criado_em.desc()).limit(10).all()
    atividades = []
    for log in logs:
        atividades.append({
            "acao": log.acao,
            "modulo": log.modulo,
            "detalhes": log.detalhes,
            "criado_em": log.criado_em.isoformat() if log.criado_em else None,
            "usuario": log.usuario.nome_completo if log.usuario else "Sistema",
        })

    return {
        "total_produtos": total_produtos,
        "estoque_baixo": estoque_baixo,
        "produtos_vencendo": produtos_vencendo,
        "produtos_vencidos": produtos_vencidos,
        "total_fornecedores": total_fornecedores,
        "movimentacoes_hoje": movimentacoes_hoje,
        "entradas_hoje": entradas_hoje,
        "saidas_hoje": saidas_hoje,
        "valor_estoque": round(float(valor_estoque), 2),
        "atividades_recentes": atividades,
    }
