// The one-key prompt that floats over something you can use right now ("E  Open the oak
// door", "Locked — needs a rusted watch-key"). One at a time; placed in world space each frame.
import * as THREE from 'three';

const _v = new THREE.Vector3();

export function createPrompt(root) {
  const el = root;
  const keyEl = el.querySelector('kbd');
  const textEl = el.querySelector('span');
  let at = null, shown = '';
  return {
    show(pos, p) {
      if (!p) return this.hide();
      at = pos;
      const sig = `${p.key}|${p.text}|${p.tone}`;
      if (sig !== shown) {
        shown = sig;
        keyEl.textContent = p.key || '';
        keyEl.style.display = p.key ? '' : 'none';
        textEl.textContent = p.text;
        el.className = `prompt tone-${p.tone || 'open'}`;
      }
    },
    hide() { at = null; if (shown) { shown = ''; el.className = 'prompt hidden'; } },
    get visible() { return !!at; },
    // after the camera is placed: pin the pill above its spot
    update(camera, canvas) {
      if (!at) return;
      _v.copy(at).project(camera);
      if (_v.z > 1) { el.style.opacity = 0; return; }
      el.style.opacity = 1;
      const x = (_v.x + 1) / 2 * canvas.clientWidth, y = (1 - _v.y) / 2 * canvas.clientHeight;
      el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -100%)`;
    },
  };
}
