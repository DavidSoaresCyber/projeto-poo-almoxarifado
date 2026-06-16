let movs = [];

if (!hasPermission('movimentacoes')) location.href = 'dashboard.html';

document.addEventListener('DOMContentLoaded', () => {
  initApp('movimentacoes.html', () => {
    load();
    document.getElementById('filtro-tipo').onchange = e => load(e.target.value);
    document.getElementById('btn-export').onclick = exportarCSV;
  });
});

async function load(tipo) {
  movs = await api.movimentacoes(tipo || undefined);
  document.getElementById('mov-tbody').innerHTML = movs.length
    ? movs.map(m => `<tr>
        <td>${formatDate(m.criado_em)}</td>
        <td>${getTipoBadge(m.tipo)}</td>
        <td class="td-strong">${m.produto_nome || '—'}</td>
        <td>${m.quantidade}</td>
        <td>${m.usuario_nome || '—'}</td>
        <td>${m.observacao || '—'}</td>
      </tr>`).join('')
    : '<tr class="empty-row"><td colspan="6">Nenhuma movimentação</td></tr>';
}

function exportarCSV() {
  const csv = 'Data,Tipo,Produto,Quantidade,Responsavel,Observacao\n' + movs.map(m =>
    `"${m.criado_em}","${m.tipo}","${m.produto_nome}",${m.quantidade},"${m.usuario_nome}","${(m.observacao||'').replace(/"/g,'""')}"`
  ).join('\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  a.download = `movimentacoes_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  showToast('Arquivo exportado', 'success');
}
