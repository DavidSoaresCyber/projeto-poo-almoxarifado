function showToast(msg, type = 'info') {
  let c = document.getElementById('toast-root');
  if (!c) {
    c = document.createElement('div');
    c.id = 'toast-root';
    document.body.appendChild(c);
  }
  const icons = { info: 'ℹ️', success: '✓', error: '✕' };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span>${icons[type] || icons.info}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(24px)';
    t.style.transition = 'opacity 0.25s, transform 0.25s';
    setTimeout(() => t.remove(), 250);
  }, 3500);
}

function hideLoading() {
  document.getElementById('loading-screen')?.classList.add('hidden');
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Bom dia';
  if (h < 18) return 'Boa tarde';
  return 'Boa noite';
}

function getFirstName(nome) {
  if (!nome) return 'colega';
  return nome.split(' ')[0];
}

function initApp(page, fn) {
  if (!requireAuth()) return;
  document.getElementById('sidebar-container').innerHTML = renderSidebar(page);
  document.getElementById('navbar-container').innerHTML = renderNavbar();
  loadNotifCount();
  if (hasPermission('morangia')) initMorangIA();
  if (fn) fn();
  hideLoading();

  const toggle = document.getElementById('menu-toggle');
  const sidebar = document.getElementById('sidebar');
  if (window.innerWidth <= 900 && toggle) {
    toggle.style.display = 'flex';
    toggle.onclick = () => sidebar?.classList.toggle('open');
  }
  document.addEventListener('click', (e) => {
    if (sidebar?.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
      sidebar.classList.remove('open');
    }
  });
}

window.showToast = showToast;
window.hideLoading = hideLoading;
window.getGreeting = getGreeting;
window.getFirstName = getFirstName;
window.initApp = initApp;
