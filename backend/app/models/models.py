from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum

from app.database.connection import Base


class CargoEnum(str, enum.Enum):
    ADMINISTRADOR = "Administrador"
    GERENTE = "Gerente"
    SUBGERENTE = "Subgerente"
    SUPERVISOR = "Supervisor"
    ESTOQUISTA = "Estoquista"
    FUNCIONARIO = "Funcionário"
    OPERADOR_CAIXA = "Operador de Caixa"


CARGO_NIVEL = {
    CargoEnum.ADMINISTRADOR: 100,
    CargoEnum.GERENTE: 80,
    CargoEnum.SUBGERENTE: 70,
    CargoEnum.SUPERVISOR: 60,
    CargoEnum.ESTOQUISTA: 50,
    CargoEnum.FUNCIONARIO: 30,
    CargoEnum.OPERADOR_CAIXA: 20,
}

CARGO_PERMISSOES = {
    CargoEnum.ADMINISTRADOR: ["*"],
    CargoEnum.GERENTE: ["dashboard", "produtos", "estoque", "fornecedores", "movimentacoes", "relatorios", "morangia"],
    CargoEnum.SUBGERENTE: ["dashboard", "produtos", "estoque", "fornecedores", "movimentacoes", "relatorios", "morangia"],
    CargoEnum.SUPERVISOR: ["dashboard", "produtos", "estoque", "movimentacoes", "relatorios", "morangia"],
    CargoEnum.ESTOQUISTA: ["dashboard", "produtos", "estoque", "movimentacoes", "morangia"],
    CargoEnum.FUNCIONARIO: ["dashboard", "movimentacoes", "morangia"],
    CargoEnum.OPERADOR_CAIXA: ["dashboard", "movimentacoes"],
}


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(150), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    telefone = Column(String(20), nullable=True)
    senha_hash = Column(String(255), nullable=False)
    cargo = Column(SAEnum(CargoEnum), nullable=False, default=CargoEnum.FUNCIONARIO)
    foto_perfil = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    ultimo_acesso = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    movimentacoes = relationship("Movimentacao", back_populates="usuario")
    logs = relationship("LogAtividade", back_populates="usuario")
    notificacoes = relationship("Notificacao", back_populates="usuario")
    conversas_ia = relationship("ConversaIA", back_populates="usuario")


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produtos = relationship("Produto", back_populates="categoria")


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    email = Column(String(120), nullable=True)
    telefone = Column(String(20), nullable=True)
    endereco = Column(String(255), nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    produtos = relationship("Produto", back_populates="fornecedor")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    codigo_interno = Column(String(50), nullable=True)
    codigo_barras = Column(String(50), nullable=True, index=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"), nullable=True)
    quantidade = Column(Integer, default=0)
    quantidade_minima = Column(Integer, default=10)
    preco = Column(Float, default=0.0)
    validade = Column(DateTime, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categoria = relationship("Categoria", back_populates="produtos")
    fornecedor = relationship("Fornecedor", back_populates="produtos")
    movimentacoes = relationship("Movimentacao", back_populates="produto")


class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # entrada, saida
    quantidade = Column(Integer, nullable=False)
    observacao = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)

    produto = relationship("Produto", back_populates="movimentacoes")
    usuario = relationship("Usuario", back_populates="movimentacoes")


class Relatorio(Base):
    __tablename__ = "relatorios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False)
    tipo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    arquivo = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class Auditoria(Base):
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tabela = Column(String(50), nullable=False)
    registro_id = Column(Integer, nullable=False)
    acao = Column(String(20), nullable=False)
    dados_antes = Column(Text, nullable=True)
    dados_depois = Column(Text, nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)


class LogAtividade(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String(100), nullable=False)
    detalhes = Column(Text, nullable=True)
    ip = Column(String(45), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)

    usuario = relationship("Usuario", back_populates="logs")


class Notificacao(Base):
    __tablename__ = "notificacoes"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    titulo = Column(String(150), nullable=False)
    mensagem = Column(Text, nullable=False)
    tipo = Column(String(30), default="info")
    lida = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="notificacoes")


class Permissao(Base):
    __tablename__ = "permissoes"

    id = Column(Integer, primary_key=True, index=True)
    cargo = Column(SAEnum(CargoEnum), nullable=False)
    modulo = Column(String(50), nullable=False)
    pode_ler = Column(Boolean, default=True)
    pode_escrever = Column(Boolean, default=False)
    pode_excluir = Column(Boolean, default=False)


class ConversaIA(Base):
    __tablename__ = "conversas_ia"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensagem = Column(Text, nullable=False)
    resposta = Column(Text, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="conversas_ia")
