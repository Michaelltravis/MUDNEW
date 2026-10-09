// Character sheet (C): the hero turning in a portrait, vitals, the six attributes, combat
// numbers, experience and active effects; a second tab lists skills and spells with their
// proficiency (the class's whole roster, unlearned ones dimmed). Everything comes from the
// map payload's player block; nothing here changes the character.
import { makeStage } from './stage.js';

const $ = s => document.querySelector(s);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ATTRS = [['str', 'Strength'], ['int', 'Intelligence'], ['wis', 'Wisdom'], ['dex', 'Dexterity'], ['con', 'Constitution'], ['cha', 'Charisma']];
const PRIME = { warrior: 'str', paladin: 'str', mage: 'int', necromancer: 'int', cleric: 'wis', thief: 'dex', ranger: 'dex', assassin: 'dex', bard: 'cha' };
const title = s => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

export function createCharacter() {
  const root = $('#character');
  const body = root.querySelector('.ch-body');
  let player = null, open = false, tab = 'overview', stage = null, shownClass = '', sig = '';

  root.querySelectorAll('.ch-tabs button').forEach(b => b.addEventListener('click', () => {
    tab = b.dataset.tab; sig = '';
    root.querySelectorAll('.ch-tabs button').forEach(x => x.classList.toggle('on', x === b));
    render();
  }));
  root.querySelector('.ch-close').addEventListener('click', () => toggle(false));

  const bar = (cur, max, cls) => `<div class="ch-bar ${cls}"><b style="width:${max ? Math.max(0, Math.min(100, cur / max * 100)) : 0}%"></b><span>${cur ?? 0} / ${max ?? 0}</span></div>`;

  function overview(p) {
    const cls = String(p.char_class || '').toLowerCase();
    const prime = PRIME[cls];
    const floor = p.exp_floor || 0, next = p.exp_to_level || 0;
    const res = p.resource && p.resource.max ? [p.resource.value, p.resource.max, p.resource.name] : [p.mana, p.max_mana, 'Mana'];
    const aff = Array.isArray(p.affects) ? p.affects : [];
    return `<div class="ch-top">
      <div class="ch-id">
        <div class="ch-name">${esc(p.name)}</div>
        <div class="ch-title">${esc(p.title || '')}</div>
        <div class="ch-line">Level ${p.level || 1} ${esc(title(p.race))} ${esc(title(p.char_class))}</div>
        <div class="ch-lab">Health</div>${bar(p.hp, p.max_hp, 'hp')}
        <div class="ch-lab">${esc(res[2])}</div>${bar(res[0], res[1], 'mp')}
        <div class="ch-lab">Movement</div>${bar(p.move, p.max_move, 'mv')}
        <div class="ch-lab">Experience</div>${next - floor > 1e9 || !next
          ? `<div class="ch-bar xp"><b style="width:100%"></b><span>Max level · ${(p.exp || 0).toLocaleString()} xp</span></div>`
          : bar(Math.max(0, (p.exp || 0) - floor), Math.max(1, next - floor), 'xp')}
        <div class="ch-gold">${(p.gold || 0).toLocaleString()} gold</div>
      </div>
    </div>
    <div class="ch-attrs">${ATTRS.map(([k, n]) => `<div class="${k === prime ? 'prime' : ''}" title="${n}${k === prime ? ' — your prime stat' : ''}"><div class="v">${p[k] ?? '–'}</div><div class="k">${k.toUpperCase()}</div></div>`).join('')}</div>
    <div class="ch-combat">
      <div><span>Hit</span><b>${p.hitroll >= 0 ? '+' : ''}${p.hitroll ?? 0}</b></div>
      <div><span>Damage</span><b>${p.damroll >= 0 ? '+' : ''}${p.damroll ?? 0}</b></div>
      <div><span>Armour</span><b>${p.armor_class ?? p.armor ?? '–'}</b></div>
      <div><span>Stance</span><b>${esc(title(p.position || 'standing'))}</b></div>
    </div>
    <div class="ch-lab">Active effects</div>
    <div class="ch-affects">${aff.length ? aff.map(a => {
      const n = title(a.name || a.type || a.spell || 'effect');
      const left = a.duration != null ? ` <small>${a.duration}${typeof a.duration === 'number' ? 't' : ''}</small>` : '';
      return `<i>${esc(n)}${left}</i>`;
    }).join('') : '<span class="ch-none">None</span>'}</div>`;
  }

  function abilities(p) {
    const learnedSk = p.skills || {}, learnedSp = p.spells || {};
    const roster = (list, learned) => {
      const names = new Set([...(list || []).map(x => typeof x === 'string' ? x : x && x.name).filter(Boolean), ...Object.keys(learned)]);
      return [...names].sort((a, b) => (learned[b] || 0) - (learned[a] || 0) || a.localeCompare(b)).map(n => {
        const v = learned[n];
        return `<div class="ab-row ${v ? '' : 'dim'}"><span>${esc(title(n))}</span>${v ? `<div class="ab-bar"><b style="width:${Math.min(100, v)}%"></b></div><em>${v}%</em>` : '<em>not learned</em>'}</div>`;
      }).join('') || '<span class="ch-none">None</span>';
    };
    const talents = Object.entries(p.talents || {});
    return `<div class="ab-cols">
      <div><div class="ch-lab">Skills</div>${roster(p.class_skills, learnedSk)}</div>
      <div><div class="ch-lab">Spells</div>${roster(p.class_spells, learnedSp)}</div>
    </div>
    ${talents.length ? `<div class="ch-lab">Talents</div><div class="ch-affects">${talents.map(([k, v]) => `<i>${esc(title(k))}${typeof v === 'number' ? ` <small>${v}</small>` : ''}</i>`).join('')}</div>` : ''}`;
  }

  function render() {
    if (!player || !open) return;
    const nsig = JSON.stringify([tab, player.level, player.hp, player.mana, player.move, player.exp, player.gold,
      player.affects, player.skills, player.spells, player.hitroll, player.damroll, player.armor_class, player.position]);
    if (nsig === sig) return;
    sig = nsig;
    body.innerHTML = tab === 'overview' ? overview(player) : abilities(player);
    // the portrait canvas lives outside the re-rendered text (one WebGL context, kept)
    const portrait = root.querySelector('.ch-portrait');
    portrait.classList.toggle('hidden', tab !== 'overview');
    if (tab === 'overview') {
      stage = stage || makeStage();
      stage.attach(portrait.querySelector('canvas'));
      if (shownClass !== player.char_class || !stage._shown) { shownClass = player.char_class; stage._shown = true; stage.show(player.char_class, { flourish: false }); }
    } else if (stage) { stage.stop(); stage._shown = false; }
  }
  function toggle(on = !open) {
    open = on;
    root.classList.toggle('hidden', !open);
    if (open) { sig = ''; if (stage) stage._shown = false; if (MH.refreshState) MH.refreshState(); render(); }
    else if (stage) { stage.stop(); stage._shown = false; }
  }
  return { toggle, get open() { return open; }, update(p) { player = p; render(); } };
}
