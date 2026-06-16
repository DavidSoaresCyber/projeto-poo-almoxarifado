if (!hasPermission('fornecedores')) { window.location.href = 'dashboard.html'; }

document.addEventListener('DOMContentLoaded', () => {
  initApp('fornecedores.html', load);
});

async function load() {
  const list = await api.fornecedores();
  document.getElementById('forn-tbody').innerHTML = list.length
    ? list.map(f => `<tr>
        <td class="td-strong">${f.nome}</td><td>${f.cnpj}</td>
        <td>${f.email || '—'}</td><td>${f.telefone || '—'}</td><td>${f.endereco || '—'}</td>
        <td class="td-actions"><button class="btn btn-danger btn-sm" onclick="excluirForn(${f.id}, '${f.nome.replace(/'/g, "\\'")}')">Remover</button></td>
      </tr>`).join('')
    : '<tr class="empty-row"><td colspan="6">Nenhum fornecedor cadastrado</td></tr>';
}

function abrirForn() {
  createModal('forn-modal', 'Novo fornecedor', `
    <div class="form-group"><label>Razão social</label><input id="f-nome" class="form-control"></div>
    <div class="form-group"><label>CNPJ</label><input id="f-cnpj" class="form-control" placeholder="00.000.000/0000-00"></div>
    <div class="form-group"><label>E-mail</label><input type="email" id="f-email" class="form-control"></div>
    <div class="form-group"><label>Telefone</label><input id="f-tel" class="form-control"></div>
    <div class="form-group"><label>Endereço</label><input id="f-end" class="form-control"></div>`,
    `<button class="btn btn-secondary btn-sm" onclick="closeModal('forn-modal')">Cancelar</button>
     <button class="btn btn-primary btn-sm" id="save-forn">Salvar</button>`);
  openModal('forn-modal');
  document.getElementById('save-forn').onclick = async () => {
    const nome = document.getElementById('f-nome').value.trim();
    const cnpj = document.getElementById('f-cnpj').value.trim();
    if (!nome || !cnpj) { showToast('Preencha nome e CNPJ', 'error'); return; }
    try {
      await api.criarFornecedor({
        nome, cnpj,
        email: document.getElementById('f-email').value.trim() || null,
        telefone: document.getElementById('f-tel').value.trim() || null,
        endereco: document.getElementById('f-end').value.trim() || null,
      });
      closeModal('forn-modal');
      showToast('Fornecedor cadastrado', 'success');
      load();
    } catch (e) { showToast(e.message, 'error'); }
  };
}

function excluirForn(id, nome) {
  confirmAction(`Remover fornecedor "${nome}"?`, async () => {
    await api.excluirFornecedor(id);
    showToast('Fornecedor removido', 'success');
    load();
  });
}

window.abrirForn = abrirForn;
