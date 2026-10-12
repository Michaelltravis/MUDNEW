// A creature's own body, as a recipe: which skeleton (plan), which parts, its proportions, colours
// and markings, read from the words of its name and description and filled in from a seed (its
// prototype number), so every kind of creature in the world looks like itself and no two kinds
// look the same. Pure data, no three.js: looks.js attaches a recipe to a creature's look, kin.js
// builds the body, and tools/qc_bestiary.mjs checks the world's creatures stay distinct.
//
// Push 1 covers the wildlife: four-legged beasts (quad), birds (bird) and swimmers (fish).

// which skeleton a bestiary body becomes, and the parts it starts from
const QUAD = {
  wolf: { head: 'pointed', ears: 'pointed', tail: 'bushy', len: 1.05, leg: 0.42, girth: 0.36, neck: 0.25 },
  dog: { head: 'pointed', ears: 'floppy', tail: 'thin', len: 0.95, leg: 0.4, girth: 0.36, neck: 0.22 },
  pug: { head: 'blunt', ears: 'floppy', tail: 'stub', len: 0.8, leg: 0.3, girth: 0.38, neck: 0.15 },
  fox: { head: 'pointed', ears: 'tall', tail: 'bushy', len: 0.95, leg: 0.34, girth: 0.3, neck: 0.22 },
  cat: { head: 'blunt', ears: 'pointed', tail: 'long', len: 1.0, leg: 0.38, girth: 0.32, neck: 0.2 },
  deer: { head: 'long', ears: 'pointed', tail: 'stub', len: 1.0, leg: 0.62, girth: 0.34, neck: 0.42 },
  horse: { head: 'long', ears: 'pointed', tail: 'tuft', mane: true, len: 1.15, leg: 0.62, girth: 0.42, neck: 0.48 },
  zebra: { head: 'long', ears: 'pointed', tail: 'tuft', mane: true, len: 1.1, leg: 0.6, girth: 0.42, neck: 0.46, pattern: 'stripes' },
  llama: { head: 'long', ears: 'tall', tail: 'stub', len: 0.95, leg: 0.6, girth: 0.4, neck: 0.62, fur: 'shaggy' },
  cow: { head: 'blunt', ears: 'round', horns: 'horns', tail: 'tuft', len: 1.15, leg: 0.45, girth: 0.52, neck: 0.18 },
  sheep: { head: 'blunt', ears: 'floppy', tail: 'stub', len: 0.95, leg: 0.36, girth: 0.5, neck: 0.18, fur: 'shaggy' },
  pig: { head: 'snout', ears: 'floppy', tail: 'curl', len: 1.0, leg: 0.26, girth: 0.46, neck: 0.1 },
  farm_pig: { head: 'snout', ears: 'pointed', tail: 'curl', len: 1.0, leg: 0.27, girth: 0.46, neck: 0.1 },
  panda: { head: 'blunt', ears: 'round', tail: 'stub', len: 1.0, leg: 0.36, girth: 0.56, neck: 0.15, fur: 'shaggy' },
  'proc:rat': { head: 'pointed', ears: 'round', tail: 'thin', len: 0.95, leg: 0.16, girth: 0.34, neck: 0.1 },
  'proc:rabbit': { head: 'blunt', ears: 'long', tail: 'puff', len: 0.75, leg: 0.24, girth: 0.42, neck: 0.12, gait: 'hop' },
  'proc:lizard': { head: 'long', ears: 'none', tail: 'long', len: 1.0, leg: 0.16, girth: 0.26, neck: 0.12, fur: 'scale', gait: 'sprawl' },
};
const BIRD = {
  bird: { beak: 'short', leg: 0.22, wing: 0.55, tail: 'fan', girth: 0.42 },
  eagle: { beak: 'hook', leg: 0.22, wing: 0.75, tail: 'fan', girth: 0.44 },
  chicken: { beak: 'short', leg: 0.24, wing: 0.38, tail: 'plume', girth: 0.5, crest: 'comb' },
  chick: { beak: 'short', leg: 0.16, wing: 0.3, tail: 'none', girth: 0.6 },
  penguin: { beak: 'short', leg: 0.1, wing: 0.4, tail: 'none', girth: 0.42, stance: 'upright' },
  bat: { beak: 'snout', leg: 0.08, wing: 0.95, tail: 'none', girth: 0.4, wingType: 'leather', ears: true },
};
const FISH = {
  fish: { snout: 'round', dorsal: 'small', tail: 'fork', len: 1.0, girth: 0.42 },
  piranha: { snout: 'pointed', dorsal: 'tall', tail: 'fork', len: 1.15, girth: 0.34 },    // sharks
  whale: { snout: 'round', dorsal: 'none', tail: 'flukes', len: 1.25, girth: 0.5, flippers: true },
};

