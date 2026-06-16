from datetime import datetime, timedelta
from app.database.connection import SessionLocal, engine, Base
from app.models.models import (
    Usuario, Categoria, Fornecedor, Produto, Movimentacao,
    Permissao, CargoEnum, TipoMovimentacao, CARGO_PERMISSOES
)
from app.security.auth import hash_password


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Usuario).first():
        db.close()
        return

    # Admin padrão
    admin = Usuario(
        nome_completo="Carlos Henrique Silva",
        email="admin@moranguinho.com",
        telefone="(11) 99999-0001",
        senha_hash=hash_password("admin123"),
        cargo=CargoEnum.ADMINISTRADOR,
        foto_perfil=None,
        ultimo_acesso=datetime.utcnow(),
    )
    gerente = Usuario(
        nome_completo="Ana Paula Mendes",
        email="gerente@moranguinho.com",
        telefone="(11) 99999-0002",
        senha_hash=hash_password("gerente123"),
        cargo=CargoEnum.GERENTE,
        ultimo_acesso=datetime.utcnow(),
    )
    estoquista = Usuario(
        nome_completo="Roberto Lima",
        email="estoquista@moranguinho.com",
        telefone="(11) 99999-0003",
        senha_hash=hash_password("estoquista123"),
        cargo=CargoEnum.ESTOQUISTA,
        ultimo_acesso=datetime.utcnow(),
    )
    db.add_all([admin, gerente, estoquista])
    db.commit()

    categorias = [
        Categoria(nome="Grãos e Cereais", descricao="Arroz, feijão, farinhas"),
        Categoria(nome="Bebidas", descricao="Refrigerantes, sucos, água"),
        Categoria(nome="Laticínios", descricao="Leite, queijos, iogurtes"),
        Categoria(nome="Hortifruti", descricao="Frutas e verduras"),
        Categoria(nome="Limpeza", descricao="Produtos de limpeza doméstica"),
        Categoria(nome="Padaria", descricao="Pães e confeitaria"),
    ]
    db.add_all(categorias)
    db.commit()

    fornecedores = [
        Fornecedor(nome="Distribuidora Campos Ltda", cnpj="12.345.678/0001-90", email="contato@campos.com", telefone="(11) 3456-7890", endereco="Rua das Indústrias, 500 — São Paulo/SP"),
        Fornecedor(nome="Alimentos Brasil S.A.", cnpj="98.765.432/0001-10", email="vendas@alimentosbrasil.com", telefone="(11) 2345-6789", endereco="Av. Paulista, 1200 — São Paulo/SP"),
        Fornecedor(nome="Bebidas Premium", cnpj="11.222.333/0001-44", email="premium@bebidas.com", telefone="(11) 4567-8901", endereco="Rod. Anhanguera, km 25 — Osasco/SP"),
    ]
    db.add_all(fornecedores)
    db.commit()

    produtos_data = [
        ("Arroz Tipo 1 5kg", "ARZ-001", "7891000100103", 0, 150, 120, 22.90, 60),
        ("Feijão Carioca 1kg", "FEJ-001", "7891000100202", 0, 80, 50, 8.50, 90),
        ("Leite Integral 1L", "LEI-001", "7891000100301", 2, 200, 100, 4.99, 15),
        ("Refrigerante Cola 2L", "REF-001", "7891000100400", 1, 120, 60, 7.99, 180),
        ("Detergente Líquido 500ml", "DET-001", "7891000100509", 4, 90, 30, 2.49, 365),
        ("Pão Francês (kg)", "PAO-001", "7891000100608", 3, 50, 20, 12.90, 2),
        ("Banana Prata (kg)", "BAN-001", "7891000100707", 3, 40, 15, 5.99, 7),
        ("Queijo Mussarela 500g", "QUE-001", "7891000100806", 2, 60, 25, 18.90, 20),
        ("Açúcar Cristal 1kg", "ACU-001", "7891000100905", 0, 100, 40, 4.29, 120),
        ("Sabão em Pó 1kg", "SAB-001", "7891000101002", 4, 70, 25, 11.90, 300),
    ]

    produtos = []
    for nome, sku, barras, cat_idx, qtd, qtd_min, preco, dias_val in produtos_data:
        p = Produto(
            nome=nome, sku=sku, codigo_barras=barras,
            categoria_id=categorias[cat_idx].id,
            fornecedor_id=fornecedores[cat_idx % 3].id,
            quantidade=qtd, quantidade_minima=qtd_min, preco=preco,
            validade=datetime.utcnow() + timedelta(days=dias_val),
        )
        produtos.append(p)
    db.add_all(produtos)
    db.commit()

    # Movimentações de exemplo
    movs = [
        Movimentacao(produto_id=produtos[0].id, usuario_id=estoquista.id, tipo=TipoMovimentacao.ENTRADA, quantidade=150, quantidade_anterior=0, quantidade_atual=150, observacao="Entrada inicial"),
        Movimentacao(produto_id=produtos[2].id, usuario_id=estoquista.id, tipo=TipoMovimentacao.SAIDA, quantidade=30, quantidade_anterior=200, quantidade_atual=170, observacao="Reposição gôndola"),
    ]
    db.add_all(movs)

    for cargo, modulos in CARGO_PERMISSOES.items():
        if modulos == ["*"]:
            db.add(Permissao(cargo=cargo, modulo="*", pode_ler=True, pode_criar=True, pode_editar=True, pode_excluir=True))
        else:
            for mod in modulos:
                db.add(Permissao(cargo=cargo, modulo=mod, pode_ler=True, pode_criar=True, pode_editar=True, pode_excluir=cargo in [CargoEnum.ADMINISTRADOR, CargoEnum.GERENTE]))

    db.commit()
    db.close()
    print("✓ Banco de dados inicializado com dados de exemplo")
