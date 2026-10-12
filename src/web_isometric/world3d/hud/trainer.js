// A guild trainer's window (right-click a trainer → Master your abilities). Using an ability
// raises it to 85% ("Mastered"); past that a trainer teaches it to 100% in 5% steps, for gold
// or a practice session left over from the old system. The server decides (`practice <id>`);
// this lists what can be bought and what it costs.
import { BY_USE, rankOf } from '../abilities.js';

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export const STEP = 5;
// the price of the next step, as the server charges it ((current − 80) × 250 gold)
export const stepCost = pct => Math.max(1, Math.round((pct - 80) * 250));

// what a trainer can do for each known ability
export function offers(abilities, gold, practices) {
  return (abilities || []).filter(a => a.known).map(a => {
    const pct = a.pct || 0;
    if (pct >= 100) return { a, state: 'done', text: 'Perfected' };
    if (pct < BY_USE) return { a, state: 'use', text: `${rankOf(pct)} · ${pct}% — keep using it; train at ${BY_USE}%` };
    const cost = stepCost(pct), next = Math.min(100, pct + STEP);
    const pay = practices > 0 ? 'practice' : gold >= cost ? 'gold' : null;
    return { a, state: pay ? 'buy' : 'poor', next, cost, pay,
      text: `${pct}% → ${next}% · ${practices > 0 ? '1 practice session' : `${cost.toLocaleString()} gold`}` };
  }).sort((x, y) => ['buy', 'poor', 'use', 'done'].indexOf(x.state) - ['buy', 'poor', 'use', 'done'].indexOf(y.state) || (y.a.pct || 0) - (x.a.pct || 0));
}

export function createTrainer(root, { icon, onTrain }) {
  const body = root.querySelector('.tr-body');
  let open = false, who = '', player = null, sig = '';
  root.querySelector('.tr-close').addEventListener('click', () => toggle(false));
  function render() {
    if (!open || !player) return;
    const list = offers(player.abilities, player.gold || 0, player.practices || 0);
    const nsig = JSON.stringify([who, player.gold, player.practices, list.map(o => [o.a.id, o.a.pct])]);
    if (nsig === sig) return;
    sig = nsig;
    root.querySelector('.tr-who').textContent = who ? `Training with ${who}` : 'Training';
    body.innerHTML = `<div class="tr-purse">${(player.gold || 0).toLocaleString()} gold${player.practices ? ` · ${player.practices} practice session${player.practices > 1 ? 's' : ''}` : ''}</div>
      <div class="sb-list">${list.map(o => `<div class="tr-row ${o.state}">
        <div class="sb-ic">${icon(o.a.id)}</div>
        <div class="sb-main"><div class="sb-name">${esc(o.a.name)}</div><div class="sb-cost">${esc(o.text)}</div></div>
        ${o.state === 'buy' || o.state === 'poor' ? `<button class="tr-buy" data-id="${esc(o.a.id)}" ${o.state === 'buy' ? '' : 'disabled title="Not enough gold"'}>Train</button>` : ''}
      </div>`).join('') || '<span class="ch-none">Nothing to teach you yet</span>'}</div>`;
    body.querySelectorAll('.tr-buy:not([disabled])').forEach(b => b.addEventListener('click', () => onTrain(b.dataset.id)));
  }
  function toggle(on = !open, name) {
    open = on;
    if (name !== undefined) who = name;
    root.classList.toggle('hidden', !open);
    if (open) { sig = ''; render(); }
  }
  return { toggle, get open() { return open; }, update(p) { player = p; render(); } };
}