// words in a creature's name that change its parts
const WORDS = [
  [/\b(stag|hart|buck|elk|moose|caribou|reindeer|antlered|antler)\b/, { horns: 'antlers' }],
  [/\b(ram|goat|ibex|mountain goat)\b/, { horns: 'curled' }],
  [/\b(bull|ox|oxen|aurochs|bison|buffalo|yak|horned)\b/, { horns: 'horns' }],
  [/\b(boar|warthog|tusked|tusk)\b/, { horns: 'tusks' }],
  [/\b(unicorn)\b/, { horns: 'spike' }],
  [/\b(badger|skunk)\b/, { pattern: 'blaze', head: 'pointed', ears: 'round' }],
  [/\b(shaggy|woolly|wooly|moss-backed|matted|thick-furred)\b/, { fur: 'shaggy' }],
  [/\b(lean|gaunt|scrawny|starving|skinny|wiry)\b/, { thin: true }],
  [/\b(stocky|bristly|heavy|thickset|burly|hulking|massive)\b/, { stout: true }],
  [/\b(striped|tabby|tiger|banded)\b/, { pattern: 'stripes' }],
  [/\b(spotted|dappled|leopard|speckled|piebald)\b/, { pattern: 'spots' }],
  [/\b(grizzled|silver-backed|saddle|black-backed|grey-backed)\b/, { pattern: 'saddle' }],
  [/\b(spiked|spined|spiny|ridged)\b/, { spikes: true }],
  [/\b(spectral|ghostly|undead|rotting|zombie|skeletal|cursed|demonic|hell|infernal|glowing|frost|winter|rabid)\b/, { eyes: 'glow' }],
  [/\b(heron|crane|stork|egret|flamingo)\b/, { beak: 'long', leg: 0.5, neckLong: true }],
  [/\b(duck|goose|swan|drake)\b/, { beak: 'flat', leg: 0.12 }],
  [/\b(owl)\b/, { beak: 'hook', face: 'owl', ears: false }],
  [/\b(crow|raven|rook|jackdaw|magpie)\b/, { beak: 'straight' }],
  [/\b(gull|tern|albatross)\b/, { beak: 'straight', wing: 0.8 }],
  [/\b(hawk|falcon|kestrel|vulture|condor)\b/, { beak: 'hook' }],
  [/\b(hammerhead)\b/, { snout: 'hammer' }],
  [/\b(seal|walrus|sea lion|sealion)\b/, { dorsal: 'none', tail: 'flippers', flippers: true, snout: 'whisker' }],
  [/\b(walrus)\b/, { horns: 'tusks' }],
  [/\b(eel|lamprey)\b/, { len: 1.6, girth: 0.22, dorsal: 'ridge' }],
  [/\b(flying fish)\b/, { fins: 'wings' }],
];

