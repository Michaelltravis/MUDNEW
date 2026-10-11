// A progress bar under the hero for timed work (picking a lock, barricading, sealing): the
// server says how long it takes; moving or anything ending the work clears it.
export function createCastbar(root) {
  const fill = root.querySelector('b');
  const label = root.querySelector('span');
  let job = null;
  return {
    start(secs, text) {
      job = { start: performance.now(), ms: Math.max(300, secs * 1000), text };
      label.textContent = text;
      root.style.display = 'block';
    },
    end() { job = null; root.style.display = 'none'; fill.style.width = '0'; },
    get active() { return !!job; },
    update() {
      if (!job) return;
      const k = Math.min(1, (performance.now() - job.start) / job.ms);
      fill.style.width = `${(k * 100).toFixed(1)}%`;
      if (k >= 1 && performance.now() - job.start > job.ms + 1500) this.end();   // the result never came
    },
  };
}
