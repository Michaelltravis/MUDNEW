// F3: frame rate, frame time, draw calls and the GPU, plus a "copy report" button so
// the owner can paste exact numbers instead of "it feels choppy".
export function attachPerf(engine, el) {
  const times = [];
  let last = performance.now(), shown = false, acc = 0;
  const gl = engine.renderer.getContext();
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  const gpu = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
  const stats = () => {
    const s = times.slice().sort((a, b) => a - b);
    const avg = s.reduce((a, b) => a + b, 0) / Math.max(1, s.length);
    const p95 = s[Math.floor(s.length * 0.95)] || 0;
    const info = engine.renderer.info;
    const c = engine.renderer.domElement;
    return {
      fps: Math.round(1000 / Math.max(1, avg)), avgMs: +avg.toFixed(1), p95Ms: +p95.toFixed(1),
      calls: info.render.calls, triangles: info.render.triangles,
      geometries: info.memory.geometries, textures: info.memory.textures, programs: (info.programs || []).length,
      canvas: `${c.width}x${c.height}`, dpr: +engine.renderer.getPixelRatio().toFixed(2),
      quality: engine.quality.name, gpu, ua: navigator.userAgent,
    };
  };
  const render = () => {
    const s = stats();
    el.innerHTML = `<b>${s.fps} fps</b> &nbsp;avg ${s.avgMs} ms · p95 ${s.p95Ms} ms<br>`
      + `draw calls ${s.calls} · tris ${(s.triangles / 1000).toFixed(0)}k<br>`
      + `canvas ${s.canvas} @${s.dpr} · ${s.quality}<br>`
      + `<span style="opacity:.7">${String(s.gpu).slice(0, 48)}</span>`
      + `<button type="button">Copy perf report</button>`;
    el.querySelector('button').onclick = () => {
      const txt = JSON.stringify(stats(), null, 1);
      (navigator.clipboard ? navigator.clipboard.writeText(txt) : Promise.reject()).then(
        () => { el.querySelector('button').textContent = 'Copied'; },
        () => { window.prompt('Copy this:', txt); });
    };
  };
  engine.onTick(dt => {
    const now = performance.now();
    times.push(now - last); last = now;
    if (times.length > 240) times.shift();
    if (shown && (acc += dt) > 0.5) { acc = 0; render(); }
  });
  window.addEventListener('keydown', e => {
    if (e.key === 'F3' || (e.key === '`' && !e.repeat)) {
      shown = !shown; el.classList.toggle('on', shown); if (shown) render(); e.preventDefault();
    }
  });
  if (/[?&]perf\b/.test(location.search)) { shown = true; el.classList.add('on'); }
  return { stats };
}
