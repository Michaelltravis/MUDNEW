// Which steed each mount is (steed.js draws it): the creature kit's body, coat words and colour,
// its size beside its rider, and its extras. Pure, so Node can check it (tests/web/steeds.test.mjs).

// key -> [kit body, coat words, coat colour, height as a share of the rider's, extras]
export const STEEDS = {
  horse: ['horse', 'bay horse', 0x6b4a2e, 1.0, {}],
  warhorse: ['horse', 'grey horse', 0x6a6a70, 1.1, { barding: 0x7a2a22 }],
  armored_warhorse: ['horse', 'white horse', 0xc8c4bc, 1.1, { barding: 0x2a4a8a }],
  celestial_charger: ['horse', 'white horse', 0xf0ece0, 1.1, { barding: 0xe8c860, glow: 0xffe8a0 }],
  nightmare: ['horse', 'black infernal horse', 0x18141a, 1.1, { flames: true }],
  nightmare_steed: ['horse', 'black infernal horse', 0x18141a, 1.1, { flames: true }],
  clockwork_steed: ['horse', 'brass horse', 0xb8904a, 1.05, { brass: true }],
  donkey: ['horse', 'grey donkey', 0x8a8478, 0.8, {}],
  pony: ['horse', 'dappled pony', 0xd8ccb0, 0.8, {}],
  griffin: ['cat', 'golden lion', 0xc89a52, 0.95, { wings: 0xd8b880 }],
  manabound_gryphon: ['cat', 'blue', 0x5a7ac8, 0.95, { wings: 0x9ab8ff, glow: 0x8ab0ff }],
  mana_wyrm: ['horse', 'blue spectral', 0x4a6ad8, 1.0, { glow: 0x9ab8ff }],
  moonstag: ['deer', 'white silver stag', 0xdcdce8, 1.05, {}],
  stoneboar: ['pig', 'grey boar', 0x6a625a, 0.8, { barding: 0x5a5a62 }],
  merchant_camel: ['llama', 'tan camel', 0xc8a878, 1.15, {}],
  shadowpanther: ['cat', 'black panther', 0x1a1820, 0.8, {}],
  shadowcat: ['cat', 'grey', 0x5a5a62, 0.75, {}],
  dire_warg: ['wolf', 'black warg', 0x2a2622, 0.9, {}],
  riding_spider: ['wolf', 'black', 0x1e1a22, 0.8, { glow: 0x8a2aff }],
  drake_whelp: ['cat', 'red scaled', 0x8a2a1a, 0.85, { flames: true }],
  ancient_treant: ['cow', 'brown bark', 0x5a4028, 1.05, {}],
};
const DEFAULT = STEEDS.horse;
// where the saddle sits, as a share of the steed's height, by kit body
const BACK = { horse: 0.74, deer: 0.74, cat: 0.72, pig: 0.82, llama: 0.64, wolf: 0.72, cow: 0.76 };


export function steedSpec(key) {
  const [body, words, tint, height, extra] = STEEDS[key] || DEFAULT;
  return { key, body, words, tint, height, extra, back: BACK[body] || 0.72 };
}
