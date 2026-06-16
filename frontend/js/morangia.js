function initMorangIA() {
  if (document.getElementById('assistant-panel')) return;

  const btn = document.createElement('button');
  btn.className = 'assistant-toggle';
  btn.id = 'assistant-btn';
  btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> MorangIA';

  const panel = document.createElement('div');
  panel.className = 'assistant-panel';
  panel.id = 'assistant-panel';
  panel.innerHTML = `
    <div class="assistant-header">
      <div><h4>MorangIA</h4><span>Assistente do almoxarifado</span></div>
      <button class="assistant-close" id="assistant-close">&times;</button>
    </div>
    <div class="assistant-messages" id="assistant-msgs">
      <div class="msg msg-bot">Oi! Sou a MorangIA 🍓 Posso te ajudar com estoque, validade, movimentações e dúvidas sobre o sistema. É só perguntar!</div>
    </div>
    <div class="assistant-chips" id="assistant-chips">
      <button class="chip" data-q="Quantos produtos estão com estoque baixo?">Estoque baixo</button>
      <button class="chip" data-q="Produtos vencendo esta semana">Validade</button>
      <button class="chip" data-q="Mostrar movimentações de hoje">Movimentações</button>
    </div>
    <div class="assistant-input">
      <input type="text" id="assistant-input" placeholder="Digite sua pergunta..." autocomplete="off">
      <button class="btn btn-primary btn-sm" id="assistant-send">Enviar</button>
    </div>`;

  document.body.appendChild(btn);
  document.body.appendChild(panel);

  const msgs = document.getElementById('assistant-msgs');
  const input = document.getElementById('assistant-input');

  btn.onclick = () => panel.classList.toggle('open');
  document.getElementById('assistant-close').onclick = () => panel.classList.remove('open');

  async function send(text) {
    if (!text.trim()) return;
    msgs.innerHTML += `<div class="msg msg-user">${esc(text)}</div>`;
    msgs.innerHTML += `<div class="msg msg-bot msg-loading" id="assistant-loading">Processando...</div>`;
    msgs.scrollTop = msgs.scrollHeight;
    input.value = '';

    try {
      const res = await api.morangiaChat(text);
      document.getElementById('assistant-loading')?.remove();
      msgs.innerHTML += `<div class="msg msg-bot">${esc(res.resposta)}</div>`;
      if (res.sugestoes?.length) {
        document.getElementById('assistant-chips').innerHTML = res.sugestoes
          .slice(0, 4)
          .map(s => `<button class="chip" data-q="${escAttr(s)}">${esc(s.length > 28 ? s.slice(0, 28) + '…' : s)}</button>`)
          .join('');
        bindChips();
      }
    } catch (e) {
      document.getElementById('assistant-loading')?.remove();
      msgs.innerHTML += `<div class="msg msg-bot">Erro: ${esc(e.message)}</div>`;
    }
    msgs.scrollTop = msgs.scrollHeight;
  }

  function bindChips() {
    document.querySelectorAll('#assistant-chips .chip').forEach(c => {
      c.onclick = () => send(c.dataset.q);
    });
  }

  document.getElementById('assistant-send').onclick = () => send(input.value);
  input.onkeydown = e => { if (e.key === 'Enter') send(input.value); };
  bindChips();
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
function escAttr(s) { return s.replace(/"/g, '&quot;'); }

window.initMorangIA = initMorangIA;
