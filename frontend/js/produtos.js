if (!hasPermission('produtos')) { window.location.href = 'dashboard.html'; }

let categorias = [], fornecedores = [], produtos = [];

document.addEventListener('DOMContentLoaded', () => {
  initApp('produtos.html', init);
});

async function init() {
  [categorias, fornecedores] = await Promise.all([api.categorias(), api.fornecedores()]);
  await carregar();
  document.getElementById('busca').addEventListener('input', e => carregar(e.target.value));
  document.getElementById('barcode-input').addEventListener('keydown', async e => {
    if (e.key !== 'Enter') return;
    try {
      const p = await api.barcode(e.target.value.trim());
      showToast(`Encontrado: ${p.nome}`, 'success');
      document.getElementById('busca').value = p.sku;
      carregar(p.sku);
    } catch { showToast('Produto não encontrado', 'error'); }
  });
}

async function carregar(busca) {
  produtos = await api.produtos(busca || '');
  const tbody = document.getElementById('produtos-tbody');
  if (!produtos.length) {
    tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Nenhum produto encontrado</td></tr>';
    return;
  }
  tbody.innerHTML = produtos.map(p => `
    <tr>
      <td class="td-strong">${p.nome}</td>
      <td>${p.sku}</td>
      <td>${p.quantidade}</td>
      <td>${formatCurrency(p.preco)}</td>
      <td>${p.validade ? new Date(p.validade).toLocaleDateString('pt-BR') : '—'}</td>
      <td>${getValidadeBadge(p.status_validade)}</td>
      <td class="td-actions">
        <button class="btn btn-secondary btn-sm" onclick="editarProduto(${p.id})">Editar</button>
        <button class="btn btn-danger btn-sm" onclick="excluirProduto(${p.id})">Excluir</button>
      </td>
    </tr>`).join('');
}

function abrirModalProduto(prod) {
  const catOpts = categorias.map(c => `<option value="${c.id}" ${prod?.categoria_id == c.id ? 'selected' : ''}>${c.nome}</option>`).join('');
  const fornOpts = fornecedores.map(f => `<option value="${f.id}" ${prod?.fornecedor_id == f.id ? 'selected' : ''}>${f.nome}</option>`).join('');
  createModal('prod-modal', prod ? 'Editar produto' : 'Novo produto', `
    <div class="form-group"><label>Nome</label><input id="p-nome" class="form-control" value="${prod?.nome || ''}"></div>
    <div class="form-group"><label>SKU</label><input id="p-sku" class="form-control" value="${prod?.sku || ''}" ${prod ? 'readonly' : ''}></div>
    <div class="form-group"><label>Código de barras</label><input id="p-barcode" class="form-control" value="${prod?.codigo_barras || ''}"></div>
    <div class="form-group"><label>Categoria</label><select id="p-cat" class="form-control">${catOpts}</select></div>
    <div class="form-group"><label>Fornecedor</label><select id="p-forn" class="form-control">${fornOpts}</select></div>
    <div class="form-group"><label>Quantidade</label><input type="number" id="p-qtd" class="form-control" value="${prod?.quantidade ?? 0}" min="0"></div>
    <div class="form-group"><label>Quantidade mínima</label><input type="number" id="p-min" class="form-control" value="${prod?.quantidade_minima ?? 10}" min="0"></div>
    <div class="form-group"><label>Preço (R$)</label><input type="number" step="0.01" id="p-preco" class="form-control" value="${prod?.preco ?? 0}" min="0"></div>
    <div class="form-group"><label>Validade</label><input type="date" id="p-val" class="form-control" value="${prod?.validade ? prod.validade.split('T')[0] : ''}"></div>`,
    `<button class="btn btn-secondary btn-sm" onclick="closeModal('prod-modal')">Cancelar</button>
     <button class="btn btn-primary btn-sm" id="save-prod">Salvar</button>`);
  openModal('prod-modal');
  document.getElementById('save-prod').onclick = () => salvarProduto(prod?.id);
}

function editarProduto(id) { abrirModalProduto(produtos.find(p => p.id === id)); }

async function salvarProduto(id) {
  const data = {
    nome: document.getElementById('p-nome').value.trim(),
    sku: document.getElementById('p-sku').value.trim(),
    codigo_barras: document.getElementById('p-barcode').value.trim() || null,
    categoria_id: +document.getElementById('p-cat').value,
    fornecedor_id: +document.getElementById('p-forn').value,
    quantidade: +document.getElementById('p-qtd').value,
    quantidade_minima: +document.getElementById('p-min').value,
    preco: +document.getElementById('p-preco').value,
    validade: document.getElementById('p-val').value ? new Date(document.getElementById('p-val').value).toISOString() : null,
  };
  if (!data.nome || !data.sku) { showToast('Preencha nome e SKU', 'error'); return; }
  try {
    if (id) await api.atualizarProduto(id, data);
    else await api.criarProduto(data);
    closeModal('prod-modal');
    showToast('Produto salvo', 'success');
    carregar();
  } catch (e) { showToast(e.message, 'error'); }
}

function excluirProduto(id) {
  const p = produtos.find(x => x.id === id);
  confirmAction(`Excluir "${p?.nome}"?`, async () => {
    await api.excluirProduto(id);
    showToast('Produto removido', 'success');
    carregar();
  });
}

window.abrirModalProduto = abrirModalProduto;
