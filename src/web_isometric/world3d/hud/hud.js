// The 3D client's HUD: player frame, orbs and action bar, target frame, room/zone banner,
// toasts, chat log with command line, menu and settings. DOM over the WebGL canvas,
// driven by the shared net.js state (`map` payloads, `combat.update`, server text).
// Actions go out as bus events ('hud.attack', 'hud.ability', 'hud.flee') for main.js,
// which knows the target and plays the hero's animation.
import { createInventory } from './inventory.js';
import { createCharacter } from './character.js';
import { createSpellbook } from './spellbook.js';
import { createTrainer } from './trainer.js';
import { createParty } from './party.js';
import { createQuest } from './quest.js';
import { createJournal } from './journal.js';
import { abilityIcon, uiIcon } from './icons.js';
import { classPortrait, creaturePortrait } from './portrait.js';
import { SLOTS, cleanBar, defaultBar, placeNew, putOnBar, takeOffBar, diffAbilities, usable, costLine, rankOf } from '../abilities.js';
import { conOf } from '../targeting.js';
import { recipeFor } from '../abilityfx.js';
import { RECIPES } from '../abilityfx-table.js';
import { sound } from '../audio.js';
const $ = s => document.querySelector(s);
const ls = { get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} } };

// class kits in the order they unlock (same order as the 2D client's action bar)
export const KIT = {
  warrior: ['bash', 'cleave', 'kick', 'execute', 'rally', 'rescue', 'charge'],
  paladin: ['censure', 'order_verdict', 'holy_smite', 'absolution', 'halo_of_reckoning', 'turn_undead', 'rescue', 'bash'],
  ranger: ['truesight_shot', 'wildbond_strike', 'loosing_storm', 'quarry_mark', 'call_lightning'],
  thief: ['backstab', 'circle', 'trip', 'low_blow', 'pocket_sand', 'jackpot'],
  assassin: ['backstab', 'mark', 'expose', 'vital', 'feint', 'execute_contract', 'fade'],
  mage: ['magic_missile', 'fireball', 'lightning_bolt', 'chill_touch', 'sleep', 'towerbolt'],
  necromancer: ['soul_bolt', 'chill_touch', 'soul_siphon', 'animate_dead', 'soul_reap'],
  cleric: ['holy_smite', 'cure_light', 'heal', 'turn_undead', 'bless', 'flamestrike'],
  bard: ['mockery', 'fascinate', 'crescendo', 'discordant_note', 'sleep'],
};
const SELF = new Set(['rally', 'cure_light', 'heal', 'bless', 'fade', 'absolution', 'halo_of_reckoning', 'animate_dead', 'crescendo']);
// an ability's painted icon (hud/icons.js) as an <img>, in the hero's class's colours
let iconClass = '';
const iconTypes = new Map();
export const ICON = id => `<img class="ic" alt="" draggable="false" src="${abilityIcon(id, iconClass, { type: iconTypes.get(id) || 'skill' })}">`;
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createHud() {
  const els = {
    pf: $('#player-frame'), tf: $('#target-frame'), banner: $('#banner'), toasts: $('#toasts'),
    mm: $('#minimap'), ab: $('#actionbar'), chat: $('#chat'), log: $('#log'), input: $('#chat-input'),
    menu: $('#menu'), settings: $('#settings'), slots: $('#slots'),
  };
  const st = { player: null, abilities: null, byId: new Map(), bar: new Array(SLOTS).fill(null), custom: false, barEdited: 0,
    barSig: '', glow: new Set(), cooldowns: {}, cdAt: 0, target: null, history: [], hi: -1 };
  const inventory = createInventory();
  const character = createCharacter();
  const spellbook = createSpellbook($('#spellbook'), {
    icon: id => ICON(id),
    onUse: id => use(id),
    onAdd: id => { const i = st.bar.indexOf(null); if (i < 0) toast('Your bar is full: drag the ability onto a slot'); else editBar(putOnBar(st.bar, id, i)); },
    onDragStart: () => els.ab.classList.add('dragging'),
    onDragEnd: () => els.ab.classList.remove('dragging'),
  });
  const trainer = createTrainer($('#trainer'), { icon: id => ICON(id), onTrain: id => MH.sendCommand(`practice ${id}`) });
  const party = createParty({
    frames: $('#party'), invite: $('#group-invite'), loot: $('#loot-roll'),
    onTarget: name => MH.bus.emit('hud.targetPlayer', name),
    onMenu: (name, x, y, leader) => MH.bus.emit('hud.partyMenu', { name, x, y, leader }),
    toast: msg => toast(msg),
  });
  // the marquee quest: the offer card, the embark popup, the tracker under the minimap
  const quest = createQuest({
    card: $('#quest-card'), embark: $('#quest-embark'), tracker: $('#quest-tracker'),
    toast: msg => toast(msg), onMark: vnum => MH.bus.emit('quest.mark', vnum),
  });

  const journal = createJournal($('#journal'), { toast: msg => toast(msg) });

  // ---- scale ----
  function applyScale() {
    const pref = ls.get('mh3d_ui') || 'auto';
    const w = window.innerWidth;
    const v = pref === 'auto' ? (w >= 1800 ? 1.05 : w >= 1400 ? 0.95 : w >= 1000 ? 0.85 : 0.72) : Number(pref) || 1;
    document.documentElement.style.setProperty('--ui', v);
  }
  window.addEventListener('resize', applyScale);
  applyScale();

  function showGame(on) {
    for (const k of ['pf', 'mm', 'ab', 'chat', 'menu']) els[k].classList.toggle('hidden', !on);
    fitChat();
    els.log.scrollTop = els.log.scrollHeight;
  }
  // the chat sits left of the action bar and never runs under it
  function fitChat() {
    if (els.ab.classList.contains('hidden')) return;
    const left = els.ab.getBoundingClientRect().left;
    const ui = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--ui')) || 1;
    els.chat.style.width = window.innerWidth <= 900 ? '' : `${Math.max(240, Math.min(430 * ui, left - 14 - 12))}px`;
  }
  window.addEventListener('resize', () => requestAnimationFrame(fitChat));

  // ---- player ----
  const pct = (a, b) => `${Math.max(0, Math.min(100, (b ? a / b : 0) * 100))}%`;
  // a vitals bar: the fill, a pale ghost that drains behind it after a wound, the numbers
  function vbar(el, cur, max, label = '') {
    const w = pct(cur, max);
    el.querySelector('b').style.width = w;
    const ghost = el.querySelector('i');
    if (ghost) ghost.style.width = w;
    el.querySelector('span').textContent = max ? `${label}${Number(cur || 0).toLocaleString()} / ${Number(max).toLocaleString()}` : '';
    el.classList.toggle('low', !!max && cur / max <= 0.3);
  }
  let portraitFor = '', lastLevel = 0;
  // a moment: a title over light rays (a level gained, a fall)
  let momentTimer = 0;
  function moment({ kicker = '', title = '', sub = '', tone = '' }) {
    const m = $('#moment');
    m.querySelector('.mo-kicker').textContent = kicker;
    m.querySelector('.mo-title').textContent = title;
    m.querySelector('.mo-sub').textContent = sub;
    m.className = tone;
    void m.offsetWidth;
    m.classList.add('in');
    clearTimeout(momentTimer);
    momentTimer = setTimeout(() => m.classList.add('hidden'), 4300);
  }
  function fallen() {
    document.documentElement.classList.add('fallen');
    moment({ kicker: 'the mist takes you', title: 'You have fallen', sub: 'You wake where your journey last found shelter…', tone: 'fall' });
    setTimeout(() => document.documentElement.classList.remove('fallen'), 4200);
  }
  function setPlayer(p) {
    if (!p) return;
    st.player = p;
    // a level gained: the moment, and the world answers with light (main.js)
    if (lastLevel && p.level > lastLevel) {
      moment({ kicker: `${String(p.char_class || '').toLowerCase()} · level ${p.level}`, title: 'Level Up!', sub: 'Your strength grows. New paths open before you.' });
      MH.bus.emit('hud.levelup', p.level);
    }
    lastLevel = p.level || lastLevel;
    const cls = String(p.char_class || '').toLowerCase();
    if (cls && cls !== iconClass) { iconClass = cls; st.barSig = ''; }
    els.pf.querySelector('.name').textContent = p.name || '';
    els.pf.querySelector('.cls').textContent = `${(p.race || '').replace(/_/g, ' ')} ${p.char_class || ''}`.trim();
    els.pf.querySelector('.ini').textContent = (p.name || '?')[0].toUpperCase();
    els.pf.querySelector('.lvl').textContent = p.level || 1;
    els.pf.dataset.cls = cls;
    if (cls && portraitFor !== cls) {
      portraitFor = cls;
      classPortrait(cls).then(url => { if (url && portraitFor === cls) { const img = els.pf.querySelector('.face'); img.src = url; img.classList.add('on'); } });
    }
    vbar(els.pf.querySelector('.vbar.hp'), p.hp, p.max_hp);
    const res = p.resource && p.resource.max ? { cur: p.resource.value, max: p.resource.max, name: p.resource.name }
      : { cur: p.mana, max: p.max_mana, name: 'Mana' };
    vbar(els.pf.querySelector('.vbar.mp'), res.cur, res.max);
    els.pf.querySelector('.vbar.mp').dataset.res = String(res.name || 'mana').toLowerCase();
    document.documentElement.classList.toggle('hp-low', !!p.max_hp && p.hp / p.max_hp <= 0.3 && p.hp > 0);
    const hpOrb = els.ab.querySelector('.orb.hp'), mpOrb = els.ab.querySelector('.orb.mp');
    hpOrb.querySelector('.fill').style.height = pct(p.hp, p.max_hp);
    hpOrb.querySelector('.val').textContent = `${p.hp}/${p.max_hp}`;
    mpOrb.querySelector('.fill').style.height = pct(res.cur, res.max);
    mpOrb.querySelector('.val').textContent = `${res.cur}/${res.max}`;
    mpOrb.querySelector('.lab').textContent = res.name;
    mpOrb.dataset.res = String(res.name || 'mana').toLowerCase();
    const floor = p.exp_floor || 0, next = p.exp_to_level || 0;
    const capped = !next || next - floor > 1e9;
    $('#xpbar b').style.width = capped ? '100%' : next > floor ? pct((p.exp || 0) - floor, next - floor) : '0%';
    $('#xpbar').title = capped ? 'Max level' : `Experience: ${p.exp || 0} / ${next}`;
    // buffs and debuffs: an icon each, a ring that empties as it wears off
    renderBuffs(Array.isArray(p.affects) ? p.affects : []);
    inventory.update(p);
    character.update(p);
    st.cooldowns = p.cooldowns || {};
    st.cdAt = performance.now();
    buildBar(p);
    paintCooldowns();
  }

  // ---- buffs ----
  const TICK_S = 6;          // an affect tick (config.AFFECT_TICK_SECONDS)
  const BAD = /poison|curse|blind|slow|weak|stun|bleed|burn|fear|snare|root|shatter|mark|expose|sunder|disease|plague|silence|entangle|sleep/;
  let buffSig = '';
  function renderBuffs(aff) {
    const list = aff.filter(a => a && (a.name || a.spell)).slice(0, 12);
    const nsig = JSON.stringify(list.map(a => [a.name, a.remaining, a.duration]));
    if (nsig === buffSig) return;
    buffSig = nsig;
    $('#buffs').innerHTML = list.map(a => {
      const id = String(a.name || a.spell).toLowerCase();
      const base = id.replace(/_(invuln|damage|speed|mend|crit|stealth|haste|stun|regen|bonus)$/, '');
      const bad = BAD.test(id);
      const left = a.remaining != null ? a.remaining : a.duration;
      const frac = a.duration ? Math.max(0, Math.min(1, (left || 0) / a.duration)) : 1;
      const secs = left != null ? Math.max(0, Math.round(left * TICK_S)) : null;
      const label = base.replace(/_/g, ' ');
      return `<div class="buff${bad ? ' bad' : ''}" style="--left:${frac}" data-tip-title="${esc(label)}" data-tip-sub="${bad ? 'Harmful' : 'Helpful'}${secs != null ? ` · about ${secs >= 60 ? `${Math.round(secs / 60)} min` : `${secs} s`} left` : ''}">
        <img alt="" src="${abilityIcon(base, iconClass, { type: 'spell' })}"><span>${secs != null && secs < 60 ? secs : ''}</span></div>`;
    }).join('');
  }

  // ---- the tooltip card: abilities, buffs, menu buttons ----
  const tip = $('#tipcard');
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.classList.remove('hidden');
    const r = tip.getBoundingClientRect();
    const left = Math.min(window.innerWidth - r.width - 8, Math.max(8, x - r.width / 2));
    const top = y - r.height - 14 < 8 ? y + 22 : y - r.height - 14;
    tip.style.left = `${left}px`; tip.style.top = `${top}px`;
  }
  function hideTip() { tip.classList.add('hidden'); }
  function abilityTip(a, key) {
    const book = a.pct > 0 ? `<div class="tc-bar"><b style="width:${Math.min(100, a.pct)}%"></b></div>` : '';
    const rank = a.known ? `${rankOf(a.pct)} · ${a.pct}%` : a.quest ? `Earned through ${a.quest}` : `Unlocks at level ${a.level}`;
    return `<div class="tc-head"><img class="tc-ic" src="${abilityIcon(a.id, iconClass, { type: a.type })}">
        <div><div class="tc-name">${esc(a.name)}</div><div class="tc-sub">${a.type === 'spell' ? 'Spell' : 'Skill'}${a.marquee ? ' · ★ marquee' : ''} · ${esc(rank)}</div></div></div>
      ${book}<div class="tc-desc">${esc(a.desc || '')}</div>
      <div class="tc-meta">${esc(costLine(a))}${key ? ` · key <b>${esc(key)}</b>` : ''}</div>`;
  }
  // anything with data-tip-title shows a small card
  document.addEventListener('mouseover', e => {
    const el = e.target.closest && e.target.closest('[data-tip-title]');
    if (!el) return;
    const r = el.getBoundingClientRect();
    showTip(`<div class="tc-name">${esc(el.dataset.tipTitle)}</div>${el.dataset.tipSub ? `<div class="tc-sub">${esc(el.dataset.tipSub)}</div>` : ''}`, r.left + r.width / 2, r.top);
  });
  document.addEventListener('mouseout', e => { if (e.target.closest && e.target.closest('[data-tip-title], .slot')) hideTip(); });

  // ---- action bar: Attack (F), your own 16 slots (1-8, Shift+1-8), Flee ----
  // Abilities come from the payload (`abilities`, `bar`: see abilities.js). A character who
  // never arranged the bar gets the class's usual order; once you drag something, the bar is
  // yours and is kept with the character (`webbar`). New abilities glow into free slots.
  const keyOf = i => i < 8 ? String(i + 1) : `⇧${i - 7}`;
  // the class's ability book (what each ability is, costs and unlocks at) comes once per class
  // from /abilitybook; the payload only carries how well you know each one (skills, spells)
  const books = new Map();
  function bookFor(cls) {
    if (!books.has(cls)) {
      books.set(cls, null);
      fetch(`/abilitybook?cls=${encodeURIComponent(cls)}`).then(r => (r.ok ? r.json() : null)).catch(() => null).then(b => {
        if (!b || !Array.isArray(b.abilities)) return;
        books.set(cls, b.abilities);
        if (st.player && String(st.player.char_class || '').toLowerCase() === cls) buildBar(st.player);
      });
    }
    return books.get(cls);
  }
  function abilityList(p) {
    const cls = String(p.char_class || '').toLowerCase();
    const learned = { ...(p.skills || {}), ...(p.spells || {}) };
    const book = bookFor(cls);
    if (book) return book.map(a => ({ ...a, pct: learned[a.id] || 0, known: (learned[a.id] || 0) > 0 }));
    // until the book arrives: what the class kit and the learned lists say
    const spells = new Set(Object.keys(p.spells || {}));
    return (KIT[cls] || []).map((id, i) => ({ id, name: id.replace(/_/g, ' '), type: spells.has(id) ? 'spell' : 'skill',
      pct: learned[id] || 0, known: !!learned[id], level: i + 1, target: SELF.has(id) ? 'self' : 'enemy' }));
  }
  function buildBar(p) {
    const cls = String(p.char_class || '').toLowerCase();
    const list = abilityList(p);
    const prev = st.abilities && st.abilities.fromBook === !!books.get(cls) ? st.abilities : null, before = st.bar;
    list.fromBook = !!books.get(cls);
    st.abilities = list;
    st.byId = new Map(list.map(a => [a.id, a]));
    for (const a of list) iconTypes.set(a.id, a.type || 'skill');
    // a bar you just changed outlives payloads the server sent before it had your change
    if (performance.now() - st.barEdited > 4000) {
      st.custom = Array.isArray(p.bar) && p.bar.some(Boolean);
      st.bar = st.custom ? cleanBar(p.bar, list) : defaultBar(list, KIT[cls] || []);
    }
    if (prev) {
      const { learned, improved } = diffAbilities(prev, list);
      if (learned.length) {
        // into free slots, without moving what is already on your keys
        const r = placeNew(st.custom ? st.bar : cleanBar(before, list), learned.filter(id => usable(st.byId.get(id))));
        if (r.placed.length || !st.custom) editBar(r.bar, true);
        for (const id of learned) {
          const a = st.byId.get(id), i = st.bar.indexOf(id);
          toast(`You learned ${a ? a.name : id}${a && a.passive ? ' (passive)' : i >= 0 ? ` — on your bar (${keyOf(i)})` : ' — open your spellbook (K)'}`);
          st.glow.add(id);
          setTimeout(() => { st.glow.delete(id); renderBar(); }, 9000);
        }
      }
      for (const imp of improved) tick(imp.id, imp.to - imp.from);
    }
    renderBar();
    spellbook.update(list, st.bar, p.level);
    trainer.update({ ...p, abilities: list });
  }
  // send the bar to the server (kept with the character)
  function editBar(bar, quiet) {
    st.bar = bar;
    st.custom = true;
    st.barEdited = performance.now();
    MH.sendCommand(`webbar ${bar.map(x => x || '-').join(' ')}`, false);
    renderBar();
    spellbook.update(st.abilities, st.bar, st.player && st.player.level);
    if (!quiet) requestAnimationFrame(fitChat);
  }
  function slotHtml(i) {
    const id = st.bar[i], a = id && st.byId.get(id), key = keyOf(i);
    if (!a) return `<div class="slot empty" data-i="${i}" data-tip-title="An empty slot" data-tip-sub="Drag an ability here from your spellbook (K)"><span class="key">${key}</span></div>`;
    return `<div class="slot${st.glow.has(id) ? ' glow' : ''}${a.marquee ? ' marquee' : ''}" data-i="${i}" data-id="${a.id}" draggable="true">`
      + `${ICON(a.id)}<span class="key">${key}</span><div class="cd"><i></i><span></span></div></div>`;
  }
  function renderBar() {
    const sig = JSON.stringify([st.bar, [...st.glow], st.bar.map(id => id && st.byId.has(id))]);
    if (sig === st.barSig) return;
    st.barSig = sig;
    const row = (from, to) => Array.from({ length: to - from }, (_, k) => slotHtml(from + k)).join('');
    els.slots.innerHTML = `<div class="bar-row shift${st.bar.slice(8).some(Boolean) ? '' : ' unused'}">${row(8, 16)}</div>`
      + `<div class="bar-row main"><div class="slot fixed attack" data-act="attack" data-tip-title="Attack" data-tip-sub="Swing at your target — or press F (or Space)"><img class="ic" alt="" src="${uiIcon('sword', { size: 96 })}"><span class="key">F</span></div>`
      + `${row(0, 8)}<div class="slot fixed flee" data-act="flee" data-tip-title="Flee" data-tip-sub="Break off the fight and run"><img class="ic" alt="" src="${uiIcon('flee', { size: 96, color: '#d8e6f0', glow: 'rgba(160,200,240,.6)' })}"></div></div>`;
    els.slots.querySelectorAll('.slot').forEach(el => {
      const i = el.dataset.i != null ? +el.dataset.i : -1;
      el.addEventListener('click', () => use(el.dataset.act || st.bar[i]));
      if (el.dataset.id) {
        el.addEventListener('mouseenter', () => {
          const a = st.byId.get(el.dataset.id);
          if (!a) return;
          const r = el.getBoundingClientRect();
          showTip(abilityTip(a, keyOf(i)), r.left + r.width / 2, r.top);
          MH.bus.emit('hud.abilityHover', { id: a.id });
        });
        el.addEventListener('mouseleave', () => { hideTip(); MH.bus.emit('hud.abilityHover', null); });
      }
      if (i < 0) return;
      el.addEventListener('contextmenu', e => {
        e.preventDefault();
        if (st.bar[i]) MH.bus.emit('hud.slotMenu', { x: e.clientX, y: e.clientY, slot: i, id: st.bar[i], name: (st.byId.get(st.bar[i]) || {}).name });
      });
      el.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/x-ability', st.bar[i]);
        e.dataTransfer.setData('text/x-slot', String(i));
        e.dataTransfer.effectAllowed = 'move';
        els.ab.classList.add('dragging');
      });
      // dropped nowhere: off the bar
      el.addEventListener('dragend', e => {
        els.ab.classList.remove('dragging');
        if (e.dataTransfer.dropEffect === 'none' && st.bar[i]) {
          const a = st.byId.get(st.bar[i]);
          editBar(takeOffBar(st.bar, i));
          toast(`${a ? a.name : 'That'} is off your bar (it stays in your spellbook, K)`);
        }
      });
      el.addEventListener('dragover', e => { if (e.dataTransfer.types.includes('text/x-ability')) { e.preventDefault(); el.classList.add('over'); } });
      el.addEventListener('dragleave', () => el.classList.remove('over'));
      el.addEventListener('drop', e => {
        e.preventDefault();
        el.classList.remove('over');
        els.ab.classList.remove('dragging');
        const id = e.dataTransfer.getData('text/x-ability');
        if (id && st.byId.has(id)) editBar(putOnBar(st.bar, id, i));
      });
    });
    requestAnimationFrame(fitChat);
  }
  // "+2%": an ability on the bar grew
  function tick(id, by) {
    const el = els.slots.querySelector(`.slot[data-id="${id}"]`);
    if (!el || !(by > 0)) return;
    const t = document.createElement('div');
    t.className = 'tick';
    t.textContent = `+${by}%`;
    el.appendChild(t);
    setTimeout(() => t.remove(), 1600);
  }
  // use an ability by id (bar, spellbook, right-click menu) or the fixed Attack/Flee
  function use(id) {
    if (!id) return;
    const el = els.slots.querySelector(id === 'attack' || id === 'flee' ? `.slot[data-act="${id}"]` : `.slot[data-id="${id}"]`);
    if (el) { el.classList.add('flash'); setTimeout(() => el.classList.remove('flash'), 180); }
    if (id === 'attack') { MH.bus.emit('hud.attack'); return; }
    if (id === 'flee') { MH.bus.emit('hud.flee'); return; }
    const a = st.byId.get(id);
    if (a && !a.known) { toast(`${a.name} unlocks at level ${a.level}`); return; }
    // aimed at a foe (the target), at a friend (a targeted player, else you), or at nothing
    // (yourself, the room, an object you name): sent without a target
    const aim = a ? a.target || 'enemy' : SELF.has(id) ? 'self' : 'enemy';
    MH.bus.emit('hud.ability', { id, spell: a ? a.type === 'spell' : false, self: aim !== 'enemy' && aim !== 'ally', ally: aim === 'ally' });
  }
  // a staggered foe: the bar's heaviest ready attacks glow for a moment (combatcues.js)
  function suggestStrike() {
    const now = (performance.now() - st.cdAt) / 1000;
    const weight = id => {
      const r = recipeFor(RECIPES, id, iconClass, {});
      return (r.flags.has('heavy') ? 2 : 0) + (r.flags.has('shake+') ? 2 : r.flags.has('shake') ? 1 : 0) + (r.flags.has('stop') ? 1 : 0) + (r.land && r.land.big ? 1 : 0);
    };
    const ready = st.bar.filter(Boolean).map(id => st.byId.get(id))
      .filter(a => a && a.known && !a.passive && (a.target || 'enemy') === 'enemy' && (st.cooldowns[a.id] || 0) - now <= 0.05)
      .sort((x, y) => weight(y.id) - weight(x.id));
    for (const a of ready.slice(0, 2)) {
      const el = els.slots.querySelector(`.slot[data-id="${a.id}"]`);
      if (el) { el.classList.add('suggest'); setTimeout(() => el.classList.remove('suggest'), 2400); }
    }
  }
  // the server says an ability grew (mastery.py): tick it now, before the next payload
  MH.bus.on('ability.improve', ({ id, pct }) => {
    const a = st.byId.get(id);
    if (!a || !(pct > (a.pct || 0))) return;
    const by = pct - (a.pct || 0);
    a.pct = pct;
    const p = st.player;
    if (p) for (const k of ['skills', 'spells']) if (p[k] && id in p[k]) p[k][id] = pct;
    tick(id, by);
    spellbook.update(st.abilities, st.bar, p && p.level);
    if (p) trainer.update({ ...p, abilities: st.abilities });
  });
  const cdTotal = new Map();             // how long each running cooldown was when it started
  function paintCooldowns() {
    const elapsed = (performance.now() - st.cdAt) / 1000;
    const p = st.player;
    els.slots.querySelectorAll('.slot[data-id]').forEach(slot => {
      const id = slot.dataset.id;
      const left = (st.cooldowns[id] || 0) - elapsed;
      const cd = slot.querySelector('.cd');
      if (!cd) return;
      if (left > 0.05) {
        if (!cdTotal.has(id) || cdTotal.get(id) < left) cdTotal.set(id, Math.max(left, (st.byId.get(id) || {}).cd || left));
        slot.classList.add('cooling');
        cd.style.setProperty('--cd', Math.min(1, left / (cdTotal.get(id) || left)));
        cd.querySelector('span').textContent = left >= 10 ? Math.ceil(left) : left.toFixed(1);
      } else if (slot.classList.contains('cooling')) {
        slot.classList.remove('cooling');
        cdTotal.delete(id);
        slot.classList.add('ready');
        setTimeout(() => slot.classList.remove('ready'), 700);
      }
      // a spell you haven't the mana for
      const a = st.byId.get(id);
      const short = !!(a && a.type === 'spell' && a.cost && p && !(p.resource && p.resource.max) && (p.mana || 0) < a.cost);
      slot.classList.toggle('nores', short);
    });
  }
  setInterval(paintCooldowns, 100);

  // ---- ranges: the target frame shows the distance; slots out of reach turn red ----
  let ranges = null, lastDist = null;
  function setRanges(d) { ranges = d; }
  function abilityRange(id) {
    if (!ranges) return null;
    if (id === 'attack') { const a = ranges.auto[String(st.player && st.player.char_class || '').toLowerCase()]; return a ? a.range : ranges.melee; }
    const ab = ranges.abilities[id], info = st.byId.get(id);
    if (ab) return /^(self|nova)/.test(ab.shape) ? null : ab.range;
    if (info && info.target === 'self') return null;
    return info && info.type === 'spell' ? ranges.spellDefault : ranges.melee;
  }
  function setDistance(d, sameRoom) {
    const sub = els.tf.querySelector('.tdist') || (() => { const x = document.createElement('div'); x.className = 'tdist'; els.tf.appendChild(x); return x; })();
    if (d == null || els.tf.classList.contains('hidden')) { sub.textContent = ''; lastDist = null; return; }
    const r = Math.round(d * 2) / 2;
    if (r === lastDist) return;
    lastDist = r;
    const reach = abilityRange('attack');
    const near = reach != null && d <= reach + 0.3 && sameRoom;
    const hostile = st.target && st.target.hostile;
    sub.textContent = `${r.toFixed(r < 10 ? 1 : 0)} m${reach != null ? (near ? (hostile && !MH.state.inCombat ? ' · in reach — press F to attack' : ' · in reach') : ` · reach ${reach} m`) : ''}`;
    sub.className = 'tdist' + (reach != null && d <= reach + 0.3 && sameRoom ? ' ok' : '');
    els.slots.querySelectorAll('.slot[data-id], .slot[data-act="attack"]').forEach(el => {
      const rng = abilityRange(el.dataset.id || 'attack');
      el.classList.toggle('far', rng != null && (d > rng + 0.3 || !sameRoom));
    });
  }

  // ---- target ----
  let targetKey = '';
  function setTarget(t) {
    st.target = t;
    els.tf.classList.toggle('hidden', !t);
    if (!t) { targetKey = ''; targetCast(null); return; }
    const me = st.player ? st.player.level || 1 : 1;
    const con = t.kind === 'player' ? { key: 'ally', label: 'Player' } : conOf(t.level || 1, me);
    const kind = t.kind === 'player' ? 'ally' : t.hostile ? 'hostile' : (t.shopkeeper || t.trainer) ? 'npc' : 'neutral';
    els.tf.className = `hud panel ornate ${kind} con-${con.key}${t.boss ? ' boss' : ''}`;
    els.tf.querySelector('.tname').textContent = t.name;
    els.tf.querySelector('.lvl').textContent = t.kind === 'player' ? (t.level || '') : (t.level || '?');
    const role = t.shopkeeper ? ' · shopkeeper' : t.trainer ? ' · trainer' : t.boss ? ' · boss' : '';
    els.tf.querySelector('.tsub').textContent = `${t.kind === 'player' ? `Level ${t.level || '?'} ${t.char_class || ''}` : `Level ${t.level || '?'} · ${con.label}`}${role}`;
    vbar(els.tf.querySelector('.vbar.hp'), t.maxHp ? t.hp : 1, t.maxHp || 1);
    if (!t.maxHp) els.tf.querySelector('.vbar.hp span').textContent = '';
    // its portrait, once per target
    const key = t.kind === 'player' ? `p:${t.name}` : `m:${t.id}`;
    if (key !== targetKey) {
      targetKey = key;
      const img = els.tf.querySelector('.face');
      img.classList.remove('on');
      targetCast(null);
      const shot = t.kind === 'player' ? classPortrait(t.char_class) : creaturePortrait(t);
      shot.then(url => { if (url && targetKey === key) { img.src = url; img.classList.add('on'); } });
    }
  }
  els.tf.querySelector('.tclose').addEventListener('click', () => MH.bus.emit('hud.untarget'));
  // the target gathers itself for a big blow: its wind-up as a cast bar ("Crushing Blow")
  let castTimer = 0;
  function targetCast(c) {
    const el = els.tf.querySelector('.tcast');
    clearTimeout(castTimer);
    if (!c) { el.classList.add('hidden'); return; }
    if (c.end) {
      el.classList.add(c.end === 'broken' ? 'broken' : 'landed');
      el.querySelector('em').textContent = c.end === 'broken' ? 'Interrupted!' : '';
      castTimer = setTimeout(() => el.classList.add('hidden'), 650);
      return;
    }
    el.className = 'tcast';
    el.querySelector('span').textContent = c.label || 'Winding up';
    el.querySelector('em').textContent = '';
    const b = el.querySelector('b');
    b.style.transition = 'none'; b.style.width = '0%';
    requestAnimationFrame(() => requestAnimationFrame(() => { b.style.transition = `width ${Math.max(0.3, (c.ms || 1500) / 1000)}s linear`; b.style.width = '100%'; }));
    castTimer = setTimeout(() => el.classList.add('hidden'), (c.ms || 1500) + 1200);
  }

  // ---- banner + toasts ----
  let bannerTimer = 0;
  function banner(room, zone) {
    els.banner.querySelector('.zone').textContent = zone || '';
    els.banner.querySelector('.room').textContent = room || '';
    els.banner.style.opacity = 1;
    clearTimeout(bannerTimer);
    bannerTimer = setTimeout(() => { els.banner.style.opacity = 0; }, zone ? 3200 : 1800);
  }
  function toast(msg) {
    if (!msg) return;
    sound.play('toast');
    const d = document.createElement('div');
    d.className = 'toast';
    d.textContent = msg;
    els.toasts.appendChild(d);
    while (els.toasts.children.length > 3) els.toasts.firstChild.remove();
    setTimeout(() => d.remove(), 2900);
  }

  // ---- chat log + command line ----
  const PROMPT = /^\s*<?\s*\d+\/\d+\s*hp\b[^\n]*>\s*$/i;
  let stick = true;
  els.log.addEventListener('scroll', () => { stick = els.log.scrollTop + els.log.clientHeight >= els.log.scrollHeight - 30; });
  // what kind of line it is, for the chat tabs (All / Group / Say / Tells)
  let tellFrom = '';
  function lineKind(text) {
    if (/^You tell the group,|^\w+ tells the group,/.test(text)) return 'group';
    const t = text.match(/^(\w+) tells you,/);
    if (t) { tellFrom = t[1]; return 'tell'; }
    if (/^You tell \w+,/.test(text)) return 'tell';
    if (/^You say,|^\w+ says,|^You say '|^\w+ says '/.test(text)) return 'say';
    return '';
  }
  function log(html, cls) {
    const atBottom = stick;
    const d = document.createElement('div');
    if (cls) { d.className = cls; d.textContent = html; } else d.innerHTML = html;
    const kind = lineKind(d.textContent.trim());
    if (kind) {
      d.classList.add(`l-${kind}`);
      const tab = document.querySelector(`#chat .chat-tabs [data-tab="${kind}"]`);
      if (tab && els.log.dataset.tab !== kind) tab.classList.add('new');
    }
    els.log.appendChild(d);
    while (els.log.childElementCount > 400) els.log.firstChild.remove();
    if (atBottom) els.log.scrollTop = els.log.scrollHeight;
  }
  MH.bus.on('terminal.output', ({ html }) => {
    if (!html || !MH.state.isLoggedIn) return;
    const plain = l => l.replace(/<[^>]+>/g, '').replace(/&gt;/g, '>').replace(/&lt;/g, '<').replace(/&amp;/g, '&');
    const lines = String(html).split(/\r?\n/).filter(l => plain(l).trim() && !PROMPT.test(plain(l)));
    if (lines.length) log(lines.join('\n'));
  });
  MH.bus.on('terminal.echo', cmd => log(`> ${cmd}`, 'cmd'));
  // tabs filter the log; the mode chip decides what Enter does with plain text
  document.querySelectorAll('#chat .chat-tabs button').forEach(b => b.addEventListener('click', () => {
    els.log.dataset.tab = b.dataset.tab;
    document.querySelectorAll('#chat .chat-tabs button').forEach(x => x.classList.toggle('on', x === b));
    b.classList.remove('new');
    els.log.scrollTop = els.log.scrollHeight;
  }));
  const MODES = ['cmd', 'say', 'group', 'tell'];
  let mode = 'cmd';
  const modeBtn = $('#chat-mode');
  function setMode(m) {
    mode = m;
    modeBtn.textContent = { cmd: 'Cmd', say: 'Say', group: 'Group', tell: tellFrom ? `→ ${tellFrom}` : 'Tell' }[m];
    els.input.placeholder = m === 'cmd' ? 'Press Enter to talk or type a command…' : m === 'tell' && !tellFrom ? 'Tell whom? Start with their name…'
      : `${m === 'say' ? 'Say' : m === 'group' ? 'Tell the group' : `Tell ${tellFrom}`} — or start with / for a command`;
  }
  modeBtn.addEventListener('click', () => setMode(MODES[(MODES.indexOf(mode) + 1) % MODES.length]));
  function framed(v) {
    if (mode === 'cmd' || v.startsWith('/')) return v.replace(/^\//, '');
    if (mode === 'say') return `say ${v}`;
    if (mode === 'group') return `gtell ${v}`;
    return tellFrom ? `tell ${tellFrom} ${v}` : `tell ${v}`;
  }
  els.input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const raw = els.input.value.trim(), v = raw && framed(raw);
      if (v) { MH.sendCommand(v); if (!MH.secretLine(raw)) { st.history.unshift(raw); st.history.length = Math.min(st.history.length, 50); } }
      st.hi = -1;
      els.input.value = '';
      els.input.blur();
      e.preventDefault();
    } else if (e.key === 'Escape') { els.input.value = ''; els.input.blur(); }
    else if (e.key === 'ArrowUp' && st.history.length) { st.hi = Math.min(st.hi + 1, st.history.length - 1); els.input.value = st.history[st.hi]; e.preventDefault(); }
    else if (e.key === 'ArrowDown') { st.hi = Math.max(st.hi - 1, -1); els.input.value = st.hi >= 0 ? st.history[st.hi] : ''; e.preventDefault(); }
    e.stopPropagation();
  });

  // ---- menu + settings ----
  els.menu.querySelectorAll('button[data-icon]').forEach(b => {
    b.innerHTML = `<img alt="" src="${uiIcon(b.dataset.icon, { size: 72 })}"><kbd>${esc(b.dataset.key || '')}</kbd>`;
    b.dataset.tipTitle = b.dataset.tip; b.dataset.tipSub = b.dataset.key ? `Key: ${b.dataset.key}` : '';
  });
  els.menu.querySelectorAll('button[data-cmd]').forEach(b => b.addEventListener('click', () => MH.sendCommand(b.dataset.cmd)));
  els.menu.querySelector('[data-act="settings"]').addEventListener('click', () => els.settings.classList.toggle('hidden'));
  els.menu.querySelector('[data-act="inventory"]').addEventListener('click', () => inventory.toggle());
  els.menu.querySelector('[data-act="character"]').addEventListener('click', () => character.toggle());
  els.menu.querySelector('[data-act="abilities"]').addEventListener('click', () => spellbook.toggle());
  els.menu.querySelector('[data-act="journal"]').addEventListener('click', () => journal.toggle());
  els.menu.querySelector('[data-act="map"]').addEventListener('click', () => MH.bus.emit('hud.map'));
  const syncSettings = () => {
    const q = ls.get('mh3d_quality') || 'high', u = ls.get('mh3d_ui') || 'auto';
    els.settings.querySelectorAll('[data-set="quality"] button').forEach(b => b.classList.toggle('on', b.dataset.v === q));
    els.settings.querySelectorAll('[data-set="ui"] button').forEach(b => b.classList.toggle('on', b.dataset.v === u));
  };
  els.settings.querySelectorAll('[data-set="quality"] button').forEach(b => b.addEventListener('click', () => {
    ls.set('mh3d_quality', b.dataset.v); syncSettings();
    toast('Graphics quality changes after a reload');
  }));
  els.settings.querySelectorAll('[data-set="ui"] button').forEach(b => b.addEventListener('click', () => {
    ls.set('mh3d_ui', b.dataset.v); applyScale(); syncSettings();
  }));
  els.settings.querySelector('[data-act="perf"]').addEventListener('click', () => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F3' })));
  els.settings.querySelector('[data-act="camreset"]').addEventListener('click', () => MH.bus.emit('hud.cameraReset'));
  els.settings.querySelector('[data-act="classic"]').addEventListener('click', () => window.open('/platformer', '_blank'));
  // sound: a master switch and a slider per bus (audio.js keeps them in localStorage)
  const muteBtn = els.settings.querySelector('[data-act="mute"]');
  const syncSound = () => {
    muteBtn.textContent = sound.muted ? 'Off' : 'On';
    muteBtn.classList.toggle('on', !sound.muted);
    els.settings.querySelectorAll('[data-vol]').forEach(r => { r.value = Math.round(sound.vol[r.dataset.vol] * 100); });
  };
  muteBtn.addEventListener('click', () => { sound.setMuted(!sound.muted); syncSound(); sound.play('ui_toggle'); });
  els.settings.querySelectorAll('[data-vol]').forEach(r => {
    r.addEventListener('input', () => sound.setVolume(r.dataset.vol, r.value / 100));
    // let go of a slider: hear what it sets
    r.addEventListener('change', () => sound.play({ sfx: 'hit', master: 'ui_confirm' }[r.dataset.vol] || 'ui_click'));
    r.addEventListener('keydown', e => e.stopPropagation());
  });
  syncSound();
  els.settings.querySelector('[data-act="logout"]').addEventListener('click', () => {
    if (!MH.logout()) toast('Finish the fight before you log out.');
  });
  syncSettings();

  // ---- sounds for windows and buttons (audio.js) ----
  // a window sounds as it opens and closes, however it was opened (a key, a button, a link)
  const WINDOW_SOUNDS = { inventory: ['bag_open', 'ui_close'], character: ['cloth', 'ui_close'], spellbook: ['book_open', 'book_close'],
    journal: ['book_open', 'book_close'], trainer: ['book_flip', 'ui_close'], settings: ['ui_open', 'ui_close'], bigmap: ['ui_open', 'ui_close'] };
  for (const [id, [on, off]] of Object.entries(WINDOW_SOUNDS)) {
    const el = document.getElementById(id);
    if (!el) continue;
    let was = !el.classList.contains('hidden');
    new MutationObserver(() => {
      const now = !el.classList.contains('hidden');
      if (now !== was) { was = now; sound.play(now ? on : off); }
    }).observe(el, { attributes: true, attributeFilter: ['class'] });
  }
  // a click on a window's buttons (not the action bar: abilities make their own sounds)
  document.addEventListener('click', e => {
    const b = e.target && e.target.closest && e.target.closest('.panel button, #create .pick, #login .btn');
    if (b && !b.closest('#actionbar') && !b.matches('[data-act="mute"]')) sound.play('ui_click');
  }, true);
  // gold changes hands: coins
  MH.bus.on('terminal.output', ({ text }) => {
    if (MH.state.isLoggedIn && /\b(?:you (?:get|receive|take|loot|sell|buy)|there (?:was|were))\b[^\n]*\b(?:gold|coins?)\b/i.test(text || '')) sound.play('coins');
  });

  // ---- keys (when not typing) ----
  window.addEventListener('keydown', e => {
    if (e.target && /INPUT|TEXTAREA|SELECT/.test(e.target.tagName)) return;
    if (!MH.state.isLoggedIn) return;
    const k = e.key;
    if (k === 'Enter') { els.input.focus(); e.preventDefault(); return; }
    if (k === 'f' || k === 'F' || k === ' ') { use('attack'); e.preventDefault(); return; }
    const digit = /^Digit([1-8])$/.exec(e.code || '');
    if (digit && !e.ctrlKey && !e.metaKey && !e.altKey) { use(st.bar[+digit[1] - 1 + (e.shiftKey ? 8 : 0)]); e.preventDefault(); return; }
    if (k === 'Escape') {
      const mapOpen = !$('#bigmap').classList.contains('hidden');
      if (inventory.open || character.open || spellbook.open || trainer.open || journal.open || mapOpen) {
        inventory.toggle(false); character.toggle(false); spellbook.toggle(false); trainer.toggle(false); journal.toggle(false);
        MH.bus.emit('hud.map', false); return;
      }
      MH.bus.emit('hud.untarget'); els.settings.classList.add('hidden'); return;
    }
    if ((k === 'i' || k === 'I') && !e.ctrlKey && !e.metaKey) { inventory.toggle(); e.preventDefault(); return; }
    if ((k === 'c' || k === 'C') && !e.ctrlKey && !e.metaKey) { character.toggle(); e.preventDefault(); return; }
    if ((k === 'k' || k === 'K') && !e.ctrlKey && !e.metaKey) { spellbook.toggle(); e.preventDefault(); return; }
    if (k === 'Tab') { MH.bus.emit('hud.cycleTarget'); e.preventDefault(); return; }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (k === 'l' || k === 'L') { journal.toggle(); e.preventDefault(); return; }
    if (k === 'm' || k === 'M') { MH.bus.emit('hud.map'); e.preventDefault(); return; }
    if (k === 'o' || k === 'O') { els.settings.classList.toggle('hidden'); e.preventDefault(); }
  });

  // ---- for the right-click menu ----
  // the bar's abilities that aim at someone (not heals on yourself, not shouts)
  function targetSkills() {
    return st.bar.map(id => id && st.byId.get(id)).filter(a => a && a.known && (a.target || 'enemy') === 'enemy')
      .map(a => ({ id: a.id, label: a.name, spell: a.type === 'spell' }));
  }
  function useAbility(id) { use(id); }
  function unslot(i) { if (st.bar[i]) editBar(takeOffBar(st.bar, i)); }
  function prefill(text) { els.input.value = text; els.input.focus(); }
  function openPanel(name) { if (name === 'inventory') inventory.toggle(true); else if (name === 'character') character.toggle(true); }
  function openTrainer(name) { trainer.toggle(true, name || ''); if (MH.refreshState) MH.refreshState(); }
  // whisper someone: the chat input set to tell them
  function whisper(name) { tellFrom = name; setMode('tell'); els.input.focus(); }

  return { showGame, setPlayer, setTarget, targetCast, moment, fallen, suggestStrike, setRanges, setDistance, banner, toast, log, targetSkills, useAbility, prefill, openPanel, openTrainer,
    spellbook, unslot, party, quest, whisper, get player() { return st.player; }, get bar() { return st.bar.slice(); } };
}
