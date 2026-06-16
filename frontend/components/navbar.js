function renderNavbar() {
  const user = getUser();
  if (!user) return '';
  const hora = new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
  const greeting = typeof getGreeting === 'function' ? getGreeting() : 'Olá';
  return `
    <header class="topbar">
      <div class="topbar-left">
        <h2>${greeting}, ${typeof getFirstName === 'function' ? getFirstName(user.nome_completo) : user.nome_completo} 👋</h2>
        <p>${user.cargo} · ${hora}</p>
      </div>
      <div class="topbar-actions">
        <div class="notif-wrap">
          <button class="btn btn-icon" id="notif-btn" title="Notificações" aria-label="Notificações">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            <span class="notif-badge hidden" id="notif-count">0</span>
          </button>
          <div class="notif-dropdown" id="notif-dropdown">
            <div class="notif-dropdown-header">Notificações</div>
            <div id="notif-list"></div>
          </div>
        </div>
        <button class="btn btn-icon" id="menu-toggle" title="Menu" style="display:none">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
      </div>
    </header>`;
}

async function loadNotifCount() {
  const countEl = document.getElementById('notif-count');
  const listEl = document.getElementById('notif-list');
  const btn = document.getElementById('notif-btn');
  const dropdown = document.getElementById('notif-dropdown');
  if (!countEl) return;

  try {
    const items = await api.notificacoes();
    const unread = items.filter(i => !i.lida);
    countEl.textContent = unread.length;
    countEl.classList.toggle('hidden', unread.length === 0);

    if (listEl) {
      listEl.innerHTML = items.length
        ? items.slice(0, 8).map(n => `
            <div class="notif-item" data-id="${n.id}">
              <strong>${n.titulo}</strong>
              <span>${n.mensagem}</span>
            </div>`).join('')
        : '<div class="notif-empty">Nenhuma notificação</div>';
    }
  } catch {
    if (listEl) listEl.innerHTML = '<div class="notif-empty">Não foi possível carregar</div>';
  }

  btn?.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown?.classList.toggle('open');
  });
  document.addEventListener('click', () => dropdown?.classList.remove('open'));
  dropdown?.addEventListener('click', e => e.stopPropagation());

  listEl?.querySelectorAll('.notif-item').forEach(el => {
    el.addEventListener('click', async () => {
      await api.marcarNotificacao(el.dataset.id);
      loadNotifCount();
    });
  });
}

window.renderNavbar = renderNavbar;
window.loadNotifCount = loadNotifCount;
