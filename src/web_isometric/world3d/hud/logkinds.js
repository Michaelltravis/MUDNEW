// The kind of each line the server sends (msgkind.py marks it with an empty <i data-k="combat">,
// web_client.py): the blow-by-blow is drawn on screen, so the log keeps it in its Combat tab and
// out of All unless asked (Settings: Combat text). A kill's reward stays in both.
const MARK = /<i data-k="([a-z]+)"><\/i>/g;

// the lines of a chunk, grouped by kind in order: [{ kind: 'combat' | 'reward' | '', html }]
export function splitByKind(lines) {
  const out = [];
  for (const line of lines) {
    let kind = '';
    const html = String(line).replace(MARK, (_, k) => { kind = kind || k; return ''; });
    const last = out[out.length - 1];
    if (last && last.kind === kind) last.html += `\n${html}`;
    else out.push({ kind, html });
  }
  return out;
}