// colour words: main coat, then a belly and markings worked out from it
const COAT = [[/\b(black|ebony|dark|sable|shadow)\b/, 0x34343c], [/\b(white|snowy|ivory|albino|pale|arctic|frost|winter|snow|ice)\b/, 0xe4e8ec],
  [/\b(grey|gray|ashen|ash-grey|slate|silver)\b/, 0x8c8c94], [/\b(brown|bay|chestnut|umber|mud-brown)\b/, 0x7a5434],
  [/\b(tawny|tan|sandy|dun|fawn|buff|golden)\b/, 0xb8925a], [/\b(red|russet|rust|ginger|auburn)\b/, 0xb4602e], [/\b(crimson|blood-red|scarlet)\b/, 0x9a2a24],
  [/\b(green|moss|emerald)\b/, 0x5a7a3a], [/\b(blue|azure)\b/, 0x4a6aa8], [/\b(yellow)\b/, 0xd8b040],
  [/\b(spotted|piebald)\b/, 0xd8cfc0]];
// the coat a species wears when its words name no colour (before the bestiary's tint for its body)
const SPECIES = [[/\b(crow|raven|rook|jackdaw|bat)\b/, 0x2a2a30], [/\b(gull|tern|albatross|swan|egret)\b/, 0xdedfe0],
  [/\b(heron|crane)\b/, 0x9aa0a8], [/\b(owl)\b/, 0x9a7a54], [/\b(hawk|eagle|falcon|kestrel|buzzard)\b/, 0x7a5a3a],
  [/\b(penguin|orca|killer whale|magpie)\b/, 0x26262c], [/\b(seal|walrus|sea lion)\b/, 0x7a7c80],
  [/\b(shark|hammerhead)\b/, 0x70808e], [/\b(trout|salmon|perch|carp|pike)\b/, 0x7a8a5a],
  [/\b(wolf|wolves)\b/, 0x7c7a78], [/\b(fox)\b/, 0xb4602e], [/\b(bear)\b/, 0x5e4430], [/\b(boar|warthog)\b/, 0x5a4a3c],
  [/\b(stag|deer|hart|doe)\b/, 0x9a6a42], [/\b(hare|rabbit)\b/, 0x9a7e60], [/\b(goat|ram|sheep)\b/, 0xc8bea8],
  [/\b(badger)\b/, 0x4a4a4e], [/\b(aurochs|bull|ox|bison)\b/, 0x4a3a2e], [/\b(horse|pony|mare|stallion)\b/, 0x7a5a3a]];
// coats a kind of beast wears when its words name none
const NATURAL = {
  quad: [0x7a6a58, 0x8a6a48, 0x5a5048, 0x9a8a70, 0x6a5a4a, 0xa08060, 0x584a40],
  bird: [0x6a5a4a, 0x8a7a6a, 0x4a4a52, 0x9a8a6a, 0xb0a890],
  fish: [0x5a7a9a, 0x7a8aa0, 0x4a6a7a, 0x8aa0a8, 0x6a7a6a],
};

// a small deterministic random stream from a seed
export function rng(seed) {
  let s = (seed >>> 0) || 1;
  return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return (s % 100000) / 100000; };
}
const pick = (r, list) => list[Math.floor(r() * list.length) % list.length];
const jig = (r, v, amt) => +(v * (1 + (r() * 2 - 1) * amt)).toFixed(3);

function shade(hex, k) {
  const c = [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255].map(v => Math.max(0, Math.min(255, Math.round(k >= 1 ? v + (255 - v) * (k - 1) : v * k))));
  return (c[0] << 16) | (c[1] << 8) | c[2];
}
// a nudge in colour so two grey wolves are two greys
function drift(r, hex, amt = 0.08) {
  const c = [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255].map(v => Math.max(0, Math.min(255, Math.round(v * (1 + (r() * 2 - 1) * amt)))));
  return (c[0] << 16) | (c[1] << 8) | c[2];
}

