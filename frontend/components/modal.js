function openModal(id) { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

function createModal(id, title, bodyHtml, footerHtml) {
  document.getElementById(id)?.remove();
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal-overlay" id="${id}">
      <div class="modal">
        <div class="modal-head"><h3>${title}</h3><button class="modal-close" onclick="closeModal('${id}')">&times;</button></div>
        <div class="modal-body">${bodyHtml}</div>
        ${footerHtml ? `<div class="modal-foot">${footerHtml}</div>` : ''}
      </div>
    </div>`);
}

function confirmAction(msg, onConfirm) {
  createModal('confirm-modal', 'Confirmar', `<p style="font-size:14px;color:var(--text-secondary)">${msg}</p>`,
    `<button class="btn btn-secondary btn-sm" onclick="closeModal('confirm-modal')">Cancelar</button>
     <button class="btn btn-danger btn-sm" id="confirm-ok">Confirmar</button>`);
  openModal('confirm-modal');
  document.getElementById('confirm-ok').onclick = () => { closeModal('confirm-modal'); onConfirm(); };
}

window.openModal = openModal;
window.closeModal = closeModal;
window.createModal = createModal;
window.confirmAction = confirmAction;
