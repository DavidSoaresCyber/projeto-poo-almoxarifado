# Jambinho Stock Manager

Sistema web profissional de almoxarifado do **Supermercado Moranguinho**.

## Início Rápido

### Linux / macOS

```bash
cd moranguinho-stock-manager/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # se ainda não existir
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Windows

```bash
cd moranguinho-stock-manager\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: **http://localhost:8000**

## Ambiente virtual

O `venv` fica dentro de `backend/venv/` junto com o projeto. O arquivo `requirements.txt` na raiz e em `backend/` lista todas as dependências instaladas no ambiente.

Para recriar o ambiente do zero:

```bash
cd backend
rm -rf venv          # Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Credenciais de Demonstração

| Email | Senha | Cargo |
|-------|-------|-------|
| admin@moranguinho.com.br | admin123 | Administrador |
| gerente@moranguinho.com.br | gerente123 | Gerente |
| estoquista@moranguinho.com.br | estoque123 | Estoquista |

## Funcionalidades

- JWT Authentication com 7 níveis de cargo
- Identificação visual de funcionários (nome, cargo, foto, status online)
- Dashboard com Chart.js e estatísticas em tempo real
- Produtos, estoque, fornecedores, movimentações
- MorangIA — assistente inteligente integrada
- Relatórios CSV/PDF/Excel
- Notificações automáticas de estoque baixo e validade
- Scanner de código de barras
- Logs de auditoria e backup

## Estrutura

```
moranguinho-stock-manager/
├── backend/
│   ├── venv/           # Ambiente virtual Python
│   ├── requirements.txt
│   ├── main.py
│   └── app/
├── frontend/           # HTML + CSS + JavaScript
├── requirements.txt    # Aponta para backend/requirements.txt
└── README.md
```

## API Docs

http://localhost:8000/api/docs

## Tecnologias

Python · FastAPI · SQLAlchemy · JWT · SQLite/PostgreSQL · HTML5 · CSS3 · Chart.js

---

Supermercado Moranguinho © 2026
