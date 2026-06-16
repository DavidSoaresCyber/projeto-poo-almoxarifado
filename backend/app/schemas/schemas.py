from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models.models import CargoEnum


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: "UsuarioResponse"


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class UsuarioBase(BaseModel):
    nome_completo: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    telefone: Optional[str] = None
    cargo: CargoEnum = CargoEnum.FUNCIONARIO
    foto_perfil: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6)
    confirmar_senha: str

    @field_validator("confirmar_senha")
    @classmethod
    def senhas_iguais(cls, v, info):
        if "senha" in info.data and v != info.data["senha"]:
            raise ValueError("As senhas não coincidem")
        return v


class UsuarioUpdate(BaseModel):
    nome_completo: Optional[str] = None
    telefone: Optional[str] = None
    cargo: Optional[CargoEnum] = None
    foto_perfil: Optional[str] = None
    ativo: Optional[bool] = None


class UsuarioResponse(BaseModel):
    id: int
    nome_completo: str
    email: str
    telefone: Optional[str]
    cargo: CargoEnum
    foto_perfil: Optional[str]
    ativo: bool
    ultimo_acesso: Optional[datetime]
    permissoes: List[str] = []
    nivel_acesso: int = 0
    status: str = "online"

    class Config:
        from_attributes = True


class CategoriaCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None


class CategoriaResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]

    class Config:
        from_attributes = True


class FornecedorCreate(BaseModel):
    nome: str
    cnpj: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None


class FornecedorResponse(BaseModel):
    id: int
    nome: str
    cnpj: str
    email: Optional[str]
    telefone: Optional[str]
    endereco: Optional[str]
    ativo: bool

    class Config:
        from_attributes = True


class ProdutoCreate(BaseModel):
    nome: str
    sku: str
    codigo_interno: Optional[str] = None
    codigo_barras: Optional[str] = None
    categoria_id: Optional[int] = None
    fornecedor_id: Optional[int] = None
    quantidade: int = 0
    quantidade_minima: int = 10
    preco: float = 0.0
    validade: Optional[datetime] = None


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    sku: Optional[str] = None
    codigo_interno: Optional[str] = None
    codigo_barras: Optional[str] = None
    categoria_id: Optional[int] = None
    fornecedor_id: Optional[int] = None
    quantidade_minima: Optional[int] = None
    preco: Optional[float] = None
    validade: Optional[datetime] = None
    ativo: Optional[bool] = None


class ProdutoResponse(BaseModel):
    id: int
    nome: str
    sku: str
    codigo_interno: Optional[str]
    codigo_barras: Optional[str]
    categoria_id: Optional[int]
    fornecedor_id: Optional[int]
    quantidade: int
    quantidade_minima: int
    preco: float
    validade: Optional[datetime]
    ativo: bool
    status_validade: Optional[str] = None

    class Config:
        from_attributes = True


class MovimentacaoCreate(BaseModel):
    produto_id: int
    tipo: str
    quantidade: int = Field(..., gt=0)
    observacao: Optional[str] = None


class MovimentacaoResponse(BaseModel):
    id: int
    produto_id: int
    usuario_id: int
    tipo: str
    quantidade: int
    observacao: Optional[str]
    criado_em: datetime
    produto_nome: Optional[str] = None
    usuario_nome: Optional[str] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_produtos: int
    estoque_baixo: int
    produtos_vencendo: int
    produtos_vencidos: int
    total_fornecedores: int
    movimentacoes_hoje: int
    valor_estoque: float
    entradas_recentes: int
    saidas_recentes: int


class NotificacaoResponse(BaseModel):
    id: int
    titulo: str
    mensagem: str
    tipo: str
    lida: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    mensagem: str


class ChatResponse(BaseModel):
    resposta: str
    sugestoes: List[str] = []
