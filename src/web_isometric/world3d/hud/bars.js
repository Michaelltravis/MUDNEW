// The extra action bars (the owner: "we need more bars to add spells, make them movable"): up to
// three floating bars of 8 slots beside the main bar: Alt+1-8, Alt+Shift+1-8, and one you click.
// Each has a grip to drag it anywhere (it stays on screen), a button that turns it across or
// along, and a lock. How many show (Settings), where each sits, and which way it lies are kept
// per character on this device (localStorage, barlayout.js); what is ON them is kept with the
// character on the server (`webbar`, hud.js).
import { BAR_COUNT, barSize, defaultPos, clamp, parse, serialize, defaults } from '../barlayout.js';
import { EXTRA } from '../abilities.js';

const ls = { get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} } };
const uiScale = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui')) || 1;
const TITLES = ['Bar 3 · Alt+1–8', 'Bar 4 · Alt+Shift+1–8', 'Bar 5 · click'];

export function createBars(root, { onChange } = {}) {
  let name = '', layout = defaults();
  const panels = [];
  for (let i = 0; i < BAR_COUNT; i++) {
    const el = document.createElement('div');
    el.className = 'xbar panel ornate small';
    el.dataset.bar = String(i);
    el.innerHTML = `<div class="xgrip" data-tip-title="${TITLES[i]}" data-tip-sub="Drag to move · ⟲ turns it · 🔒 locks it">`
      + `<i class="dots"></i><button class="xturn" title="Turn the bar">⟲</button><button class="xlock" title="Lock where it is">🔓</button></div>`
      + `<div class="xslots" data-from="${EXTRA[i][0]}"></div>`;
    root.appendChild(el);
    panels.push(el);
    el.querySelector('.xturn').addEventListener('click', e => { e.stopPropagation(); turn(i); });
    el.querySelector('.xlock').addEventListener('click', e => { e.stopPropagation(); lock(i); });
    drag(el, i);
  }

  const key = () => `mh3d_bars:${String(name || '').toLowerCase()}`;
  function save() { if (name) ls.set(key(), serialize(layout)); }
  function posOf(i) {
    const b = layout.bars[i];
    const size = barSize(!!(b && b.vertical), uiScale());
    const vw = window.innerWidth, vh = window.innerHeight;
    return b ? { ...clamp(b, size, vw, vh), vertical: !!b.vertical, locked: !!b.locked } : { ...defaultPos(i, vw, vh, { ui: uiScale() }), vertical: false, locked: false };
  }
  function apply() {
    panels.forEach((el, i) => {
      const on = i < layout.count;
      el.classList.toggle('off', !on);
      if (!on) return;
      const p = posOf(i);
      el.classList.toggle('vertical', p.vertical);
      el.classList.toggle('locked', p.locked);
      el.querySelector('.xlock').textContent = p.locked ? '🔒' : '🔓';
      el.style.left = `${p.x}px`;
      el.style.top = `${p.y}px`;
    });
  }
  function turn(i) {
    const p = posOf(i);
    layout.bars[i] = { ...p, vertical: !p.vertical };
    layout.bars[i] = { ...layout.bars[i], ...clamp(layout.bars[i], barSize(!p.vertical, uiScale()), window.innerWidth, window.innerHeight) };
    save(); apply();
  }
  function lock(i) {
    const p = posOf(i);
    layout.bars[i] = { ...p, locked: !p.locked };
    save(); apply();
  }
  // drag by the grip (not its buttons), unless locked
  function drag(el, i) {
    const grip = el.querySelector('.xgrip');
    let start = null;
    grip.addEventListener('pointerdown', e => {
      if (e.button !== 0 || e.target.closest('button') || posOf(i).locked) return;
      const p = posOf(i);
      start = { mx: e.clientX, my: e.clientY, x: p.x, y: p.y, vertical: p.vertical };
      grip.setPointerCapture(e.pointerId);
      el.classList.add('moving');
      e.preventDefault();
    });
    grip.addEventListener('pointermove', e => {
      if (!start) return;
      const pos = clamp({ x: start.x + e.clientX - start.mx, y: start.y + e.clientY - start.my },
        barSize(start.vertical, uiScale()), window.innerWidth, window.innerHeight);
      el.style.left = `${pos.x}px`;
      el.style.top = `${pos.y}px`;
      layout.bars[i] = { x: pos.x, y: pos.y, vertical: start.vertical, locked: false };
    });
    const end = () => { if (!start) return; start = null; el.classList.remove('moving'); save(); };
    grip.addEventListener('pointerup', end);
    grip.addEventListener('pointercancel', end);
  }
  window.addEventListener('resize', () => requestAnimationFrame(apply));

  return {
    // whose layout (a character's own, on this device)
    load(who) { name = who || ''; layout = name ? parse(ls.get(key())) : defaults(); apply(); if (onChange) onChange(); },
    get count() { return layout.count; },
    setCount(n) { layout.count = Math.max(0, Math.min(BAR_COUNT, n | 0)); save(); apply(); if (onChange) onChange(); },
    show(on) { root.classList.toggle('hidden', !on); if (on) apply(); },
    // the slot rows of the bars that show: [{el, from, to}]
    rows() { return panels.map((el, i) => ({ el: el.querySelector('.xslots'), from: EXTRA[i][0], to: EXTRA[i][1], on: i < layout.count })); },
    panels,
  };
}
