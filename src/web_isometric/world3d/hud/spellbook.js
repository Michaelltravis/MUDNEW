// The spellbook (K): every ability of your class — what it costs, how far it reaches, how well
// you know it — and the ones still to come ("Unlocks at level 12"). Drag one onto your bar
// (or press its ＋), double-click to use it. Abilities improve as you use them, up to 85%; a
// trainer teaches the rest. Data: the player payload's `abilities` (see abilities.js).
import { rankOf, costLine, usable, BY_USE } from '../abilities.js';

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createSpellbook(root, { icon, onUse, onAdd, onDragStart, onDragEnd }) {
  const body = root.querySelector('.sb-body');
  let abilities = [], bar = [], open = false, tab = 'all', sig = '', level = 1;

  root.querySelectorAll('.sb-tabs button').forEach(b => b.addEventListener('click', () => {
    tab = b.dataset.tab; sig = '';
    root.querySelectorAll('.sb-tabs button').forEach(x => x.classList.toggle('on', x === b));
    render();
  }));
  root.querySelector('.sb-close').addEventListener('click', () => toggle(false));

  function card(a) {
    const onBar = bar.indexOf(a.id);
    const key = onBar < 0 ? '' : onBar < 8 ? String(onBar + 1) : `⇧${onBar - 7}`;
    const pct = Math.max(0, Math.min(100, a.pct || 0));
    const can = usable(a);
    return `<div class="sb-card ${a.known ? '' : 'locked'}${a.passive ? ' passive' : ''}" data-id="${esc(a.id)}" ${can ? 'draggable="true"' : ''}
        title="${!a.known ? (a.quest ? `Earned through ${a.quest} (your guild's trainer, from level ${a.level})` : `Unlocks at level ${a.level}`) : can ? 'Drag onto your bar · double-click to use' : 'Passive: it works on its own'}">
      <div class="sb-ic">${icon(a.id)}</div>
      <div class="sb-main">
        <div class="sb-top"><span class="sb-name">${esc(a.name)}</span>
          <span class="sb-rank">${a.known ? `${rankOf(pct)} · ${pct}%` : a.quest ? `★ Quest · level ${a.level}` : `Level ${a.level}`}</span></div>
        ${a.known ? `<div class="sb-bar"><b style="width:${pct}%"></b><i style="left:${BY_USE}%"></i></div>` : ''}
        <div class="sb-cost">${esc(costLine(a))}</div>
        ${a.desc ? `<div class="sb-desc">${esc(a.desc)}</div>` : ''}
      </div>
      ${can ? (key ? `<span class="sb-key" title="On your bar">${key}</span>` : '<button class="sb-add" title="Put it on your bar">＋</button>') : ''}
    </div>`;
  }

  function render() {
    if (!open) return;
    const show = abilities.filter(a => tab === 'all' || a.type === tab);
    const nsig = JSON.stringify([tab, level, bar, show.map(a => [a.id, a.pct, a.known])]);
    if (nsig === sig) return;
    sig = nsig;
    const known = show.filter(a => a.known).sort((a, b) => (a.level || 0) - (b.level || 0) || a.name.localeCompare(b.name));
    const later = show.filter(a => !a.known).sort((a, b) => (a.level || 0) - (b.level || 0) || a.name.localeCompare(b.name));
    body.innerHTML = `<div class="sb-hint">Abilities grow as you use them, up to ${BY_USE}%. A trainer in your guild teaches the rest, for gold.</div>
      <div class="sb-list">${known.map(card).join('') || '<span class="ch-none">Nothing yet</span>'}</div>
      ${later.length ? `<div class="ch-lab">Coming later</div><div class="sb-list">${later.map(card).join('')}</div>` : ''}`;
    body.querySelectorAll('.sb-card[draggable]').forEach(el => {
      const id = el.dataset.id;
      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/x-ability', id);
        e.dataTransfer.effectAllowed = 'copyMove';
        if (onDragStart) onDragStart(id);
      });
      el.addEventListener('dragend', () => onDragEnd && onDragEnd());
      el.addEventListener('dblclick', () => onUse(id));
      const add = el.querySelector('.sb-add');
      if (add) add.addEventListener('click', e => { e.stopPropagation(); onAdd(id); });
    });
  }

  function toggle(on = !open) {
    open = on;
    root.classList.toggle('hidden', !open);
    if (open) { sig = ''; render(); }
  }
  return {
    toggle,
    get open() { return open; },
    update(list, b, lvl) { abilities = list || []; bar = b || []; level = lvl || 1; render(); },
  };
}
