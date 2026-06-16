const ICONS = {
  dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  produtos: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
  estoque: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
  fornecedores: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
  movimentacoes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
  relatorios: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
  usuarios: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
};

const NAV = [
  { href: 'dashboard.html', key: 'dashboard', label: 'Painel', mod: 'dashboard' },
  { href: 'produtos.html', key: 'produtos', label: 'Produtos', mod: 'produtos' },
  { href: 'estoque.html', key: 'estoque', label: 'Estoque', mod: 'estoque' },
  { href: 'fornecedores.html', key: 'fornecedores', label: 'Fornecedores', mod: 'fornecedores' },
  { href: 'movimentacoes.html', key: 'movimentacoes', label: 'Movimentações', mod: 'movimentacoes' },
  { href: 'relatorios.html', key: 'relatorios', label: 'Relatórios', mod: 'relatorios' },
  { href: 'usuarios.html', key: 'usuarios', label: 'Equipe', mod: 'usuarios' },
];

function renderSidebar(activePage) {
  const user = getUser();
  if (!user) return '';

  const nav = NAV.map(item => {
    const ok = hasPermission(item.mod);
    const cls = item.href === activePage ? 'nav-item active' : 'nav-item';
    return `<a href="${ok ? item.href : '#'}" class="${cls}${ok ? '' : ' disabled'}">${ICONS[item.key]}${item.label}</a>`;
  }).join('');

  const avatar = user.foto_perfil
    ? `<img src="${user.foto_perfil}" alt="">`
    : getInitials(user.nome_completo);

  const greeting = typeof getGreeting === 'function' ? getGreeting() : 'Olá';
  const firstName = typeof getFirstName === 'function' ? getFirstName(user.nome_completo) : user.nome_completo;

  return `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-brand">
        <img src="assets/logo/moranguinho.svg" alt="Moranguinho">
        <div class="sidebar-brand-text">
          <h2>Moranguinho</h2>
          <span>Gestão de almoxarifado</span>
        </div>
      </div>
      <div class="sidebar-greeting">
        <strong>${greeting}, ${firstName}!</strong>
        Pronto para mais um dia de trabalho?
      </div>
      <div class="sidebar-profile">
        <div class="sidebar-avatar">${avatar}</div>
        <div class="sidebar-profile-info">
          <strong>${user.nome_completo}</strong>
          <span><span class="online-dot"></span>${user.cargo}</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">Menu</div>
        ${nav}
      </nav>
      <div class="sidebar-footer">
        <button class="btn btn-secondary btn-sm" onclick="logout()">Sair do sistema</button>
      </div>
    </aside>`;
}

window.renderSidebar = renderSidebar;
