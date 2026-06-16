import io
import json
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app.database.connection import get_db
from app.models.models import Produto, Movimentacao, Fornecedor, Usuario
from app.security.auth import require_permission
from app.services.services import registrar_log

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/estoque/pdf")
def relatorio_estoque_pdf(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("relatorios"))):
    produtos = db.query(Produto).filter(Produto.ativo == True).order_by(Produto.nome).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("<b>Moranguinho Stock Manager</b>", styles["Title"]),
        Paragraph(f"Relatório de Estoque — {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    data = [["Produto", "SKU", "Qtd", "Mín", "Preço", "Validade"]]
    for p in produtos:
        val = p.validade.strftime("%d/%m/%Y") if p.validade else "-"
        data.append([p.nome[:30], p.sku, str(p.quantidade), str(p.quantidade_minima), f"R$ {p.preco:.2f}", val])

    table = Table(data, colWidths=[6 * cm, 3 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff1f1f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    registrar_log(db, user.id, "Relatório PDF gerado", "relatorios")
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=relatorio_estoque.pdf"})


@router.get("/estoque/excel")
def relatorio_estoque_excel(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("relatorios"))):
    produtos = db.query(Produto).filter(Produto.ativo == True).order_by(Produto.nome).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Estoque"
    ws.append(["Produto", "SKU", "Código Barras", "Quantidade", "Mínimo", "Preço", "Validade", "Categoria"])
    for p in produtos:
        ws.append([
            p.nome, p.sku, p.codigo_barras or "",
            p.quantidade, p.quantidade_minima, p.preco,
            p.validade.strftime("%d/%m/%Y") if p.validade else "",
            p.categoria.nome if p.categoria else "",
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    registrar_log(db, user.id, "Relatório Excel gerado", "relatorios")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=relatorio_estoque.xlsx"},
    )


@router.get("/movimentacoes/excel")
def relatorio_movimentacoes_excel(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("relatorios"))):
    movs = db.query(Movimentacao).order_by(Movimentacao.criado_em.desc()).limit(500).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimentações"
    ws.append(["Data", "Tipo", "Produto", "Quantidade", "Usuário", "Observação"])
    for m in movs:
        ws.append([
            m.criado_em.strftime("%d/%m/%Y %H:%M"),
            m.tipo,
            m.produto.nome if m.produto else "",
            m.quantidade,
            m.usuario.nome_completo if m.usuario else "",
            m.observacao or "",
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=movimentacoes.xlsx"},
    )


@router.post("/backup")
def gerar_backup(db: Session = Depends(get_db), user: Usuario = Depends(require_permission("relatorios"))):
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"

    data = {
        "gerado_em": datetime.utcnow().isoformat(),
        "produtos": [{"id": p.id, "nome": p.nome, "sku": p.sku, "quantidade": p.quantidade} for p in db.query(Produto).all()],
        "fornecedores": [{"id": f.id, "nome": f.nome, "cnpj": f.cnpj} for f in db.query(Fornecedor).all()],
        "movimentacoes": db.query(Movimentacao).count(),
    }
    backup_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    registrar_log(db, user.id, f"Backup gerado: {backup_file.name}", "backup")
    return {"message": "Backup gerado", "arquivo": str(backup_file)}
