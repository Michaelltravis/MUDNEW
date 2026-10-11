// Inventory panel (I): worn gear in slots around the hero, the bag as a grid, item
// tooltips (stats, damage, armour, effects) and actions that go out as the MUD's own
// commands (wear, wield, remove, quaff, eat, drink, recite, drop, examine). Item art comes
// from the 2D client's icon painter (platformer/items.js, no Phaser needed).
import { sound } from '../audio.js';

const $ = s => document.querySelector(s);

const SLOTS = [
  ['head', 'Head'], ['neck1', 'Neck'], ['neck2', 'Neck'], ['about', 'Cloak'], ['body', 'Body'], ['arms', 'Arms'],
  ['wrist1', 'Wrist'], ['wrist2', 'Wrist'], ['hands', 'Hands'], ['waist', 'Waist'], ['legs', 'Legs'], ['feet', 'Feet'],
  ['finger1', 'Ring'], ['finger2', 'Ring'], ['light', 'Light'], ['wield', 'Weapon'], ['shield', 'Shield'],
  ['hold', 'Held'], ['dual_wield', 'Off-hand'],
];
const RARITY = { common: '#b8b0a0', uncommon: '#6fd06f', rare: '#5aa8ff', epic: '#c07aff', legendary: '#ffa640', set: '#5fe0c8' };
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// the word the MUD finds an item by, numbered when several share it ("2.sword")
function keywordFor(item, list) {
  const kw = String(item.name || item.short || 'item').toLowerCase().split(/\s+/).find(w => w.length > 1) || 'item';
  let n = 0;
  for (const it of list) {
    const k = String(it.name || it.short || '').toLowerCase().split(/\s+/);
    if (k.includes(kw)) n++;
    if (it === item) break;
  }
  return n > 1 ? `${n}.${kw}` : kw;
}

function actionsFor(item, worn) {
  if (worn) return [['Remove', 'remove'], ['Examine', 'examine']];
  const t = item.type;
  const a = [];
  if (t === 'weapon') a.push(['Wield', 'wield']);
  else if (t === 'armor' || t === 'worn' || item.slot) a.push(['Wear', 'wear']);
  else if (t === 'light') a.push(['Hold', 'hold']);
  if (t === 'potion') a.push(['Quaff', 'quaff']);
  if (t === 'food') a.push(['Eat', 'eat']);
  if (t === 'drink') a.push(['Drink', 'drink']);
  if (t === 'scroll') a.push(['Recite', 'recite']);
  if (t === 'wand') a.push(['Zap', 'zap']);
  if (t === 'staff') a.push(['Brandish', 'brandish']);
  if (t === 'note') a.push(['Read', 'read']);
  if (t === 'container') a.push(['Look inside', 'look in']);
  a.push(['Examine', 'examine'], ['Drop', 'drop']);
  return a;
}

function tooltip(item) {
  const r = item.set_id ? 'set' : (item.rarity || 'common');
  const rows = [];
  rows.push(`<div class="tt-name" style="color:${RARITY[r] || RARITY.common}">${esc(item.short || item.name)}</div>`);
  rows.push(`<div class="tt-sub">${esc(r)} ${esc(item.type || '')}${item.slot ? ` · ${esc(String(item.slot).replace(/\d$/, ''))}` : ''}${item.level ? ` · level ${item.level}` : ''}</div>`);
  if (item.damage_dice) rows.push(`<div>Damage ${esc(item.damage_dice)}${item.weapon_type ? ` (${esc(item.weapon_type)})` : ''}</div>`);
  if (item.armor) rows.push(`<div>Armour ${esc(item.armor)}</div>`);
  for (const a of item.affects || []) {
    const loc = a.location || a.stat || a.type || a.name, mod = a.modifier ?? a.value ?? a.amount;
    if (loc && mod != null) rows.push(`<div class="tt-aff">${mod > 0 ? '+' : ''}${esc(mod)} ${esc(String(loc).replace(/_/g, ' '))}</div>`);
  }
  for (const p of item.procs || []) rows.push(`<div class="tt-proc">${esc(p)}</div>`);
  const foot = [item.weight ? `${item.weight} lb` : '', item.cost ? `${item.cost} gold` : ''].filter(Boolean).join(' · ');
  if (foot) rows.push(`<div class="tt-foot">${esc(foot)}</div>`);
  return rows.join('');
}

