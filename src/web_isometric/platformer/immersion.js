// Misthollow: the immersion layer. MUDs lived on their details - prose,
// ambient whispers, things to look at, a world clock you could feel.
// This module surfaces all of it over the graphical client:
//   - ambient echoes float as whispers over the world (+ matching sound)
//   - zone title cards when crossing borders
//   - a sky chip: sun/moon position, weather, game date
//   - look-at-everything: clickable prose keywords, examine cards
//   - NPC street chatter lines + prop flavor text tables
//   - procedural ambient soundscapes per zone theme
(() => {
  const MH = window.MH = window.MH || {};
  const $ = id => document.getElementById(id);

  // ---------------- whispers ----------------
  const whisperQueue = [];
  let whispersShowing = 0;
  function showWhisper(text) {
    const host = $('whisper-host');
    if (!host) return;
    if (whispersShowing >= 2) { if (whisperQueue.length < 4) whisperQueue.push(text); return; }
    whispersShowing++;
    const div = document.createElement('div');
    div.className = 'whisper';
    div.textContent = text;
    host.appendChild(div);
    requestAnimationFrame(() => div.classList.add('show'));
    setTimeout(() => div.classList.remove('show'), 5200);
    setTimeout(() => {
      div.remove();
      whispersShowing--;
      if (whisperQueue.length) showWhisper(whisperQueue.shift());
    }, 6200);
    whisperSound(text);
  }
  MH.bus.on('ambient.echo', showWhisper);

  // ---------------- zone title cards ----------------
  let lastZoneName = null;
  MH.bus.on('room.entered', ({ zoneName }) => {
    if (!zoneName || zoneName === lastZoneName) { lastZoneName = zoneName || lastZoneName; return; }
    const first = lastZoneName === null;
    lastZoneName = zoneName;
    if (first) return;           // no card for the login room
    const card = $('zone-card');
    if (!card) return;
    card.textContent = zoneName;
    card.classList.remove('show');
    void card.offsetWidth;       // restart the animation
    card.classList.add('show');
  });

  // ---------------- sky chip: sun/moon arc + weather + date ----------------
  const MONTHS = ['Deepwinter', 'Thaw', 'Seedfall', 'Rainmoon', 'Blossom', 'Highsun',
    'Goldfield', 'Harvest', 'Emberfall', 'Mistmoon', 'Frostveil', 'Longnight'];
  function updateSky(payload) {
    const c = $('sky-canvas'), label = $('sky-label');
    if (!c || !payload.time) return;
    const { hour = 12, day = 1, month = 6 } = payload.time;
    const w = payload.weather || {};
    const x = c.getContext('2d');
    const W = c.width, H = c.height;
    x.clearRect(0, 0, W, H);
    // arc path: dawn at left horizon, noon top, dusk right
    const sunT = (hour - 6) / 12;          // 0..1 across the day sky
    const moonT = ((hour + 18) % 24) / 12; // night arc
    const arc = t => ({ X: 6 + t * (W - 12), Y: H - 4 - Math.sin(Math.max(0, Math.min(1, t)) * Math.PI) * (H - 9) });
    x.strokeStyle = 'rgba(200,205,220,0.25)';
    x.beginPath();
    for (let t = 0; t <= 1.001; t += 0.1) { const p = arc(t); t === 0 ? x.moveTo(p.X, p.Y) : x.lineTo(p.X, p.Y); }
    x.stroke();
    const day_ = sunT >= 0 && sunT <= 1;
    if (day_) {
      const p = arc(sunT);
      const g = x.createRadialGradient(p.X, p.Y, 0.5, p.X, p.Y, 5);
      g.addColorStop(0, '#fff2c0'); g.addColorStop(1, 'rgba(255,200,80,0)');
      x.fillStyle = g; x.beginPath(); x.arc(p.X, p.Y, 5, 0, 7); x.fill();
      x.fillStyle = '#ffd860'; x.beginPath(); x.arc(p.X, p.Y, 2.4, 0, 7); x.fill();
    } else {
      const p = arc(moonT <= 1 ? moonT : 0.5);
      x.fillStyle = '#d8e2f4'; x.beginPath(); x.arc(p.X, p.Y, 2.6, 0, 7); x.fill();
      x.fillStyle = '#10131e'; x.beginPath(); x.arc(p.X + 1.2, p.Y - 0.8, 2.1, 0, 7); x.fill();
    }
    const sky = (w.sky || 'clear').toLowerCase();
    const icon = /storm|lightning/.test(sky) ? '⛈' : /rain/.test(sky) ? '🌧' : /cloud/.test(sky) ? '☁' : day_ ? '☀' : '🌙';
    const hh = String(hour).padStart(2, '0');
    if (label) label.textContent = `${icon} ${hh}:00 · ${day} ${MONTHS[(month - 1 + 12) % 12]}`;
    if (label) label.title = `Sky: ${w.sky || 'clear'} · ${w.temperature != null ? w.temperature + '°' : ''} ${w.wind ? '· wind ' + w.wind : ''}`;
  }
  MH.bus.on('map', updateSky);

  // ---------------- look-at-everything ----------------
  let cardTimer = null;
  // remember where the player last clicked so examine/look bubbles can pop up
  // right at the object instead of in a far corner
  let _lastPointer = null;
  document.addEventListener('pointerdown', e => { _lastPointer = { x: e.clientX, y: e.clientY }; }, true);

  function showDetailCard(title, text, kind, x, y) {
    const card = $('detail-card');
    if (!card) return;
    if (x == null && _lastPointer) { x = _lastPointer.x; y = _lastPointer.y; }
    const ICONS = { detail: '✦', being: '☻', item: '❖', prop: '✧' };
    card.innerHTML = `<div class="dc-title"><span class="dc-icon">${ICONS[kind] || '✦'}</span>${title}</div><div class="dc-text"></div>`;
    card.querySelector('.dc-text').textContent = text;
    card.classList.add('show');
    // anchor the bubble at the object/pointer when coordinates are given,
    // otherwise fall back to the fixed top-right card
    if (x != null && y != null) {
      card.classList.add('at');
      card.style.right = 'auto';
      // measure then place above the point, flipping below if it would clip
      card.style.left = '0px'; card.style.top = '0px';
      const r = card.getBoundingClientRect();
      const w = r.width || 260, h = r.height || 120;
      let lx = Math.max(8, Math.min(x - w / 2, window.innerWidth - w - 8));
      let ty = y - h - 16;
      if (ty < 8) ty = Math.min(y + 22, window.innerHeight - h - 8);
      card.style.left = lx + 'px'; card.style.top = ty + 'px';
    } else {
      card.classList.remove('at');
      card.style.left = ''; card.style.top = ''; card.style.right = '';
    }
    clearTimeout(cardTimer);
    cardTimer = setTimeout(() => card.classList.remove('show'), Math.min(14000, 4500 + text.length * 28));
    card.onclick = () => { card.classList.remove('show'); clearTimeout(cardTimer); };
  }
  MH.immersion = {
    async lookAt(target) {
      if (!target) return;
      try {
        const r = await fetch(`/lookat?player=${encodeURIComponent(MH.state.playerName)}&target=${encodeURIComponent(target)}`);
        const j = await r.json();
        if (j.found) showDetailCard(j.title || target, j.text || '', j.kind);
        else showDetailCard(target, 'You see nothing special about it.', 'detail');
      } catch (_) { /* server older than the client - fall back silently */ }
    },
    propFlavor(name) {
      const f = PROP_FLAVOR[name];
      if (f) showDetailCard(f[0], f[1], 'prop');
    },
    // run a text command and surface its reply in the detail card, so
    // right-click verbs like Consider / Where / Score visibly "do something"
    // instead of quietly dumping into the (usually closed) terminal drawer.
    runInfo(cmd, title) {
      let done = false;
      const handler = ({ text }) => {
        if (done) return;
        done = true;
        MH.bus.off('terminal.output', handler);
        clearTimeout(t);
        const clean = (text || '').replace(/\n{3,}/g, '\n\n').trim();
        showDetailCard(title || cmd, clean || 'Nothing happens.', 'detail');
      };
      MH.bus.on('terminal.output', handler);
      const t = setTimeout(() => { MH.bus.off('terminal.output', handler); }, 1600);
      MH.sendCommand(cmd);
    },
    showDetailCard,
    // wrap look-at keywords in the room prose with clickable spans
    decorateProse(el, desc, room) {
      const kws = new Set((room && room.details) || []);
      // mobs and items present in the room are also lookable
      const entry = (MH.state.lastPayload && (MH.state.lastPayload.rooms || []).find(r => r.vnum === room.vnum)) || {};
      for (const m of entry.mobs || []) { const k = MH.mobKeyword(m.name); if (k) kws.add(k.toLowerCase()); }
      for (const it of entry.items || []) { const k = MH.mobKeyword(it.name); if (k) kws.add(k.toLowerCase()); }
      if (!kws.size) { el.textContent = desc; return; }
      const pat = new RegExp(`\\b(${[...kws].map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '')).filter(Boolean).join('|')})\\b`, 'gi');
      el.textContent = '';
      let last = 0;
      desc.replace(pat, (match, _g, idx) => {
        el.appendChild(document.createTextNode(desc.slice(last, idx)));
        const span = document.createElement('span');
        span.className = 'prose-kw';
        span.textContent = match;
        span.title = `look at ${match.toLowerCase()}`;
        span.onclick = e => { e.stopPropagation(); MH.immersion.lookAt(match.toLowerCase()); };
        el.appendChild(span);
        last = idx + match.length;
        return match;
      });
      el.appendChild(document.createTextNode(desc.slice(last)));
    },
  };

  // ---------------- object action popover ----------------
  let popTimer = null;
  MH.popover = {
    show(x, y, title, actions) {
      const pop = $('obj-popover');
      if (!pop) return;
      pop.innerHTML = `<div class="op-title">${title}</div>`;
      for (const a of actions) {
        const b = document.createElement('button');
        b.textContent = a.label;
        b.onclick = () => { MH.popover.hide(); a.fn(); };
        pop.appendChild(b);
      }
      // anchor the bubble centred on the object, floating just above it —
      // or just below if there isn't room above
      pop.classList.add('show');
      const r = pop.getBoundingClientRect();
      const w = r.width || 150, h = r.height || (40 + actions.length * 30);
      let left = x - w / 2;
      left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
      let top = y - h - 14;                       // prefer above the object
      if (top < 8) top = Math.min(y + 18, window.innerHeight - h - 8);   // flip below
      pop.style.left = left + 'px';
      pop.style.top = top + 'px';
      clearTimeout(popTimer);
      popTimer = setTimeout(() => MH.popover.hide(), 8000);
      setTimeout(() => document.addEventListener('pointerdown', onAway, { once: true }), 0);
    },
    hide() {
      const pop = $('obj-popover');
      if (pop) pop.classList.remove('show');
    },
  };
  function onAway(e) {
    const pop = $('obj-popover');
    if (pop && !pop.contains(e.target)) MH.popover.hide();
  }

  // ============ universal right-click context menus ============
  // every sensible verb for the target, the long tail behind More…
  function kw(name) { return MH.mobKeyword(name || ''); }
  function send(c) { MH.sendCommand(c); }
  function mySkills() { return (MH.state.player && MH.state.player.skills) || {}; }

  function mobVerbs(d) {
    const k = kw(d.name);
    const sk = mySkills();
    const top = [];
    if (d.hostile || d.fighting) top.push({ label: '⚔ Attack', fn: () => send(`kill ${k}`) });
    top.push({ label: '💬 Talk', fn: () => MH.bus.emit('npc.talk', { name: d.name, quest: d.quest || '' }) });
    top.push({ label: '👁 Look', fn: () => MH.immersion.lookAt(k) });
    top.push({ label: '🧠 Consider', fn: () => MH.immersion.runInfo(`consider ${k}`, `Consider ${d.name}`) });
    if (d.shopkeeper) top.push({ label: '🪙 Shop', fn: () => MH.bus.emit('shop.open', d) });
    if (d.trainer) top.push({ label: '📖 Train', fn: () => MH.bus.emit('training.open', d) });
    if (!d.hostile) top.push({ label: '⚔ Attack', fn: () => send(`kill ${k}`) });
    const more = [
      { label: 'Follow', fn: () => send(`follow ${k}`) },
      { label: 'Give item…', fn: () => promptCmd(`give <item> ${k}`, `give `, ` ${k}`) },
    ];
    if ('steal' in sk) more.push({ label: 'Steal gold', fn: () => send(`steal gold ${k}`) });
    if ('backstab' in sk) more.push({ label: 'Backstab', fn: () => send(`backstab ${k}`) });
    if ('mark' in sk) more.push({ label: 'Mark', fn: () => send(`mark ${k}`) });
    if ('track' in sk) more.push({ label: 'Track', fn: () => send(`track ${k}`) });
    more.push({ label: 'Group with', fn: () => send(`group ${k}`) });
    return { top, more };
  }
  function playerVerbs(d) {
    const k = kw(d.name);
    return {
      top: [
        { label: '💬 Tell…', fn: () => promptCmd(`tell ${k} <message>`, `tell ${k} `, '') },
        { label: '👁 Look', fn: () => MH.immersion.lookAt(k) },
        { label: '🤝 Group invite', fn: () => send(`group ${k}`) },
        { label: '🚶 Follow', fn: () => send(`follow ${k}`) },
      ],
      more: [
        { label: 'Give item…', fn: () => promptCmd(`give <item> ${k}`, `give `, ` ${k}`) },
        { label: 'Where', fn: () => MH.immersion.runInfo('where', 'Who is where') },
      ],
    };
  }
  function selfVerbs() {
    const sk = mySkills();
    const top = [
      { label: '👁 Look around', fn: () => MH.immersion.runInfo('look', 'You look around') },
      { label: '🔍 Search for secrets', fn: () => MH.immersion.runInfo('search', 'You search') },
      { label: '😴 Rest', fn: () => send('rest') },
      { label: '🧍 Stand', fn: () => send('stand') },
      { label: '🌀 Recall', fn: () => send('recall') },
    ];
    const more = [
      { label: 'Where am I', fn: () => MH.immersion.runInfo('where', 'Who is where') },
      { label: 'Who is online', fn: () => MH.immersion.runInfo('who', 'Who is online') },
      { label: 'Sleep', fn: () => send('sleep') },
      { label: 'Time & weather', fn: () => MH.immersion.runInfo('time', 'Time & weather') },
      { label: 'Save', fn: () => send('save') },
      { label: 'Score sheet', fn: () => MH.immersion.runInfo('score', 'Your score') },
    ];
    if ('hide' in sk) more.unshift({ label: 'Hide', fn: () => send('hide') });
    if ('sneak' in sk) more.unshift({ label: 'Sneak', fn: () => send('sneak') });
    if ('camp' in sk) more.unshift({ label: 'Camp', fn: () => send('camp') });
    return { top, more };
  }
  // typed-argument verbs prefill the command input instead of guessing
  function promptCmd(hint, prefix, suffix) {
    const input = document.getElementById('command-input');
    if (!input) return;
    input.value = prefix + suffix;
    input.focus();
    const pos = prefix.length;
    input.setSelectionRange(pos, pos);
    MH.bus.emit('flash', hint);
  }

  MH.contextMenu = function (kind, data, x, y) {
    let v;
    if (kind === 'mob') v = mobVerbs(data || {});
    else if (kind === 'player') v = playerVerbs(data || {});
    else if (kind === 'self') v = selfVerbs();
    else if (kind === 'item') { MH.objectActions(data, x, y); return; }
    else return;
    const title = kind === 'self' ? (MH.state.player ? MH.state.player.name : 'You') : ((data && (data.short || data.name)) || kind);
    const open = items => MH.popover.show(x, y, String(title).slice(0, 30), items);
    const entries = v.top.slice(0, 6);
    if (v.more && v.more.length) entries.push({ label: 'More…', fn: () => setTimeout(() => open(v.more), 0) });
    open(entries);
  };

  // context actions for a world object (server item on the ground)
  MH.objectActions = function (data, x, y) {
    const name = data.name || 'object';
    const kw = MH.mobKeyword(name);
    const type = data.type || data.item_type || 'other';
    const acts = [];
    if (type === 'fountain') {
      acts.push({ label: '🜄 Drink', fn: () => MH.sendCommand('drink') });
      const p = MH.state.player || {};
      for (const it of (p.inventory || []).filter(i => (i.item_type || i.type) === 'drink').slice(0, 4)) {
        acts.push({ label: `⚱ Fill ${ (it.short || it.name).slice(0, 18) }`, fn: () => MH.sendCommand(`fill ${MH.mobKeyword(it.name)}`) });
      }
      acts.push({ label: '👁 Look', fn: () => MH.immersion.lookAt(kw) });
    } else if (type === 'container') {
      acts.push({ label: '📦 Open', fn: () => MH.openContainer(kw, name) });
      acts.push({ label: '✋ Take', fn: () => MH.sendCommand(`get ${kw}`) });
      acts.push({ label: '👁 Look', fn: () => MH.immersion.lookAt(kw) });
    } else if (type === 'note' || type === 'scroll') {
      acts.push({ label: '📜 Read', fn: () => MH.immersion.lookAt(kw) });
      acts.push({ label: '✋ Take', fn: () => MH.sendCommand(`get ${kw}`) });
    } else if (type === 'drink') {
      acts.push({ label: '🜄 Drink from it', fn: () => MH.sendCommand(`drink ${kw}`) });
      acts.push({ label: '✋ Take', fn: () => MH.sendCommand(`get ${kw}`) });
    } else {
      acts.push({ label: '✋ Take', fn: () => MH.sendCommand(`get ${kw}`) });
      acts.push({ label: '👁 Look', fn: () => MH.immersion.lookAt(kw) });
    }
    MH.popover.show(x, y, (data.short || name).slice(0, 30), acts);
  };

  // peek inside a ground/carried container, with per-item Take buttons
  MH.openContainer = async function (kw, displayName) {
    try {
      const r = await fetch(`/container?player=${encodeURIComponent(MH.state.playerName)}&target=${encodeURIComponent(kw)}`);
      const j = await r.json();
      if (!j.found) { MH.immersion.showDetailCard(displayName, 'You find no way in.', 'item'); return; }
      if (j.closed) { MH.sendCommand(`open ${kw}`); setTimeout(() => MH.openContainer(kw, displayName), 700); return; }
      const lines = (j.items && j.items.length)
        ? j.items.map(it => `• ${it.short || it.name}`).join('\n')
        : 'It is empty.';
      MH.immersion.showDetailCard(j.title || displayName, lines + (j.items && j.items.length ? '\n\n(taking everything…)' : ''), 'item');
      if (j.items && j.items.length) MH.sendCommand(`get all ${kw}`);
    } catch (_) { MH.sendCommand(`look in ${kw}`); }
  };

  // ---------------- prop flavor (client-side lore for scenery) ----------------
  const PROP_FLAVOR = {
    lamppost: ['A Street Lamp', 'Oil-fed and iron-wrought, its flame gutters with every gust. Moths spiral in its halo.'],
    lantern: ['A Hanging Lantern', 'Pale elven glass. The light inside does not flicker like fire - it breathes.'],
    brazier: ['A Brazier', 'Coals shift and settle in the iron basket, breathing out waves of dry heat.'],
    fountain: ['A Fountain', 'Water sings over worn stone. Generations of coins glint up from the bottom, each one a wish.'],
    statue: ['A Weathered Statue', 'Rain and years have softened the face to anonymity, yet the stance is still proud.'],
    gravestone: ['A Gravestone', 'Lichen fills the carved letters. Whoever rests here has long been only a name.'],
    banner: ['A Banner', 'The cloth is sun-faded but the sigil remains defiant, snapping in the wind.'],
    stall: ['A Market Stall', "A striped awning over crates of goods. The vendor's patter never quite stops."],
    crate: ['A Crate', 'Stenciled lettering, half worn away. It smells faintly of straw and far-off ports.'],
    barrel: ['A Barrel', 'The staves creak when you lean on it. Something inside sloshes, thick and slow.'],
    anvil: ['An Anvil', 'Its face is polished mirror-bright by ten thousand hammer blows.'],
    gear: ['A Great Gear', 'Teeth taller than your hand. It turns once a minute with a sound like a drawn breath.'],
    pipe: ['A Steam Pipe', 'Rivets weep rust. The pipe shudders, then settles, as pressure passes through.'],
    runestone: ['A Runestone', 'The carved sigil glows faintly warmer when you stand near. It is watching, politely.'],
    crystal: ['A Crystal Growth', 'Violet light pulses deep in the facets, slow as a sleeping heartbeat.'],
    icecrystal: ['An Ice Formation', 'Blue-white and flawless. Deep inside, something glimmers - frozen mid-fall.'],
    mushrooms: ['Wild Mushrooms', 'Red-capped and freckled. Probably poisonous. Definitely beautiful.'],
    flowers: ['Wildflowers', 'They turn with the light through the day. Bees argue quietly over the best ones.'],
    tree: ['An Old Tree', 'Initials are carved in the bark, grown tall and stretched with the years.'],
    pine: ['A Pine', 'Snow slides from the boughs in soft thumps. The scent of resin cuts the cold.'],
    deadtree: ['A Dead Tree', 'Bone-grey branches claw at the sky. A crow considers you from the highest one.'],
    bush: ['A Bush', 'Something small rustles deeper into it as you approach.'],
    stump: ['A Stump', 'The rings count more years than the town has names for.'],
    rock: ['A Boulder', 'Moss on the north face, warmth on the south. The oldest citizen of this place.'],
    bones: ['Scattered Bones', 'Picked clean and sun-bleached. You choose not to count whether anything is missing.'],
    web: ['A Spiderweb', 'Dew hangs on every strand. Its architect is nowhere to be seen - which is worse.'],
    reeds: ['Reeds', 'They whisper against each other even when the wind has stopped.'],
    lilypad: ['Lily Pads', 'A frog regards you with ancient, untroubled patience.'],
    coral: ['Coral', 'A garden of stone flowers, swaying colors no painter has matched.'],
    shell: ['A Great Shell', 'Hold it to your ear and the drowned streets murmur back.'],
    cactus: ['A Cactus', 'It has outlasted everything else that tried to live here, and looks smug about it.'],
    snowdrift: ['A Snowdrift', 'Wind-sculpted into a frozen wave. Small tracks stitch across its crest.'],
    rubble: ['Rubble', 'Squared stones in the wreckage - this was built once, by careful hands.'],
    urn: ['A Clay Urn', 'Sealed with wax gone amber with age. It is heavier than it looks.'],
    bookpile: ['A Stack of Books', 'Marginalia crowd every page, three arguments deep, in three different hands.'],
    candles: ['Votive Candles', 'Each flame is a small promise someone left burning here.'],
    pillar: ['A Pillar', 'Fluted marble, cool to the touch in any weather.'],
    beam: ['A Support Beam', 'The timber is scarred with tally marks. Miners counting days, or luck.'],
    fence: ['A Fence', 'Leaning, patched, repainted in three different decades of color.'],
  };
  MH.PROP_FLAVOR = PROP_FLAVOR;

  // ---------------- NPC street chatter (by sprite archetype) ----------------
  MH.CHATTER = {
    citizen: ['Fine weather for it.', 'Mind the gutters after dark.', 'Fresh bread, gone by noon.',
      "Haven't seen rain like last week's in years.", 'The guard doubled patrols, you know.',
      'My grandmother swore the fountain grants wishes.', 'Watch your purse near the gates.'],
    guard: ['Move along.', 'Keep your blade peace-bound in the city.', 'All quiet. Too quiet, if you ask me.',
      'Report trouble to the watch.', 'The gates close at midnight. Officially.'],
    shopkeeper: ['Finest wares this side of the river!', 'Browse all you like.', 'Everything has a price.',
      'Back in stock, just for you.', 'No refunds. House rule.'],
    caster: ['The leylines are restless today.', 'Magic always collects its fee.', 'I felt a ripple in the weave...'],
    citizenF: ['Lovely morning, no?', 'The market is mad today.'],
  };

  // ---------------- whisper sounds + ambient soundscapes ----------------
  let actx = null, master = null, bedNodes = [], bedTimer = null, curBed = null;
  let muted = localStorage.getItem('misthollow_ambience') === 'off';
  function actxGet() {
    if (actx) { if (actx.state === 'suspended') actx.resume().catch(() => {}); return actx; }
    const Ref = window.AudioContext || window.webkitAudioContext;
    if (!Ref) return null;
    try { actx = new Ref(); } catch (_) { return null; }
    master = actx.createGain();
    master.gain.value = muted ? 0 : 1;
    master.connect(actx.destination);
    return actx;
  }
  function noiseBuf(ctx, secs = 2) {
    const buf = ctx.createBuffer(1, ctx.sampleRate * secs, ctx.sampleRate);
    const d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return buf;
  }
  function oneShot({ f = 600, f2 = null, type = 'sine', dur = 0.2, vol = 0.05, delay = 0, bp = null }) {
    const ctx = actxGet(); if (!ctx) return;
    const t = ctx.currentTime + delay;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + dur * 0.2);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    let src;
    if (bp) {
      src = ctx.createBufferSource(); src.buffer = noiseBuf(ctx, dur + 0.1);
      const filt = ctx.createBiquadFilter(); filt.type = 'bandpass'; filt.frequency.value = bp; filt.Q.value = 2.5;
      src.connect(filt); filt.connect(g);
    } else {
      src = ctx.createOscillator(); src.type = type;
      src.frequency.setValueAtTime(f, t);
      if (f2) src.frequency.exponentialRampToValueAtTime(f2, t + dur);
      src.connect(g);
    }
    g.connect(master);
    src.start(t); src.stop(t + dur + 0.05);
  }
  function whisperSound(text) {
    const s = text.toLowerCase();
    if (/wind|breeze|gust/.test(s)) oneShot({ bp: 400, dur: 1.6, vol: 0.05 });
    else if (/owl|bird|hawk|crow|caw/.test(s)) { oneShot({ f: 880, f2: 620, type: 'sine', dur: 0.18, vol: 0.04 }); oneShot({ f: 840, f2: 580, type: 'sine', dur: 0.22, vol: 0.035, delay: 0.3 }); }
    else if (/water|wave|stream|river|drip|splash/.test(s)) oneShot({ bp: 900, dur: 0.5, vol: 0.045 });
    else if (/thunder|storm/.test(s)) oneShot({ bp: 90, dur: 2.2, vol: 0.09 });
    else if (/bell|chime/.test(s)) oneShot({ f: 520, type: 'triangle', dur: 1.4, vol: 0.05 });
    else if (/wolf|howl/.test(s)) oneShot({ f: 420, f2: 300, type: 'sine', dur: 1.1, vol: 0.045 });
    else oneShot({ bp: 600, dur: 0.5, vol: 0.022 });
  }

  MH.bus.on('ambient.sound', k => {
    if (k === 'thunder') oneShot({ bp: 90, dur: 2.2, vol: 0.09 });
    else if (k === 'chime') { oneShot({ f: 880, type: 'triangle', dur: 0.5, vol: 0.05 }); oneShot({ f: 1320, type: 'triangle', dur: 0.7, vol: 0.04, delay: 0.12 }); }
  });

  // ambient beds: a filtered noise layer + periodic chirps per theme family
  const BEDS = {
    forest:   { wind: [320, 0.016], chirp: { f: [900, 1500], every: [2.5, 7], dur: 0.12, vol: 0.022 } },
    meadow:   { wind: [380, 0.014], chirp: { f: [900, 1600], every: [2, 6], dur: 0.1, vol: 0.02 } },
    autumn:   { wind: [300, 0.02], chirp: { f: [700, 1100], every: [5, 12], dur: 0.14, vol: 0.016 } },
    darkforest:{ wind: [220, 0.018], chirp: { f: [300, 500], every: [6, 14], dur: 0.4, vol: 0.018 } },
    elven:    { wind: [420, 0.012], chirp: { f: [1100, 1700], every: [3, 8], dur: 0.16, vol: 0.018 } },
    swamp:    { wind: [180, 0.016], chirp: { f: [220, 420], every: [3, 8], dur: 0.25, vol: 0.02 } },
    midgaard: { wind: [500, 0.010], chirp: { f: [400, 800], every: [4, 10], dur: 0.18, vol: 0.012 } },
    sandstone:{ wind: [450, 0.012], chirp: { f: [500, 900], every: [5, 12], dur: 0.15, vol: 0.012 } },
    rome:     { wind: [480, 0.010], chirp: { f: [500, 900], every: [5, 12], dur: 0.15, vol: 0.012 } },
    temple:   { wind: [240, 0.010], chirp: { f: [520, 660], every: [8, 18], dur: 1.0, vol: 0.012 } },
    sewer:    { wind: [140, 0.014], chirp: { f: [1300, 2100], every: [1.5, 5], dur: 0.05, vol: 0.025, drip: true } },
    mines:    { wind: [110, 0.016], chirp: { f: [1100, 1900], every: [3, 9], dur: 0.06, vol: 0.02, drip: true } },
    dwarvenhall:{ wind: [150, 0.014], chirp: { f: [200, 320], every: [4, 9], dur: 0.2, vol: 0.02 } },
    drow:     { wind: [120, 0.016], chirp: { f: [1500, 2400], every: [4, 11], dur: 0.05, vol: 0.018, drip: true } },
    desert:   { wind: [520, 0.02], chirp: null },
    frozen:   { wind: [600, 0.024], chirp: { f: [800, 1300], every: [8, 18], dur: 0.3, vol: 0.012 } },
    volcanic: { wind: [90, 0.02], chirp: { f: [140, 240], every: [3, 8], dur: 0.4, vol: 0.022 } },
    necropolis:{ wind: [160, 0.018], chirp: { f: [260, 380], every: [7, 16], dur: 0.8, vol: 0.014 } },
    sunken:   { wind: [200, 0.018], chirp: { f: [600, 1000], every: [2, 6], dur: 0.3, vol: 0.018 } },
    clockwork:{ wind: [260, 0.012], chirp: { f: [320, 540], every: [1.2, 3], dur: 0.08, vol: 0.018 } },
    voidstar: { wind: [80, 0.014], chirp: { f: [1800, 2600], every: [4, 10], dur: 0.5, vol: 0.012 } },
    arcane:   { wind: [100, 0.012], chirp: { f: [1600, 2400], every: [3, 8], dur: 0.4, vol: 0.014 } },
    castle:   { wind: [340, 0.012], chirp: null },
    darkcastle:{ wind: [200, 0.018], chirp: { f: [180, 300], every: [6, 15], dur: 0.6, vol: 0.014 } },
    chessboard:{ wind: [260, 0.008], chirp: null },
  };
  function stopBed() {
    bedNodes.forEach(n => { try { n.stop ? n.stop() : n.disconnect(); } catch (_) {} });
    bedNodes = [];
    if (bedTimer) { clearTimeout(bedTimer); bedTimer = null; }
    curBed = null;
  }
  function startBed(key) {
    if (curBed === key) return;
    stopBed();
    const spec = BEDS[key];
    if (!spec) return;
    const ctx = actxGet(); if (!ctx) return;
    curBed = key;
    // continuous wind/room-tone layer
    const src = ctx.createBufferSource();
    src.buffer = noiseBuf(ctx, 3); src.loop = true;
    const filt = ctx.createBiquadFilter();
    filt.type = 'bandpass'; filt.frequency.value = spec.wind[0]; filt.Q.value = 0.6;
    const g = ctx.createGain();
    g.gain.value = 0.0001;
    g.gain.exponentialRampToValueAtTime(spec.wind[1], ctx.currentTime + 2.5);
    // slow swell so it never reads as a flat hiss
    const lfo = ctx.createOscillator(); lfo.frequency.value = 0.07;
    const lfoG = ctx.createGain(); lfoG.gain.value = spec.wind[1] * 0.5;
    lfo.connect(lfoG); lfoG.connect(g.gain);
    src.connect(filt); filt.connect(g); g.connect(master);
    src.start(); lfo.start();
    bedNodes.push(src, lfo, g);
    // periodic chirps (birds, drips, clanks, hums)
    if (spec.chirp) {
      const loop = () => {
        if (curBed !== key) return;
        const ch = spec.chirp;
        const f = ch.f[0] + Math.random() * (ch.f[1] - ch.f[0]);
        if (ch.drip) oneShot({ f, f2: f * 0.6, type: 'sine', dur: ch.dur, vol: ch.vol });
        else oneShot({ f, f2: f * (0.8 + Math.random() * 0.4), type: 'sine', dur: ch.dur, vol: ch.vol });
        bedTimer = setTimeout(loop, (ch.every[0] + Math.random() * (ch.every[1] - ch.every[0])) * 1000);
      };
      bedTimer = setTimeout(loop, 1500);
    }
  }
  MH.bus.on('zone.theme', ({ zoneKey, theme }) => startBed(zoneKey || theme));
  MH.bus.on('login.success', () => { actxGet(); });

  // mute toggle on the sky chip
  document.addEventListener('DOMContentLoaded', () => {
    const btn = $('ambience-toggle');
    if (!btn) return;
    const sync = () => { btn.textContent = muted ? '🔇' : '🔊'; btn.title = muted ? 'Unmute ambience' : 'Mute ambience'; };
    sync();
    btn.onclick = () => {
      muted = !muted;
      localStorage.setItem('misthollow_ambience', muted ? 'off' : 'on');
      if (master) master.gain.value = muted ? 0 : 1;
      MH.bus.emit('audio.mute', muted);   // also silence FX stings + sfx
      sync();
    };
  });
})();
