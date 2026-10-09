// Login and character creation for the 3D client. The protocol is the server's own
// prompts, driven through net.js (MH.connect): name/password, then for a new hero the
// race, class and stat-roll prompts, answered from these screens. The class step shows the
// class's 3D model turning on a small stage.
import * as THREE from 'three';
import { spawnCharacter } from '../assets.js';
import { classModel } from '../entities.js';

const $ = s => document.querySelector(s);
const NAME_KEY = 'misthollow_name', PW_KEY = 'misthollow_pw';   // shared with the 2D client
const ls = { get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} } };

const RACES = [
  ['human', 'Versatile and balanced — at home anywhere.'],
  ['elf', 'Graceful and magical, keen of mind and eye.'],
  ['dwarf', 'Sturdy and tough, hewn from living stone.'],
  ['halfling', 'Nimble and lucky — small, quick, hard to hit.'],
  ['half_orc', 'Fierce and mighty, a born brawler.'],
  ['gnome', 'Clever and arcane, a tinkering mind.'],
  ['dark_elf', 'Deadly shadow-kin, swift and merciless.'],
];
const CLASSES = [
  ['warrior', 'Tank', 'Master of melee and defence — sturdy and relentless.', 'STR'],
  ['cleric', 'Healer', 'Divine healer who mends allies and smites the undead.', 'WIS'],
  ['ranger', 'Ranged', 'Wilderness warrior blending bow and nature magic.', 'DEX'],
  ['mage', 'Caster', 'Commands devastating arcane spells from afar.', 'INT'],
  ['thief', 'Stealth', 'Cunning rogue who strikes from the shadows.', 'DEX'],
  ['paladin', 'Tank · Healer', 'Holy warrior — martial skill fused with divine power.', 'STR'],
  ['necromancer', 'Summoner', 'Dark mage who commands death and the undead.', 'INT'],
  ['bard', 'Support', 'Charismatic performer who inspires with magical songs.', 'CHA'],
  ['assassin', 'Burst', 'Deadly killer who eliminates targets with precision.', 'DEX'],
];
const FIRST = new Set(['warrior', 'cleric', 'ranger']);

export function setupLogin() {
  const name = $('#login-name'), pass = $('#login-pass'), status = $('#login-status');
  const create = $('#create');
  let creating = false, prime = '';
  const saved = ls.get(NAME_KEY), savedPw = ls.get(PW_KEY);
  if (saved) name.value = saved;
  if (savedPw) { try { pass.value = atob(savedPw); } catch (_) {} }
  const say = (msg, err) => { status.textContent = msg || ''; status.className = err ? 'error' : ''; };

  function begin(isNew) {
    const n = name.value.trim(), p = pass.value;
    if (!n || !p) return say('Need both a name and a password.', true);
    if (isNew && !/^[a-zA-Z]{3,12}$/.test(n)) return say('A name is 3–12 letters (no spaces, numbers or symbols).', true);
    creating = isNew;
    if (isNew) wizard('', 'FORGE YOUR HERO', 'Summoning the loom of fate…', '');
    MH.connect(n, p, isNew);
  }
  $('#login-btn').addEventListener('click', () => begin(false));
  $('#create-btn').addEventListener('click', () => begin(true));
  pass.addEventListener('keydown', e => { if (e.key === 'Enter') begin(false); e.stopPropagation(); });
  name.addEventListener('keydown', e => { if (e.key === 'Enter') pass.focus(); e.stopPropagation(); });

  // ---- creation wizard ----
  const send = v => { const s = MH.state.mudSocket; if (s && s.readyState === WebSocket.OPEN) s.send(v); };
  function wizard(step, title, hint, body) {
    create.classList.remove('hidden');
    create.querySelector('.step').textContent = step;
    create.querySelector('h2').textContent = title;
    create.querySelector('.hint').textContent = hint;
    create.querySelector('.body').innerHTML = body;
  }
  function races() {
    wizard('STEP 1 OF 3', 'CHOOSE YOUR LINEAGE', 'Your bloodline shapes your gifts and your fate.',
      `<div class="grid">${RACES.map(([id, de]) => `<div class="pick" data-v="${id}"><b>${id.replace('_', ' ')}</b><small>${de}</small></div>`).join('')}</div>`);
    create.querySelectorAll('.pick').forEach(el => el.addEventListener('click', () => { send(el.dataset.v); wizard('', 'FORGE YOUR HERO', 'Weaving your lineage…', ''); }));
  }
  let stage = null;
  function classes() {
    wizard('STEP 2 OF 3', 'CHOOSE YOUR CALLING', 'Pick a class to see it up close. Three are marked as good first picks.',
      `<div class="split"><div class="grid">${CLASSES.map(([id, role]) =>
        `<div class="pick" data-v="${id}"><b>${id}</b><small>${role}</small>${FIRST.has(id) ? '<div class="first">★ first pick</div>' : ''}</div>`).join('')}</div>`
      + `<div class="focus"><canvas width="520" height="600"></canvas><div class="fn"></div><p class="fd"></p><p class="fs"></p>`
      + `<button class="btn" id="choose-class" disabled>Choose</button></div></div>`);
    stage = stage || makeStage();
    stage.attach(create.querySelector('canvas'));
    let pick = null;
    const focus = id => {
      pick = id;
      create.querySelectorAll('.pick').forEach(el => el.classList.toggle('on', el.dataset.v === id));
      const c = CLASSES.find(x => x[0] === id);
      prime = c[3];
      create.querySelector('.fn').textContent = id;
      create.querySelector('.fd').textContent = c[2];
      create.querySelector('.fs').textContent = `Role: ${c[1]} · Prime stat: ${c[3]}`;
      const b = $('#choose-class'); b.disabled = false; b.textContent = `Choose ${id}`;
      stage.show(id);
    };
    create.querySelectorAll('.pick').forEach(el => el.addEventListener('click', () => focus(el.dataset.v)));
    $('#choose-class').addEventListener('click', () => { if (pick) { send(pick); stage.stop(); wizard('', 'FORGE YOUR HERO', 'Rolling the dice of fate…', ''); } });
    focus('warrior');
  }
  function stats(text) {
    const map = { Strength: 'STR', Intelligence: 'INT', Wisdom: 'WIS', Dexterity: 'DEX', Constitution: 'CON', Charisma: 'CHA' };
    const re = /(Strength|Intelligence|Wisdom|Dexterity|Constitution|Charisma):\s*(\d+)/g;
    let m, cells = '';
    while ((m = re.exec(text))) cells += `<div class="${map[m[1]] === prime ? 'prime' : ''}"><div class="v">${m[2]}</div><div class="k">${map[m[1]]}</div></div>`;
    wizard('STEP 3 OF 3', 'ROLL YOUR FATE', 'The dice favour the bold — keep them, or tempt fate again.',
      `<div class="stats">${cells}</div><div class="row2"><button class="btn" id="keep">Keep these</button><button class="btn alt" id="reroll">Reroll</button></div>`);
    $('#keep').addEventListener('click', () => { send('y'); wizard('', 'FORGE YOUR HERO', 'Your story begins…', ''); });
    $('#reroll').addEventListener('click', () => send('n'));
  }
  MH.bus.on('terminal.output', ({ text }) => {
    if (!creating || MH.state.isLoggedIn || !text) return;
    if (/choose your race|race name or number/i.test(text)) return races();
    if (/choose your class|class name or number/i.test(text)) return classes();
    if (/accept these stats|to reroll/i.test(text) || /Strength:\s*\d+/.test(text)) return stats(text);
    const note = text.split('\n').map(l => l.trim()).filter(Boolean).slice(-1)[0];
    if (note && /invalid|already|taken|try again|not a valid|must (?:be|contain)|in use/i.test(note)) {
      wizard('', 'FORGE YOUR HERO', note.slice(0, 140), '<button class="btn alt" id="restart">Start over</button>');
      $('#restart').addEventListener('click', () => location.reload());
    }
  });
  MH.bus.on('create.blocked', msg => {
    if (!creating) return;
    wizard('', 'FORGE YOUR HERO', msg, '<button class="btn alt" id="restart">Start over</button>');
    $('#restart').addEventListener('click', () => location.reload());
  });
  MH.bus.on('login.status', msg => say(msg));
  MH.bus.on('login.error', msg => say(msg, true));
  MH.bus.on('login.success', () => {
    creating = false;
    create.classList.add('hidden');
    $('#login').classList.add('hidden');
    if (stage) stage.stop();
    ls.set(NAME_KEY, MH.state.playerName);
    ls.set(PW_KEY, btoa(MH.state.playerPassword));
  });
}

