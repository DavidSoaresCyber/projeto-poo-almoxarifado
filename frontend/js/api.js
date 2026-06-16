const API_BASE = (window.location.port === '8000' || !window.location.port)
  ? '/api'
  : 'http://127.0.0.1:8000/api';

async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('moranguinho_token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (res.status === 401) {
    localStorage.removeItem('moranguinho_token');
    localStorage.removeItem('moranguinho_user');
    if (!location.pathname.includes('login') && !location.pathname.includes('index')) {
      location.href = 'login.html';
    }
    throw new Error(data.detail || 'Não autorizado');
  }
  if (!res.ok) {
    const msg = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail[0]?.msg : 'Erro na requisição';
    throw new Error(msg || 'Erro na requisição');
  }
  return data;
}

const api = {
  get: (url) => apiRequest(url),
  post: (url, body) => apiRequest(url, { method: 'POST', body: JSON.stringify(body) }),
  put: (url, body) => apiRequest(url, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (url, body) => apiRequest(url, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (url) => apiRequest(url, { method: 'DELETE' }),

  login: (email, senha) => api.post('/auth/login/json', { email, senha }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),

  dashboard: () => api.get('/dashboard'),
  dashboardGraficos: () => api.get('/dashboard/graficos'),
  produtos: (busca = '') => api.get(`/produtos${busca ? '?busca=' + encodeURIComponent(busca) : ''}`),
  criarProduto: (data) => api.post('/produtos', data),
  atualizarProduto: (id, data) => api.put(`/produtos/${id}`, data),
  excluirProduto: (id) => api.delete(`/produtos/${id}`),
  produtoBarcode: (code) => api.get(`/produtos/barcode/${code}`),
  barcode: (code) => api.get(`/produtos/barcode/${code}`),
  cargos: () => api.get('/auth/cargos'),

  movimentacoes: (tipo) => api.get(`/movimentacoes${tipo ? '?tipo=' + tipo : ''}`),
  criarMovimentacao: (data) => api.post('/movimentacoes', data),

  fornecedores: () => api.get('/fornecedores'),
  criarFornecedor: (data) => api.post('/fornecedores', data),
  excluirFornecedor: (id) => api.delete(`/fornecedores/${id}`),

  categorias: () => api.get('/categorias'),
  usuarios: () => api.get('/usuarios'),
  notificacoes: () => api.get('/notificacoes'),
  logs: () => api.get('/logs'),
  morangiaChat: (mensagem) => api.post('/morangia/chat', { mensagem }),
  marcarNotificacao: (id) => api.patch(`/notificacoes/${id}/lida`, {}),
  backupInfo: () => api.get('/backup/info'),

  async download(url, filename) {
    const token = localStorage.getItem('moranguinho_token');
    const res = await fetch(`${API_BASE}${url}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!res.ok) throw new Error('Erro ao baixar arquivo');
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
  }
};

window.api = api;
window.Api = api;