export function createInventory() {
  const root = $('#inventory');
  const doll = root.querySelector('.inv-doll'), bag = root.querySelector('.inv-bag');
  const tip = $('#item-tip'), menu = $('#item-menu');
  let player = null, open = false, sig = '';

  const icon = (item, size = 88) => {
    const c = document.createElement('canvas');
    c.width = c.height = size;
    try { if (MH.itemIcons) MH.itemIcons.intoCanvas(c, item); } catch (_) {}
    return c;
  };
  const run = (verb, item, list) => {
    MH.sendCommand(`${verb} ${keywordFor(item, list)}`);
    sound.play({ wear: 'equip', wield: 'draw', hold: 'equip', remove: 'cloth', drop: 'ui_drop', sell: 'coins' }[verb] || 'ui_click');
    // wearing and dropping do not move you, so no map push follows: ask for one
    setTimeout(() => MH.refreshState && MH.refreshState(), 450);
  };
  function showMenu(e, item, worn, list) {
    menu.innerHTML = actionsFor(item, worn).map(([label, verb]) => `<button data-v="${verb}">${label}</button>`).join('');
    menu.classList.remove('hidden');
    menu.style.left = `${Math.min(e.clientX, innerWidth - 160)}px`;
    menu.style.top = `${Math.min(e.clientY, innerHeight - 220)}px`;
    menu.querySelectorAll('button').forEach(b => b.addEventListener('click', () => { menu.classList.add('hidden'); run(b.dataset.v, item, list); }));
  }
  function cell(item, worn, list, label) {
    const d = document.createElement('div');
    d.className = 'inv-cell' + (item ? '' : ' empty');
    if (!item) { d.innerHTML = `<span>${label || ''}</span>`; return d; }
    const r = item.set_id ? 'set' : (item.rarity || 'common');
    d.style.borderColor = RARITY[r] || RARITY.common;
    d.appendChild(icon(item));
    d.addEventListener('mouseenter', e => { tip.innerHTML = tooltip(item); tip.classList.remove('hidden'); place(e); });
    d.addEventListener('mousemove', place);
    d.addEventListener('mouseleave', () => tip.classList.add('hidden'));
    d.addEventListener('click', e => { e.stopPropagation(); showMenu(e, item, worn, list); });
    d.addEventListener('dblclick', e => { e.stopPropagation(); menu.classList.add('hidden'); run(actionsFor(item, worn)[0][1], item, list); });
    return d;
  }
  function place(e) {
    tip.style.left = `${Math.min(e.clientX + 16, innerWidth - 260)}px`;
    tip.style.top = `${Math.min(e.clientY + 12, innerHeight - tip.offsetHeight - 10)}px`;
  }
  function render() {
    if (!player || !open) return;
    const eq = player.equipment || {}, inv = player.inventory || [];
    const nsig = JSON.stringify([eq, inv.map(i => i.name + i.rarity), player.gold]);
    if (nsig === sig) return;
    sig = nsig;
    doll.innerHTML = '';
    const wornList = Object.values(eq);
    for (const [slot, label] of SLOTS) {
      const w = document.createElement('div');
      w.className = 'inv-slot';
      w.appendChild(cell(eq[slot], true, wornList, label));
      doll.appendChild(w);
    }
    bag.innerHTML = '';
    const cells = Math.max(30, Math.ceil(inv.length / 6) * 6);
    for (let i = 0; i < cells; i++) bag.appendChild(cell(inv[i], false, inv));
    root.querySelector('.inv-gold').textContent = `${(player.gold || 0).toLocaleString()} gold`;
    root.querySelector('.inv-count').textContent = `${inv.length} item${inv.length === 1 ? '' : 's'}`;
  }
  document.addEventListener('click', () => menu.classList.add('hidden'));
  root.querySelector('.inv-close').addEventListener('click', () => toggle(false));
  function toggle(on = !open) {
    open = on;
    root.classList.toggle('hidden', !open);
    tip.classList.add('hidden'); menu.classList.add('hidden');
    if (open) { sig = ''; if (MH.refreshState) MH.refreshState(); render(); }
  }
  return {
    toggle,
    get open() { return open; },
    update(p) { player = p; render(); },
  };
}