// a small second renderer: the chosen class turning on a plinth
function makeStage() {
  let renderer = null, canvas = null, actor = null, raf = 0, token = 0;
  const scene = new THREE.Scene();
  const cam = new THREE.PerspectiveCamera(30, 520 / 600, 0.1, 50);
  cam.position.set(0, 1.6, 6.2); cam.lookAt(0, 1.05, 0);
  scene.add(new THREE.HemisphereLight(0xdde6ff, 0x2a2018, 1.4));
  const key = new THREE.DirectionalLight(0xffe2b0, 2.6); key.position.set(2.5, 4, 3); scene.add(key);
  const rim = new THREE.DirectionalLight(0x8ab0ff, 1.6); rim.position.set(-3, 2.5, -3); scene.add(rim);
  const plinth = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 1.25, 0.25, 40),
    new THREE.MeshStandardMaterial({ color: 0x3a3442, roughness: 0.6, metalness: 0.2 }));
  plinth.position.y = -0.125; scene.add(plinth);
  const clock = new THREE.Clock();
  const loop = () => {
    raf = requestAnimationFrame(loop);
    const dt = Math.min(clock.getDelta(), 0.05);
    if (actor) { actor.update(dt); actor.root.rotation.y += dt * 0.5; }
    if (renderer) renderer.render(scene, cam);
  };
  return {
    attach(cv) {
      if (canvas !== cv) {
        if (renderer) renderer.dispose();
        canvas = cv;
        renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
        renderer.outputColorSpace = THREE.SRGBColorSpace;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
      }
      if (!raf) { clock.getDelta(); loop(); }
    },
    async show(cls) {
      const my = ++token;
      const look = classModel(cls);
      const a = await spawnCharacter(look.model, { tint: look.tint });
      if (my !== token) return;
      if (actor) scene.remove(actor.root);
      actor = a;
      scene.add(actor.root);
      actor.play('Idle', 0);
      actor.once(/mage|necro|cleric|bard/.test(cls) ? 'Spellcast_Shoot' : /ranger/.test(cls) ? '1H_Ranged_Shoot' : '1H_Melee_Attack_Chop', 0.1, 1);
    },
    stop() { cancelAnimationFrame(raf); raf = 0; if (renderer) { renderer.dispose(); renderer = null; canvas = null; } },
  };
}
