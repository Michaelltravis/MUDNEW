// Speech over heads: when someone in view speaks ("Sage Aldric says, '...'"), the words float
// over them for a few seconds in a parchment bubble, as well as in the chat log. Positioned
// once the camera is placed for the frame (like the nameplates).
import * as THREE from 'three';

const MAX = 4;

export function createBubbles(container, engine) {
  const live = [];
  const v = new THREE.Vector3();
  function say(root, text, { lift = 2.6, npc = true } = {}) {
    if (!root || !text) return;
    // one bubble per speaker: a new line replaces the last
    for (let i = live.length - 1; i >= 0; i--) if (live[i].root === root) { live[i].el.remove(); live.splice(i, 1); }
    const el = document.createElement('div');
    el.className = `bubble${npc ? ' npc' : ''}`;
    el.textContent = text.length > 160 ? `${text.slice(0, 157)}…` : text;
    container.appendChild(el);
    const ms = Math.min(9000, 2800 + text.length * 45);
    live.push({ root, el, lift, until: performance.now() + ms });
    while (live.length > MAX) live.shift().el.remove();
  }
  function update() {
    const now = performance.now(), cam = engine.camera, cv = engine.renderer.domElement;
    for (let i = live.length - 1; i >= 0; i--) {
      const b = live[i];
      if (now > b.until || !b.root.parent) { b.el.remove(); live.splice(i, 1); continue; }
      v.copy(b.root.position).setY(b.root.position.y + b.lift).project(cam);
      const off = v.z > 1 || Math.abs(v.x) > 1.05 || Math.abs(v.y) > 1.05;
      b.el.style.display = off ? 'none' : '';
      if (!off) b.el.style.transform = `translate(${((v.x + 1) / 2 * cv.clientWidth).toFixed(1)}px, ${((1 - v.y) / 2 * cv.clientHeight).toFixed(1)}px) translate(-50%, -100%)`;
      b.el.style.opacity = b.until - now < 600 ? (b.until - now) / 600 : 1;
    }
  }
  return { say, update };
}
