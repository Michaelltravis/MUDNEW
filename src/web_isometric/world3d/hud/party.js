// Your group on screen: the invite popup (Join / Decline), party frames under your own frame
// (health, mana, the leader's crown, where an absent member is; click one to target them —
// heals and blessings go to your target — right-click for Whisper, Follow, Make leader,
// Remove), and need / greed / pass loot rolls. Data: the payloads' `group` block
// (map_system.build_group_block) and the server's group / group_invite / loot_roll events.
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ARROW = { north: '↑', south: '↓', east: '→', west: '←', up: '⤒', down: '⤓', northeast: '↗', northwest: '↖', southeast: '↘', southwest: '↙' };
const CLASS_ICON = { warrior: '⚔', paladin: '✚', cleric: '✚', mage: '✦', necromancer: '☠', thief: '🗡', assassin: '🗡', ranger: '➶', bard: '♪' };
const pct = (a, b) => `${Math.max(0, Math.min(100, (b ? a / b : 0) * 100))}%`;

export function createParty({ frames, invite, loot, onTarget, onMenu, toast }) {
  let block = null, sig = '';

  // ---- party frames ----
  function members() {
    return block && Array.isArray(block.members) ? block.members.filter(m => !m.is_self && !m.is_minion) : [];
  }
  function render() {
    const list = members();
    const nsig = JSON.stringify(list.map(m => [m.name, m.is_leader, m.sameRoom, m.dead, m.online, m.roomName, m.dir]));
    frames.classList.toggle('hidden', !list.length);
    if (nsig !== sig) {
      sig = nsig;
      frames.innerHTML = list.map(m => `<div class="pt${m.dead ? ' dead' : ''}${m.sameRoom ? '' : ' away'}${m.online === false ? ' off' : ''}" data-name="${esc(m.name)}" title="Click to target · right-click for more">
        <div class="pt-top"><span class="pt-ic">${CLASS_ICON[String(m.char_class || '').toLowerCase()] || '⚔'}</span>
          <span class="pt-nm">${m.is_leader ? '<i class="crown" title="Leader">♚</i>' : ''}${esc(m.name)}</span><span class="pt-lv">${m.level || ''}</span></div>
        <div class="pt-bar hp"><b></b></div><div class="pt-bar mp"><b></b></div>
        <div class="pt-away"></div></div>`).join('');
      frames.querySelectorAll('.pt').forEach(el => {
        el.addEventListener('click', () => onTarget(el.dataset.name));
        el.addEventListener('contextmenu', e => { e.preventDefault(); onMenu(el.dataset.name, e.clientX, e.clientY, amLeader()); });
      });
    }
    // bars and whereabouts change every round: update in place
    for (const m of list) {
      const el = frames.querySelector(`.pt[data-name="${CSS.escape(m.name)}"]`);
      if (!el) continue;
      el.querySelector('.hp b').style.width = pct(m.hp, m.maxHp);
      el.querySelector('.mp b').style.width = pct(m.mana, m.maxMana);
      el.classList.toggle('low', !m.dead && m.sameRoom && m.maxHp && m.hp / m.maxHp <= 0.3);
      el.querySelector('.pt-away').textContent = m.online === false ? 'gone' : m.dead ? 'fallen' : m.sameRoom ? '' : `${ARROW[m.dir] || '·'} ${m.roomName || 'elsewhere'}`;
    }
  }
  function amLeader() {
    const me = block && (block.members || []).find(m => m.is_self);
    return !!(me && me.is_leader);
  }

  // ---- the invite ----
  let inviteTimer = 0;
  function showInvite({ from, level, char_class, expires }) {
    invite.innerHTML = `<div class="iv-t">Group invitation</div>
      <div class="iv-who"><b>${esc(from)}</b>${level ? ` · level ${level}` : ''}${char_class ? ` ${esc(char_class)}` : ''} invites you to join their group.</div>
      <div class="iv-b"><button class="join">Join</button><button class="decline">Decline</button></div>
      <div class="lr-bar" style="--lr-ms:${(expires || 60) * 1000}ms"></div>`;
    invite.classList.remove('hidden');
    const close = () => { invite.classList.add('hidden'); clearTimeout(inviteTimer); };
    invite.querySelector('.join').addEventListener('click', () => { MH.sendCommand('group accept'); close(); });
    invite.querySelector('.decline').addEventListener('click', () => { MH.sendCommand('group decline'); close(); });
    clearTimeout(inviteTimer);
    inviteTimer = setTimeout(close, (expires || 60) * 1000);
  }

  // ---- loot rolls: one at a time, the rest queued ----
  const queue = [];
  let lootTimer = 0;
  function showLoot() {
    const r = queue[0];
    if (!r) { loot.classList.add('hidden'); return; }
    loot.innerHTML = `<div class="iv-t">Loot roll${queue.length > 1 ? ` · ${queue.length} items` : ''}</div>
      <div class="lr-item ${esc(r.rarity || '')}">${esc(r.item)}</div>
      <div class="iv-b"><button data-v="need">Need</button><button data-v="greed">Greed</button><button data-v="pass">Pass</button></div>
      <div class="lr-bar" style="--lr-ms:${(r.timeout || 20) * 1000}ms"></div>`;
    loot.classList.remove('hidden');
    loot.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      MH.sendCommand(`roll ${b.dataset.v}`, false);
      queue.shift(); showLoot();
    }));
    clearTimeout(lootTimer);
    lootTimer = setTimeout(() => { queue.shift(); showLoot(); }, (r.timeout || 20) * 1000);
  }

  return {
    // the group block from a payload or a group event (null: no group)
    update(b) { block = b || null; render(); },
    showInvite,
    lootRoll(r) { queue.push(r); if (queue.length === 1) showLoot(); },
    lootResult(r) {
      const i = queue.findIndex(q => q.id === r.id);
      if (i >= 0) { queue.splice(i, 1); if (i === 0) showLoot(); }
      toast(r.winner ? `${r.winner} wins ${r.item}` : `Everyone passed on ${r.item}`);
    },
    get members() { return members(); },
    get leader() { return amLeader(); },
    get inGroup() { return !!(block && (block.members || []).length > 1); },
  };
}