// The recipe for a creature whose bestiary body is `body` ('wolf', 'proc:rat'...), from all its
// words and a seed; null when that body is not yet one of the kit's skeletons.
export function kinRecipe(body, all, seed, tint = null) {
  const words = String(all || '').toLowerCase();
  let plan, base;
  if (QUAD[body]) { plan = 'quad'; base = QUAD[body]; }
  else if (BIRD[body]) { plan = 'bird'; base = BIRD[body]; }
  else if (FISH[body]) { plan = 'fish'; base = FISH[body]; }
  else return null;
  const r = rng(seed);
  const p = { ...base };
  for (const [re, add] of WORDS) if (re.test(words)) Object.assign(p, add);
  const coat = (COAT.find(([re]) => re.test(words)) || [])[1];
  // its own colour words first, then the bestiary's tint for its kind, then a natural coat
  const species = (SPECIES.find(([re]) => re.test(words)) || [])[1];
  const main = drift(r, coat != null ? coat : species != null ? species : tint != null ? tint : pick(r, NATURAL[plan]));
  const lightBelly = plan !== 'quad' || r() < 0.7;
  const c = { main, belly: shade(main, lightBelly ? 1.45 : 0.85), accent: shade(main, 0.55), eye: p.eyes === 'glow' ? 'glow' : 'dark' };
  if (body === 'panda' && !coat && tint == null) c.belly = shade(main, 1.3);
  const out = { plan, seed: seed >>> 0, c };
  if (plan === 'quad') {
    const stout = p.stout ? 1.15 : 1, thin = p.thin ? 0.82 : 1;
    Object.assign(out, {
      head: p.head, ears: p.ears, tail: p.tail, horns: p.horns || 'none', mane: !!p.mane, fur: p.fur || 'fur',
      gait: p.gait || 'walk', spikes: !!p.spikes,
      pattern: p.pattern || pick(r, ['plain', 'plain', 'plain', 'saddle', 'socks', 'blaze']),
      len: jig(r, p.len * (p.thin ? 1.05 : 1), 0.08), leg: jig(r, p.leg, 0.1), girth: jig(r, p.girth * stout * thin, 0.08),
      neck: jig(r, p.neck, 0.12), headSize: jig(r, 1, 0.1), earSize: jig(r, 1, 0.18), tailLen: jig(r, 1, 0.2),
    });
  } else if (plan === 'bird') {
    Object.assign(out, {
      beak: p.beak, tail: p.tail, crest: p.crest || pick(r, ['none', 'none', 'none', 'tuft']), stance: p.stance || 'perch',
      wingType: p.wingType || 'feather', ears: !!p.ears, face: p.face || 'plain', neckLong: !!p.neckLong,
      pattern: p.pattern || pick(r, ['plain', 'plain', 'bars', 'cap', 'collar']),
      leg: jig(r, p.leg, 0.12), wing: jig(r, p.wing, 0.1), girth: jig(r, p.girth, 0.08), headSize: jig(r, 1, 0.1),
    });
    if (out.pattern === 'cap' || out.pattern === 'collar') c.accent = shade(main, r() < 0.5 ? 0.45 : 1.6);
  } else {
    Object.assign(out, {
      snout: p.snout, dorsal: p.dorsal, tail: p.tail, flippers: !!p.flippers, fins: p.fins || 'plain',
      pattern: p.pattern || (p.flippers ? pick(r, ['plain', 'countershade']) : pick(r, ['plain', 'plain', 'stripes', 'spots', 'countershade'])),
      len: jig(r, p.len, 0.08), girth: jig(r, p.girth, 0.08), finSize: jig(r, 1, 0.15),
    });
  }
  return out;
}

// what makes two recipes the same body: everything but the seed, the colours rounded (so a shade
// apart is not "different")
export function kinSignature(k) {
  if (!k) return '';
  const round = v => (typeof v === 'number' ? +v.toFixed(2) : v);
  const parts = Object.entries(k).filter(([key]) => key !== 'seed' && key !== 'c').map(([key, v]) => `${key}=${round(v)}`);
  const col = h => ((h >> 20) & 15).toString(16) + ((h >> 12) & 15).toString(16) + ((h >> 4) & 15).toString(16);
  return parts.sort().join(',') + `|${col(k.c.main)}`;
}
