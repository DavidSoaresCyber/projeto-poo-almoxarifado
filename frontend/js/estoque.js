if (!hasPermission('estoque')) { window.location.href = 'dashboard.html'; }

let produtos = [];

document.addEventListener('DOMContentLoaded', () => {
  initApp('estoque.html', load);
});

async function load() {
  const stats = await api.dashboard();
  document.getElementById('estoque-stats').innerHTML = `
    <div class="stat-card"><div class="stat-label">Total</div><div class="stat-value">${stats.total_produtos}</div></div>
    <div class="stat-card accent-danger"><div class="stat-label">Estoque baixo</div><div class="stat-value">${stats.estoque_baixo}</div></div>
    <div class="stat-card accent-warning"><div class="stat-label">Vencendo</div><div class="stat-value">${stats.produtos_vencendo}</div></div>
    <div class="stat-card accent-danger"><div class="stat-label">Vencidos</div><div class="stat-value">${stats.produtos_vencidos}</div></div>`;

  produtos = await api.produtos();
  document.getElementById('estoque-tbody').innerHTML = produtos.map(p => {
    const baixo = p.quantidade <= p.quantidade_minima;
    return `<tr${baixo ? ' style="background:rgba(220,38,38,0.04)"' : ''}>
      <td class="td-strong">${p.nome}</td><td>${p.sku}</td>
      <td><strong>${p.quantidade}</strong></td><td>${p.quantidade_minima}</td>
      <td>${baixo ? '<span class="badge badge-danger">Baixo</span>' : '<span class="badge badge-success">OK</span>'}</td>
      <td>${getValidadeBadge(p.status_validade)}</td></tr>`;
  }).join('') || '<tr class="empty-row"><td colspan="6">Nenhum produto</td></tr>';
}

function abrirMov() {
  if (!produtos.length) { showToast('Cadastre produtos primeiro', 'error'); return; }
  createModal('mov-modal', 'Registrar movimentação', `
    <div class="form-group"><label>Produto</label><select id="m-prod" class="form-control">${produtos.map(p => `<option value="${p.id}">${p.nome} (${p.quantidade} un.)</option>`).join('')}</select></div>
    <div class="form-group"><label>Tipo</label><select id="m-tipo" class="form-control"><option value="entrada">Entrada</option><option value="saida">Saída</option></select></div>
    <div class="form-group"><label>Quantidade</label><input type="number" id="m-qtd" class="form-control" min="1" value="1"></div>
    <div class="form-group"><label>Observação</label><input id="m-obs" class="form-control" placeholder="Opcional"></div>`,
    `<button class="btn btn-secondary btn-sm" onclick="closeModal('mov-modal')">Cancelar</button>
     <button class="btn btn-primary btn-sm" id="save-mov">Registrar</button>`);
  openModal('mov-modal');
  document.getElementById('save-mov').onclick = async () => {
    try {
      await api.criarMovimentacao({
        produto_id: +document.getElementById('m-prod').value,
        tipo: document.getElementById('m-tipo').value,
        quantidade: +document.getElementById('m-qtd').value,
        observacao: document.getElementById('m-obs').value.trim() || null,
      });
      closeModal('mov-modal');
      showToast('Movimentação registrada', 'success');
      load();
    } catch (e) { showToast(e.message, 'error'); }
  };
}

window.abrirMov = abrirMov;
