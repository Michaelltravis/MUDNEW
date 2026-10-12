// A small right-click menu: a title and a few actions, kept on screen, closed by Esc, a
// click elsewhere, the wheel or a movement key. Items: {label, run?, disabled?}.
export function createContextMenu(root) {
  let open = false;
  const close = () => {
    if (!open) return;
    open = false;
    root.classList.add('hidden');
    root.innerHTML = '';
  };
  function show(x, y, title, items) {
    root.innerHTML = '';
    if (title) {
      const h = document.createElement('div');
      h.className = 'ctx-title';
      h.textContent = title;
      root.appendChild(h);
    }
    for (const it of items) {
      const b = document.createElement('button');
      b.textContent = it.label;
      if (!it.run || it.disabled) { b.disabled = true; b.className = 'muted'; }
      b.addEventListener('click', e => { e.stopPropagation(); close(); if (it.run) it.run(); });
      root.appendChild(b);
    }
    root.classList.remove('hidden');
    open = true;
    const r = root.getBoundingClientRect();
    root.style.left = `${Math.max(6, Math.min(x, window.innerWidth - r.width - 6))}px`;
    root.style.top = `${Math.max(6, Math.min(y, window.innerHeight - r.height - 6))}px`;
  }
  window.addEventListener('pointerdown', e => { if (open && !root.contains(e.target)) close(); }, true);
  window.addEventListener('wheel', close, { passive: true });
  window.addEventListener('keydown', e => {
    if (!open) return;
    if (e.key === 'Escape') { close(); e.stopPropagation(); return; }
    if (/^(w|a|s|d|arrow\w+)$/i.test(e.key)) close();
  }, true);
  return { show, close, get open() { return open; } };
}
