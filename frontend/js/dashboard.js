document.addEventListener('DOMContentLoaded', () => {
  initApp('dashboard.html', loadDashboard);
});

async function loadDashboard() {
  const user = getUser();
  const avatar = user.foto_perfil
    ? `<img src="${user.foto_perfil}" alt="">`
    : getInitials(user.nome_completo);

  const perms = (user.permissoes || [])
    .map(p => `<span class="tag">${p === '*' ? 'Acesso total' : p}</span>`)
    .join('');

  document.getElementById('user-card').innerHTML = `
    <div class="profile-banner fade-in">
      <div class="profile-avatar">${avatar}</div>
      <div class="profile-details">
        <h3>${user.nome_completo}</h3>
        <div class="role">${user.cargo}</div>
        <div class="profile-meta">
          <span>${user.email}</span>
          <span>Último acesso: ${formatDate(user.ultimo_acesso)}</span>
          <span>Nível ${user.nivel_acesso}</span>
        </div>
        <div class="profile-tags">${perms}</div>
      </div>
    </div>`;

  try {
    const stats = await api.dashboard();
    document.getElementById('stats-grid').innerHTML = `
      <div class="stat-card accent-primary"><div class="stat-icon">📦</div><div class="stat-label">Produtos cadastrados</div><div class="stat-value">${stats.total_produtos}</div></div>
      <div class="stat-card accent-danger"><div class="stat-icon">⚠️</div><div class="stat-label">Precisam de reposição</div><div class="stat-value">${stats.estoque_baixo}</div><div class="stat-sub">Abaixo do mínimo</div></div>
      <div class="stat-card accent-warning"><div class="stat-icon">📅</div><div class="stat-label">Vencem em 7 dias</div><div class="stat-value">${stats.produtos_vencendo}</div></div>
      <div class="stat-card accent-success"><div class="stat-icon">💰</div><div class="stat-label">Valor em estoque</div><div class="stat-value" style="font-size:22px">${formatCurrency(stats.valor_estoque)}</div></div>
      <div class="stat-card"><div class="stat-icon">🔄</div><div class="stat-label">Movimentações hoje</div><div class="stat-value">${stats.movimentacoes_hoje}</div><div class="stat-sub">${stats.entradas_recentes} entradas · ${stats.saidas_recentes} saídas</div></div>
      <div class="stat-card"><div class="stat-icon">🚚</div><div class="stat-label">Fornecedores ativos</div><div class="stat-value">${stats.total_fornecedores}</div></div>
      <div class="stat-card accent-danger"><div class="stat-icon">🚫</div><div class="stat-label">Produtos vencidos</div><div class="stat-value">${stats.produtos_vencidos}</div></div>
      <div class="stat-card"><div class="stat-icon">📋</div><div class="stat-label">Itens monitorados</div><div class="stat-value">${stats.total_produtos}</div></div>`;

    const graf = await api.dashboardGraficos();
    Chart.defaults.color = '#6b7280';
    Chart.defaults.borderColor = '#2e2e2e';

    new Chart(document.getElementById('chart-mov'), {
      type: 'bar',
      data: {
        labels: graf.dias,
        datasets: [
          { label: 'Entradas', data: graf.entradas, backgroundColor: 'rgba(22,163,74,0.7)', borderRadius: 4 },
          { label: 'Saídas', data: graf.saidas, backgroundColor: 'rgba(224,25,25,0.7)', borderRadius: 4 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { labels: { boxWidth: 12, font: { size: 12 } } } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { stepSize: 1 } } },
      },
    });

    new Chart(document.getElementById('chart-cat'), {
      type: 'doughnut',
      data: {
        labels: graf.categorias,
        datasets: [{ data: graf.cat_data, backgroundColor: ['#e01919','#16a34a','#2563eb','#d97706','#7c3aed','#0891b2'], borderWidth: 0 }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 }, padding: 12 } } },
      },
    });

    const movs = await api.movimentacoes();
    document.getElementById('activity-list').innerHTML = movs.slice(0, 8).map(m => `
      <div class="activity-row">
        <span class="activity-dot"></span>
        <div>
          <strong>${m.tipo === 'entrada' ? 'Entrada' : 'Saída'} — ${m.quantidade} un. ${m.produto_nome || ''}</strong>
          <small>${m.usuario_nome || '—'} · ${formatDate(m.criado_em)}</small>
        </div>
      </div>`).join('') || '<p class="text-muted" style="padding:12px 0">Nenhuma movimentação registrada</p>';
  } catch (e) {
    showToast(e.message, 'error');
  }
}
