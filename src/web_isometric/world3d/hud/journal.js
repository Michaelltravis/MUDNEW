// The quest journal (L): a two-page book. On the left your quests (the marquee quest first,
// with a star); on the right the one you chose — its story, each objective with its progress,
// what it pays — and Complete / Abandon. Under the list, the quests offered by whoever stands
// beside you, each with Accept. Data: /quests (web_map.py), asked again whenever it opens and
// after anything you do in it.
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createJournal(root, { toast }) {
  const list = root.querySelector('.jr-list'), page = root.querySelector('.jr-page');
  let data = null, chosen = null, open = false;

  async function load() {
    const name = MH.state.playerName;
    if (!name) return;
    try {
      const r = await fetch(`/quests?player=${encodeURIComponent(name)}`);
      data = r.ok ? await r.json() : null;
    } catch (_) { data = null; }
    render();
  }
  const rewards = rw => {
    if (!rw) return '';
    const parts = [];
    if (rw.exp) parts.push(`<span class="jr-xp">${Number(rw.exp).toLocaleString()} xp</span>`);
    if (rw.gold) parts.push(`<span class="jr-gold">${Number(rw.gold).toLocaleString()} gold</span>`);
    if (rw.items && rw.items.length) parts.push(`<span class="jr-item">${rw.items.length} item${rw.items.length > 1 ? 's' : ''}</span>`);
    return parts.join('');
  };
  function render() {
    if (!open) return;
    const active = (data && data.active) || [];
    const offers = ((data && data.givers) || []).flatMap(g => (g.offers || []).map(o => ({ ...o, giver: g.name })));
    if (!chosen || !active.find(q => q.id === chosen)) chosen = active.length ? active[0].id : null;
    list.innerHTML = `<div class="jr-sec">Your quests <span>${active.length}</span></div>
      ${active.length ? active.map(q => {
        const done = (q.objectives || []).filter(o => o.completed).length, of = (q.objectives || []).length;
        return `<button class="jr-q${q.id === chosen ? ' on' : ''}${q.complete ? ' ready' : ''}" data-id="${esc(q.id)}">
          <span class="jr-qn">${q.marquee ? '★ ' : ''}${esc(q.name)}</span><span class="jr-qp">${q.complete ? 'Ready' : `${done}/${of}`}</span></button>`;
      }).join('') : '<div class="jr-none">No quest yet. Speak with the people of the hollow — some will have work for you.</div>'}
      ${offers.length ? `<div class="jr-sec">Offered here <span>${offers.length}</span></div>${offers.map(o => `<div class="jr-offer">
        <div class="jr-on">${esc(o.name)}</div><div class="jr-og">${esc(o.giver)} · level ${o.level_min || 1}${o.level_max ? `–${o.level_max}` : '+'}</div>
        <div class="jr-od">${esc(o.description || '')}</div><div class="jr-ofoot">${rewards(o.rewards)}<button class="btn jr-accept" data-id="${esc(o.id)}">Accept</button></div></div>`).join('')}` : ''}
      <div class="jr-count">${data && data.completed ? `${data.completed} quest${data.completed > 1 ? 's' : ''} completed` : ''}</div>`;
    list.querySelectorAll('.jr-q').forEach(b => b.addEventListener('click', () => { chosen = b.dataset.id; render(); }));
    list.querySelectorAll('.jr-accept').forEach(b => b.addEventListener('click', () => { MH.sendCommand(`quest accept ${b.dataset.id}`); setTimeout(load, 700); }));
    const q = active.find(x => x.id === chosen);
    page.innerHTML = q ? `<div class="jr-title">${esc(q.name)}</div>
      <div class="jr-desc">${esc(q.description || '')}</div>
      <div class="rule"></div>
      <div class="jr-lab">objectives</div>
      <ul class="jr-objs">${(q.objectives || []).map(o => `<li class="${o.completed ? 'done' : ''}"><i></i><span>${esc(o.description)}</span>${o.required > 1 ? `<b>${o.current || 0}/${o.required}</b>` : ''}</li>`).join('')}</ul>
      ${q.remaining_min != null ? `<div class="jr-time">${q.remaining_min} min left</div>` : ''}
      ${q.marquee ? `<div class="jr-lab">${q.role === 'helper' ? `you help ${esc(q.owner)}` : 'it teaches'}</div>
        <div class="jr-rew">${q.teaches ? `<span class="jr-teach">★ ${esc(q.teaches)}</span>` : '<span class="jr-none">Experience and gold when the trial falls</span>'}</div>
        <div class="jr-time">Stage ${q.stage} of ${q.of}</div>`
      : `<div class="jr-lab">reward</div><div class="jr-rew">${rewards(q.rewards) || '<span class="jr-none">The thanks of the hollow</span>'}</div>`}
      <div class="jr-acts">${q.complete ? `<button class="btn jr-done" data-id="${esc(q.id)}">Complete the quest</button>` : ''}
        <button class="btn alt jr-drop" data-id="${esc(q.id)}" data-marquee="${q.marquee ? q.role : ''}">${q.marquee && q.role === 'helper' ? 'Stop helping' : 'Abandon'}</button></div>`
      : `<div class="jr-empty"><div class="jr-title">The journal is open</div><div class="jr-desc">Its pages wait for your story. Talk to those marked with a <b>!</b> above their heads — and keep your lantern lit.</div></div>`;
    const done = page.querySelector('.jr-done');
    if (done) done.addEventListener('click', () => { MH.sendCommand(`quest complete ${done.dataset.id}`); setTimeout(load, 700); });
    const drop = page.querySelector('.jr-drop');
    if (drop) drop.addEventListener('click', () => {
      if (drop.dataset.armed) {
        const mq = drop.dataset.marquee;
        MH.sendCommand(mq === 'helper' ? 'marquee leave' : mq ? 'marquee abandon confirm' : `quest abandon ${drop.dataset.id}`);
        toast(mq === 'helper' ? 'You stop helping' : 'Quest abandoned'); setTimeout(load, 700);
      }
      else { drop.dataset.armed = '1'; drop.textContent = 'Click again to abandon'; }
    });
  }
  function toggle(on = !open) {
    open = on;
    root.classList.toggle('hidden', !open);
    if (open) { render(); load(); }
  }
  root.querySelector('.jr-close').addEventListener('click', () => toggle(false));
  return { toggle, get open() { return open; }, refresh: load };
}
