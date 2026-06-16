function getUser() {
  try { return JSON.parse(localStorage.getItem('moranguinho_user')); } catch { return null; }
}

function getToken() { return localStorage.getItem('moranguinho_token'); }

function saveAuth(token, user) {
  localStorage.setItem('moranguinho_token', token);
  localStorage.setItem('moranguinho_user', JSON.stringify(user));
}

function logout() {
  localStorage.removeItem('moranguinho_token');
  localStorage.removeItem('moranguinho_user');
  window.location.href = 'login.html';
}

function requireAuth() {
  if (!getToken()) { window.location.href = 'login.html'; return false; }
  return true;
}

function hasPermission(modulo) {
  const user = getUser();
  if (!user?.permissoes) return false;
  return user.permissoes.includes('*') || user.permissoes.includes(modulo);
}

function getInitials(nome) {
  if (!nome) return '?';
  return nome.split(' ').filter(Boolean).slice(0, 2).map(n => n[0]).join('').toUpperCase();
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function formatCurrency(v) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0);
}

function getValidadeBadge(status) {
  const map = {
    ok: '<span class="badge badge-success">Normal</span>',
    atencao: '<span class="badge badge-warning">Atenção</span>',
    vencendo: '<span class="badge badge-warning">Vencendo</span>',
    vencido: '<span class="badge badge-danger">Vencido</span>',
    sem_validade: '<span class="badge badge-neutral">Sem validade</span>',
  };
  return map[status] || map.sem_validade;
}

function getTipoBadge(tipo) {
  return tipo === 'entrada'
    ? '<span class="badge badge-success">Entrada</span>'
    : '<span class="badge badge-danger">Saída</span>';
}

window.getUser = getUser;
window.getToken = getToken;
window.saveAuth = saveAuth;
window.logout = logout;
window.requireAuth = requireAuth;
window.hasPermission = hasPermission;
window.getInitials = getInitials;
window.formatDate = formatDate;
window.formatCurrency = formatCurrency;
window.getValidadeBadge = getValidadeBadge;
window.getTipoBadge = getTipoBadge;
