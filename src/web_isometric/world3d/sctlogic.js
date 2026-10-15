// Scrolling combat text: what colour a number is and what it says (combat.js draws it, fx.js
// moves it). Pure, so tests/web/sct.test.mjs can check it without a scene.

// a blow's number in the colour of its harm; physical is cream
export const SCHOOL_CSS = { physical: '#fff1d6', fire: '#ff8a3a', frost: '#9fdcff', lightning: '#c6dcff', arcane: '#cf8aff',
  holy: '#ffe27a', shadow: '#a878f0', nature: '#8ae860', poison: '#b6f04e', necrotic: '#7ef0a0', blood: '#ff4a4a', sound: '#ffb8ff' };

// "pyroblast" -> "Pyroblast", "meteor_storm" -> "Meteor Storm"
export const titleOf = s => String(s || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// the colour a wound is drawn in: its school's, else (physical) the element of the striker's
// weapon once it glows (tier 4 and up, as its blow's trail), else cream
export function harmColour(school, look) {
  const s = school && school !== 'physical' && school !== 'magic' ? school : null;
  if (s && SCHOOL_CSS[s]) return SCHOOL_CSS[s];
  const m = look && look.main;
  if (m && m.e && (m.t || 0) >= 4 && SCHOOL_CSS[m.e]) return SCHOOL_CSS[m.e];
  return SCHOOL_CSS.physical;
}
