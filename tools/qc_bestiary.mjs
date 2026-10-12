// QC: which 3D body every creature and NPC in the world gets (world3d/looks.js).
//   node tools/qc_bestiary.mjs              every mob, grouped by body
//   node tools/qc_bestiary.mjs wolf goblin  only mobs whose text matches
//   node tools/qc_bestiary.mjs --suspects   only people whose description names a creature
// Exits non-zero when a creature word turns into a person (tests/web/looks.test.mjs runs it).
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { creatureLook, describe } from '../src/web_isometric/world3d/looks.js';

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');

// the mob entries the map payload sends (map_system.py), from the zone prototypes
export function loadMobs(dir = path.join(ROOT, 'world/zones')) {
  const out = [];
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith('.json')).sort()) {
    const z = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    for (const p of Object.values(z.mobs || {})) {
      const flags = p.flags || [];
      out.push({
        name: p.name || '', short: p.short_desc || '', long: String(p.long_desc || '').slice(0, 80), pv: p.vnum, flags, level: p.level,
        hostile: flags.includes('aggressive') || !!p.hostile,
        boss: flags.includes('boss') || !!p.boss || !!p.is_boss,
        shopkeeper: p.special === 'shopkeeper',
        trainer: p.special === 'trainer' || p.special === 'guildmaster',
        zone: z.number,
      });
    }
  }
  return out;
}

export function lookLabel(look) {
  if (look.beast) {
    const b = look.beast;
    const what = b.mob ? b.mob : b.proc ? `proc:${b.proc}` : b.prop ? `prop:${b.prop[1]}` : '?';
    return `${what} ${b.h}m${b.fly ? ' fly' : ''}`;
  }
  const kit = (look.loadout || []).join('+');
  return `${look.model}${look.scale ? ` x${(+look.scale).toFixed(2)}` : ''}${kit ? ` [${kit}]` : ''}${look.still ? ' still' : ''}`;
}

// words that name a creature, never a person: if one is the head noun, or stands right before a
// ruler's title ("the spider queen"), a person body is a mistake. Bodies the bestiary itself
// gives a person's shape (golems, statues, hags) are meant.
const CREATURE = /^(blob|ooze|slime|jelly|pudding|spider|beetle|worm|maggot|centipede|rat|wolf|bear|snake|serpent|dragon|drake|wyvern|bat|bird|crow|raven|eagle|hawk|owl|fox|deer|stag|boar|pig|cow|bull|horse|pony|sheep|goat|dog|hound|cat|lion|tiger|panther|crab|scorpion|fish|eel|shark|frog|toad|lizard|crocodile|basilisk|golem|statue|elemental|treant|tree|mushroom|myconid|myconoid|fungus|mimic|ghost|wraith|spectre|specter|demon|devil|imp|troll|ogre|giant|cyclops|minotaur|yeti|beholder|harpy|griffon|hydra|naga|sphinx|chimera|unicorn|pegasus|bee|wasp|hornet|ant|mosquito|fly|moth|squirrel|rabbit|hare|badger|weasel|vulture|swan|duck|goose|chicken|hen|rooster|whale|octopus|squid|kraken|goblin|kobold)s?$/;
const RULER = /^(king|queen|lord|lady|chief|chieftain|leader|master|mistress|matron|mother|elder|shaman|priest|priestess|warrior|guard|guardian|champion|captain|soldier|mage|wizard|witch|knight|druid|sage|warden|sentry)$/;

export function suspects(mobs) {
  const bad = [];
  for (const m of mobs) {
    const look = creatureLook(m);
    if (look.beast || /^skeleton/.test(look.model) || look.why === 'bestiary') continue;
    const { head, words } = describe(m);
    const before = words[words.length - 2] || '';
    if (CREATURE.test(head) || (RULER.test(head) && CREATURE.test(before))) bad.push({ m, look });
  }
  return bad;
}

function main(args) {
  const mobs = loadMobs();
  if (args.includes('--suspects')) {
    const bad = suspects(mobs);
    for (const { m, look } of bad) console.log(`${String(m.pv).padStart(5)}  ${m.short.padEnd(42)} ${lookLabel(look)}`);
    console.log(`${bad.length} suspect(s) of ${mobs.length}`);
    return bad.length ? 1 : 0;
  }
  const want = args.filter(a => !a.startsWith('--')).map(a => a.toLowerCase());
  const groups = new Map();
  for (const m of mobs) {
    const text = `${m.name} ${m.short}`.toLowerCase();
    if (want.length && !want.some(w => text.includes(w))) continue;
    const look = creatureLook(m);
    const b = look.beast;
    const key = b ? b.mob || (b.proc && `proc:${b.proc}`) || `prop:${b.prop[1]}`
      : /^skeleton/.test(look.model) ? `undead:${look.model}` : `person:${look.model}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push({ m, look });
  }
  for (const [key, list] of [...groups].sort((a, b) => b[1].length - a[1].length)) {
    console.log(`\n== ${key} (${list.length})`);
    for (const { m, look } of list) {
      const role = m.shopkeeper ? ' {shop}' : m.trainer ? ' {trainer}' : m.boss ? ' {boss}' : '';
      console.log(`${String(m.pv).padStart(5)}  ${(m.short || m.name).slice(0, 44).padEnd(44)} ${lookLabel(look)}${role}  <${look.why}>`);
    }
  }
  const bad = suspects(mobs);
  console.log(`\n${mobs.length} mobs; ${bad.length} creature word(s) shown as people`);
  return bad.length ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) process.exitCode = main(process.argv.slice(2));
