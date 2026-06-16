from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.models import (
    Usuario, Produto, Fornecedor, Categoria, Movimentacao,
    CargoEnum, Permissao
)
from app.security.auth import hash_password


def seed_database(db: Session):
    if db.query(Usuario).first():
        return

    admin = Usuario(
        nome_completo="Carlos Henrique Silva",
        email="admin@moranguinho.com.br",
        telefone="(11) 98765-4321",
        cargo=CargoEnum.ADMINISTRADOR,
        senha_hash=hash_password("admin123"),
        foto_perfil=None,
        ultimo_acesso=datetime.utcnow(),
    )
    gerente = Usuario(
        nome_completo="Ana Paula Mendes",
        email="gerente@moranguinho.com.br",
        telefone="(11) 91234-5678",
        cargo=CargoEnum.GERENTE,
        senha_hash=hash_password("gerente123"),
    )
    estoquista = Usuario(
        nome_completo="João Pedro Santos",
        email="estoquista@moranguinho.com.br",
        telefone="(11) 99876-5432",
        cargo=CargoEnum.ESTOQUISTA,
        senha_hash=hash_password("estoque123"),
    )
    db.add_all([admin, gerente, estoquista])

    categorias = [
        Categoria(nome="Grãos e Cereais", descricao="Arroz, feijão, farinhas"),
        Categoria(nome="Bebidas", descricao="Refrigerantes, sucos, água"),
        Categoria(nome="Limpeza", descricao="Produtos de limpeza doméstica"),
        Categoria(nome="Hortifruti", descricao="Frutas, verduras e legumes"),
        Categoria(nome="Laticínios", descricao="Leite, queijos, iogurtes"),
    ]
    db.add_all(categorias)
    db.flush()

    fornecedores = [
        Fornecedor(nome="Distribuidora Alimentos Brasil", cnpj="12.345.678/0001-90",
                   email="contato@alimentosbrasil.com", telefone="(11) 3333-4444",
                   endereco="Av. Industrial, 1500 - São Paulo/SP"),
        Fornecedor(nome="Bebidas Premium Ltda", cnpj="98.765.432/0001-10",
                   email="vendas@bebidaspremium.com", telefone="(11) 5555-6666",
                   endereco="Rua das Indústrias, 800 - Guarulhos/SP"),
        Fornecedor(nome="Hortifruti Verde Vida", cnpj="11.222.333/0001-44",
                   email="pedidos@verdevida.com", telefone="(11) 7777-8888",
                   endereco="CEASA - Box 42 - São Paulo/SP"),
    ]
    db.add_all(fornecedores)
    db.flush()

    hoje = datetime.utcnow()
    produtos = [
        Produto(nome="Arroz Tipo 1 5kg", sku="ARZ-001", codigo_interno="INT-001",
                codigo_barras="7891234567890", categoria_id=categorias[0].id,
                fornecedor_id=fornecedores[0].id, quantidade=150, quantidade_minima=30,
                preco=22.90, validade=hoje + timedelta(days=365)),
        Produto(nome="Feijão Carioca 1kg", sku="FEJ-001", codigo_interno="INT-002",
                codigo_barras="7891234567891", categoria_id=categorias[0].id,
                fornecedor_id=fornecedores[0].id, quantidade=8, quantidade_minima=20,
                preco=8.50, validade=hoje + timedelta(days=180)),
        Produto(nome="Refrigerante Cola 2L", sku="BEB-001", codigo_interno="INT-003",
                codigo_barras="7891234567892", categoria_id=categorias[1].id,
                fornecedor_id=fornecedores[1].id, quantidade=80, quantidade_minima=25,
                preco=7.99, validade=hoje + timedelta(days=120)),
        Produto(nome="Detergente Líquido 500ml", sku="LIM-001", codigo_interno="INT-004",
                codigo_barras="7891234567893", categoria_id=categorias[2].id,
                fornecedor_id=fornecedores[0].id, quantidade=45, quantidade_minima=15,
                preco=2.49, validade=hoje + timedelta(days=730)),
        Produto(nome="Banana Prata kg", sku="HOR-001", codigo_interno="INT-005",
                categoria_id=categorias[3].id, fornecedor_id=fornecedores[2].id,
                quantidade=25, quantidade_minima=10, preco=5.99,
                validade=hoje + timedelta(days=5)),
        Produto(nome="Leite Integral 1L", sku="LAT-001", codigo_interno="INT-006",
                codigo_barras="7891234567894", categoria_id=categorias[4].id,
                fornecedor_id=fornecedores[0].id, quantidade=5, quantidade_minima=20,
                preco=4.89, validade=hoje + timedelta(days=3)),
    ]
    db.add_all(produtos)
    db.flush()

    movs = [
        Movimentacao(produto_id=produtos[0].id, usuario_id=1, tipo="entrada", quantidade=50,
                     observacao="Reposição semanal"),
        Movimentacao(produto_id=produtos[2].id, usuario_id=2, tipo="saida", quantidade=10,
                     observacao="Abastecimento loja"),
        Movimentacao(produto_id=produtos[4].id, usuario_id=3, tipo="entrada", quantidade=15,
                     observacao="Entrega hortifruti"),
    ]
    db.add_all(movs)

    for cargo in CargoEnum:
        for modulo in ["dashboard", "produtos", "estoque", "fornecedores", "movimentacoes", "relatorios", "usuarios", "morangia"]:
            db.add(Permissao(cargo=cargo, modulo=modulo, pode_ler=True, pode_escrever=cargo == CargoEnum.ADMINISTRADOR))

    db.commit()
