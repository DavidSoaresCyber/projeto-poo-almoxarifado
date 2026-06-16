import re
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    Produto, Movimentacao, Fornecedor, Categoria,
    ConversaIA, TipoMovimentacao, CargoEnum
)
from app.security.auth import user_has_permission


class MorangIAService:
    """Assistente inteligente do almoxarifado Moranguinho."""

    SUGESTOES_PADRAO = [
        "Quantos produtos estão com estoque baixo?",
        "Produtos vencendo esta semana",
        "Mostrar movimentações de hoje",
        "Qual fornecedor entrega arroz?",
        "Produtos mais movimentados",
        "Como cadastrar um produto?",
    ]

    def __init__(self, db: Session, usuario):
        self.db = db
        self.usuario = usuario

    def processar(self, mensagem: str) -> dict:
        msg = mensagem.lower().strip()
        resposta = self._responder(msg)
        sugestoes = self._sugestoes_contextuais(msg)

        log = ConversaIA(
            usuario_id=self.usuario.id,
            mensagem=mensagem,
            resposta=resposta,
        )
        self.db.add(log)
        self.db.commit()

        return {"resposta": resposta, "sugestoes": sugestoes}

    def _responder(self, msg: str) -> str:
        cargo = self.usuario.cargo.value

        if any(w in msg for w in ["olá", "ola", "oi", "bom dia", "boa tarde", "boa noite"]):
            return (
                f"Bem-vindo, {self.usuario.nome_completo.split()[0]}! "
                f"Sou a MorangIA, assistente do almoxarifado Moranguinho. "
                f"Como {cargo}, posso ajudá-lo com estoque, movimentações e relatórios."
            )

        if any(w in msg for w in ["estoque baixo", "falta", "acabando", "reposição", "reposicao"]):
            if not user_has_permission(self.usuario, "estoque") and not user_has_permission(self.usuario, "dashboard"):
                return "Seu cargo não possui permissão para consultar dados de estoque detalhados."
            produtos = self.db.query(Produto).filter(
                Produto.ativo == True,
                Produto.quantidade <= Produto.quantidade_minima
            ).all()
            if not produtos:
                return "Ótima notícia! Nenhum produto está com estoque baixo no momento."
            lista = "\n".join([f"• {p.nome} — {p.quantidade} un. (mín: {p.quantidade_minima})" for p in produtos[:10]])
            extra = f"\n\n... e mais {len(produtos)-10} produtos." if len(produtos) > 10 else ""
            return f"Encontrei {len(produtos)} produto(s) com estoque baixo:\n\n{lista}{extra}"

        if any(w in msg for w in ["vencendo", "validade", "vencido", "vence"]):
            if not user_has_permission(self.usuario, "produtos"):
                return "Consulta de validade disponível para cargos com acesso a produtos."
            limite = datetime.utcnow() + timedelta(days=7)
            produtos = self.db.query(Produto).filter(
                Produto.ativo == True,
                Produto.validade != None,
                Produto.validade <= limite
            ).order_by(Produto.validade).all()
            if not produtos:
                return "Nenhum produto com validade crítica nos próximos 7 dias."
            lista = "\n".join([
                f"• {p.nome} — vence {p.validade.strftime('%d/%m/%Y')} ({p.quantidade} un.)"
                for p in produtos[:10]
            ])
            return f"Produtos com validade próxima:\n\n{lista}"

        if any(w in msg for w in ["movimentação", "movimentacao", "movimentações", "hoje"]):
            if not user_has_permission(self.usuario, "movimentacoes"):
                return "Seu cargo não possui acesso ao módulo de movimentações."
            hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            movs = self.db.query(Movimentacao).filter(Movimentacao.criado_em >= hoje).order_by(Movimentacao.criado_em.desc()).limit(15).all()
            if not movs:
                return "Nenhuma movimentação registrada hoje."
            lista = "\n".join([
                f"• [{m.tipo.value.upper()}] {m.produto.nome if m.produto else 'N/A'} — {m.quantidade} un. às {m.criado_em.strftime('%H:%M')}"
                for m in movs
            ])
            return f"Movimentações de hoje ({len(movs)}):\n\n{lista}"

        if "fornecedor" in msg:
            if not user_has_permission(self.usuario, "fornecedores"):
                return "Consulta de fornecedores restrita ao seu nível de acesso."
            termo = self._extrair_termo_produto(msg)
            if termo:
                produtos = self.db.query(Produto).join(Fornecedor).filter(
                    Produto.nome.ilike(f"%{termo}%")
                ).all()
                if produtos:
                    info = []
                    for p in produtos[:5]:
                        fn = p.fornecedor.nome if p.fornecedor else "Sem fornecedor"
                        info.append(f"• {p.nome} → {fn}")
                    return "Fornecedores encontrados:\n\n" + "\n".join(info)
            fornecedores = self.db.query(Fornecedor).filter(Fornecedor.ativo == True).limit(10).all()
            lista = "\n".join([f"• {f.nome} — CNPJ: {f.cnpj}" for f in fornecedores])
            return f"Fornecedores cadastrados:\n\n{lista}"

        if any(w in msg for w in ["mais vendido", "mais movimentado", "popular", "ranking"]):
            if not user_has_permission(self.usuario, "relatorios"):
                return "Relatórios de ranking disponíveis para Gerente ou superior."
            result = self.db.query(
                Produto.nome,
                func.sum(Movimentacao.quantidade).label("total")
            ).join(Movimentacao).filter(
                Movimentacao.tipo == TipoMovimentacao.SAIDA
            ).group_by(Produto.id).order_by(func.sum(Movimentacao.quantidade).desc()).limit(5).all()
            if not result:
                return "Ainda não há dados suficientes para ranking de saídas."
            lista = "\n".join([f"{i+1}. {r.nome} — {int(r.total)} unidades" for i, r in enumerate(result)])
            return f"Produtos com mais saídas:\n\n{lista}"

        if any(w in msg for w in ["relatório", "relatorio", "resumo"]):
            if not user_has_permission(self.usuario, "relatorios"):
                return "Geração de relatórios requer permissão de Gerente ou Administrador."
            total = self.db.query(Produto).filter(Produto.ativo == True).count()
            baixo = self.db.query(Produto).filter(Produto.quantidade <= Produto.quantidade_minima).count()
            hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            movs = self.db.query(Movimentacao).filter(Movimentacao.criado_em >= hoje).count()
            return (
                f"📊 Resumo operacional — {datetime.utcnow().strftime('%d/%m/%Y')}\n\n"
                f"• Total de produtos ativos: {total}\n"
                f"• Produtos com estoque baixo: {baixo}\n"
                f"• Movimentações hoje: {movs}\n"
                f"• Responsável: {self.usuario.nome_completo} ({cargo})\n\n"
                f"Acesse Relatórios para exportar PDF ou Excel."
            )

        if any(w in msg for w in ["cadastrar", "como usar", "ajuda", "help", "tutorial"]):
            return (
                "Posso ajudá-lo com:\n\n"
                "• Consultar estoque baixo e validades\n"
                "• Ver movimentações do dia\n"
                "• Identificar fornecedores\n"
                "• Gerar resumos operacionais\n"
                "• Explicar módulos do sistema\n\n"
                "Módulos disponíveis:\n"
                "→ Produtos: cadastro com SKU, categoria e validade\n"
                "→ Estoque: entradas e saídas com controle automático\n"
                "→ Fornecedores: gestão completa de parceiros\n"
                "→ Relatórios: exportação PDF e Excel\n\n"
                "Pergunte algo específico, como 'estoque baixo' ou 'movimentações de hoje'."
            )

        if any(w in msg for w in ["categoria", "sugerir categoria"]):
            categorias = self.db.query(Categoria).all()
            nomes = [c.nome for c in categorias]
            return f"Categorias disponíveis: {', '.join(nomes) if nomes else 'Nenhuma cadastrada'}."

        if "duplic" in msg:
            return "Para verificar duplicações, informe o SKU ou nome do produto na tela de Produtos e use o filtro de busca."

        return (
            "Não identifiquei sua solicitação. Tente perguntar sobre:\n"
            "• estoque baixo\n• produtos vencendo\n• movimentações de hoje\n"
            "• fornecedor de [produto]\n• relatório do dia\n• ajuda"
        )

    def _extrair_termo_produto(self, msg: str) -> str | None:
        patterns = [r"fornecedor (?:do|de|da|entrega) (\w+)", r"entrega (\w+)", r"(\w+) fornecedor"]
        for p in patterns:
            m = re.search(p, msg)
            if m:
                return m.group(1)
        return None

    def _sugestoes_contextuais(self, msg: str) -> list[str]:
        if "estoque" in msg:
            return ["Produtos vencendo esta semana", "Relatório do dia", "Como fazer entrada de estoque?"]
        if "fornecedor" in msg:
            return ["Listar todos fornecedores", "Estoque baixo", "Movimentações de hoje"]
        return self.SUGESTOES_PADRAO[:4]
