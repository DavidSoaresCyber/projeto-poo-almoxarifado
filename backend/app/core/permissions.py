"""Definição de cargos e permissões do Supermercado Moranguinho."""

CARGOS = [
    "Administrador",
    "Gerente",
    "Subgerente",
    "Supervisor",
    "Estoquista",
    "Funcionário",
    "Operador de Caixa",
]

# nível hierárquico (maior = mais acesso)
CARGO_NIVEL = {
    "Administrador": 100,
    "Gerente": 80,
    "Subgerente": 70,
    "Supervisor": 60,
    "Estoquista": 50,
    "Funcionário": 30,
    "Operador de Caixa": 20,
}

# páginas do sistema
PAGINAS = [
    "dashboard",
    "produtos",
    "estoque",
    "fornecedores",
    "movimentacoes",
    "relatorios",
    "usuarios",
    "auditoria",
    "backup",
]

PERMISSOES_POR_CARGO = {
    "Administrador": PAGINAS,
    "Gerente": ["dashboard", "produtos", "estoque", "fornecedores", "movimentacoes", "relatorios"],
    "Subgerente": ["dashboard", "produtos", "estoque", "fornecedores", "movimentacoes", "relatorios"],
    "Supervisor": ["dashboard", "produtos", "estoque", "movimentacoes", "relatorios"],
    "Estoquista": ["dashboard", "produtos", "estoque", "movimentacoes"],
    "Funcionário": ["dashboard", "movimentacoes"],
    "Operador de Caixa": ["dashboard", "movimentacoes"],
}


def get_permissoes(cargo: str) -> list[str]:
    return PERMISSOES_POR_CARGO.get(cargo, ["dashboard"])


def get_nivel(cargo: str) -> int:
    return CARGO_NIVEL.get(cargo, 0)


def pode_acessar(cargo: str, pagina: str) -> bool:
    return pagina in get_permissoes(cargo)
