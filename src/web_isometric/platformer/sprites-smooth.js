// Misthollow: smooth high-resolution art generator (the clean aesthetic).
// Replaces the pixel-art top-down textures under the SAME td_* keys, drawn
// at 4x supersample with gradients, rounded shapes and soft shadows, then
// displayed scaled down with antialiasing. Still 100% procedural.
(() => {
  const MH = window.MH = window.MH || {};
  const SS = 4;                 // supersample factor
  MH.SMOOTH_SS = SS;
  const TD_FRAMES = ['d0', 'd1', 'u0', 'u1', 's0', 's1', 'atk_d', 'atk_u', 'atk_s', 'hurt', 'death'];
  const FW = 24 * SS, FH = 24 * SS;

  function canvasOf(w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    return [c, ctx];
  }
  function shade(hex, amt) {
    const n = parseInt(hex.slice(1), 16);
    const cl = v => Math.max(0, Math.min(255, v + amt));
    return `#${(((cl((n >> 16) & 255)) << 16) | ((cl((n >> 8) & 255)) << 8) | cl(n & 255)).toString(16).padStart(6, '0')}`;
  }
  function rr(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  function outline(ctx, alpha = 0.45) {
    ctx.strokeStyle = `rgba(12,14,20,${alpha})`;
    ctx.lineWidth = 1.2 * SS;
    ctx.stroke();
  }
  function softShadow(ctx, cx, cy, w, h) {
    const g = ctx.createRadialGradient(cx, cy, 1, cx, cy, w / 2);
    g.addColorStop(0, 'rgba(0,0,0,0.30)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(1, h / w);
    ctx.translate(-cx, -cy);
    ctx.beginPath();
    ctx.arc(cx, cy, w / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // ------------------------- tiles -------------------------
  function genTiles(scene, name, p) {
    const T = 16 * SS;
    {
      // floor: near-flat with a whisper of center sheen (seamless when tiled)
      const [c, ctx] = canvasOf(T, T);
      ctx.fillStyle = p.fillA;
      ctx.fillRect(0, 0, T, T);
      const g = ctx.createRadialGradient(T / 2, T / 2, 2, T / 2, T / 2, T);
      g.addColorStop(0, 'rgba(255,255,255,0.025)');
      g.addColorStop(1, 'rgba(0,0,0,0.02)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, T, T);
      scene.textures.addCanvas(`td_${name}_floor`, c);
    }
    {
      // border block: rounded organic forms per biome family
      const [c, ctx] = canvasOf(T, T);
      const kind = ['forest', 'field', 'swamp'].includes(name) ? 'tree'
        : ['mountain', 'hills', 'cave', 'desert'].includes(name) ? 'rock'
        : ['underwater', 'water_swim', 'water_noswim'].includes(name) ? 'coral'
        : name === 'flying' ? 'cloud' : 'wall';
      ctx.fillStyle = shade(p.fillB, -22);
      ctx.fillRect(0, 0, T, T);
      if (kind === 'tree') {
        softShadow(ctx, T / 2, T * 0.82, T * 0.8, T * 0.3);
        const g = ctx.createRadialGradient(T * 0.38, T * 0.3, 4, T / 2, T / 2, T * 0.62);
        g.addColorStop(0, '#5fae62');
        g.addColorStop(1, '#27572f');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(T / 2, T * 0.46, T * 0.40, 0, Math.PI * 2);
        ctx.fill();
        outline(ctx, 0.35);
        ctx.fillStyle = 'rgba(255,255,255,0.12)';
        ctx.beginPath();
        ctx.arc(T * 0.38, T * 0.32, T * 0.14, 0, Math.PI * 2);
        ctx.fill();
      } else if (kind === 'rock') {
        softShadow(ctx, T / 2, T * 0.84, T * 0.9, T * 0.3);
        const g = ctx.createLinearGradient(0, 0, 0, T);
        g.addColorStop(0, shade(p.top, 26));
        g.addColorStop(1, shade(p.top, -28));
        ctx.fillStyle = g;
        rr(ctx, T * 0.1, T * 0.14, T * 0.8, T * 0.74, T * 0.22);
        ctx.fill();
        outline(ctx, 0.35);
        ctx.fillStyle = 'rgba(255,255,255,0.10)';
        rr(ctx, T * 0.18, T * 0.2, T * 0.34, T * 0.2, T * 0.1);
        ctx.fill();
      } else if (kind === 'coral') {
        const g = ctx.createLinearGradient(0, T, 0, 0);
        g.addColorStop(0, '#b14a72');
        g.addColorStop(1, '#e98aa8');
        ctx.fillStyle = g;
        rr(ctx, T * 0.14, T * 0.2, T * 0.3, T * 0.7, T * 0.15);
        ctx.fill();
        const g2 = ctx.createLinearGradient(0, T, 0, 0);
        g2.addColorStop(0, '#b97a32');
        g2.addColorStop(1, '#eeb066');
        ctx.fillStyle = g2;
        rr(ctx, T * 0.52, T * 0.34, T * 0.3, T * 0.56, T * 0.15);
        ctx.fill();
      } else if (kind === 'cloud') {
        ctx.fillStyle = '#aebad2';
        ctx.fillRect(0, 0, T, T);
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        ctx.beginPath();
        ctx.arc(T * 0.35, T * 0.5, T * 0.3, 0, Math.PI * 2);
        ctx.arc(T * 0.68, T * 0.42, T * 0.24, 0, Math.PI * 2);
        ctx.fill();
      } else {
        const g = ctx.createLinearGradient(0, 0, 0, T);
        g.addColorStop(0, shade(p.wall, 30));
        g.addColorStop(1, shade(p.wall, -18));
        ctx.fillStyle = g;
        rr(ctx, T * 0.05, T * 0.05, T * 0.9, T * 0.9, T * 0.12);
        ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.18)';
        ctx.lineWidth = SS;
        ctx.beginPath();
        ctx.moveTo(T * 0.05, T * 0.5); ctx.lineTo(T * 0.95, T * 0.5);
        ctx.moveTo(T * 0.5, T * 0.05); ctx.lineTo(T * 0.5, T * 0.5);
        ctx.moveTo(T * 0.3, T * 0.5); ctx.lineTo(T * 0.3, T * 0.95);
        ctx.moveTo(T * 0.72, T * 0.5); ctx.lineTo(T * 0.72, T * 0.95);
        ctx.stroke();
      }
      scene.textures.addCanvas(`td_${name}_border`, c);
    }
    for (let i = 0; i < 2; i++) {
      const key = `td_${name}_obst${i}`;
      if (scene.textures.exists(key)) continue;
      const [c, ctx] = canvasOf(T, T);
      softShadow(ctx, T / 2, T * 0.82, T * 0.85, T * 0.3);
      if (i === 0) {
        const g = ctx.createRadialGradient(T * 0.36, T * 0.3, 3, T / 2, T / 2, T * 0.6);
        g.addColorStop(0, shade(p.top, 30));
        g.addColorStop(1, shade(p.top, -30));
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(T * 0.5, T * 0.52, T * 0.36, 0, Math.PI * 2);
        ctx.fill();
        outline(ctx, 0.35);
      } else {
        const g = ctx.createLinearGradient(0, 0, 0, T);
        g.addColorStop(0, shade(p.accent, -22));
        g.addColorStop(1, shade(p.accent, -58));
        ctx.fillStyle = g;
        rr(ctx, T * 0.16, T * 0.16, T * 0.68, T * 0.68, T * 0.14);
        ctx.fill();
        outline(ctx, 0.35);
        ctx.fillStyle = 'rgba(255,255,255,0.10)';
        rr(ctx, T * 0.22, T * 0.22, T * 0.3, T * 0.18, T * 0.08);
        ctx.fill();
      }
      scene.textures.addCanvas(key, c);
    }
  }

  function genUniversal(scene) {
    const T = 16 * SS;
    {
      const [c, ctx] = canvasOf(T, T);
      // stairs up: luminous ascending steps
      ctx.fillStyle = '#181b24';
      rr(ctx, 0, 0, T, T, T * 0.12); ctx.fill();
      ['#4c5260', '#707a8c', '#9aa6ba', '#d5dde9'].forEach((col, i) => {
        ctx.fillStyle = col;
        rr(ctx, T * (0.12 + i * 0.06), T * (0.74 - i * 0.2), T * (0.76 - i * 0.12), T * 0.17, 3 * SS);
        ctx.fill();
      });
      scene.textures.addCanvas('td_stairs_up', c);
    }
    {
      const [c, ctx] = canvasOf(T, T);
      // stairs down: descent into soft darkness
      const g = ctx.createRadialGradient(T / 2, T / 2, 2, T / 2, T / 2, T * 0.7);
      g.addColorStop(0, '#05060a');
      g.addColorStop(1, '#2a2e3a');
      ctx.fillStyle = g;
      rr(ctx, 0, 0, T, T, T * 0.12); ctx.fill();
      ['#3c4250', '#262b36', '#14161e'].forEach((col, i) => {
        ctx.fillStyle = col;
        rr(ctx, T * 0.16, T * (0.14 + i * 0.24), T * 0.68, T * 0.2, 2 * SS);
        ctx.fill();
      });
      scene.textures.addCanvas('td_stairs_down', c);
    }
    {
      // smooth portal: swirling violet oval, 2 frames
      const PW = 28 * SS, PH = 40 * SS;
      const [c, ctx] = canvasOf(PW * 2, PH);
      for (let f = 0; f < 2; f++) {
        const ox = f * PW;
        softShadow(ctx, ox + PW / 2, PH * 0.92, PW * 0.8, PW * 0.25);
        const g = ctx.createRadialGradient(ox + PW / 2, PH * 0.45, 2, ox + PW / 2, PH * 0.45, PW * 0.55);
        g.addColorStop(0, f ? '#e8d4ff' : '#cfaaff');
        g.addColorStop(0.5, '#8a4ad6');
        g.addColorStop(1, 'rgba(60,20,110,0)');
        ctx.fillStyle = g;
        ctx.save();
        ctx.translate(ox + PW / 2, PH * 0.45);
        ctx.scale(0.72, 1);
        ctx.beginPath();
        ctx.arc(0, 0, PW * 0.52, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
        ctx.strokeStyle = f ? 'rgba(235,215,255,0.8)' : 'rgba(200,160,255,0.7)';
        ctx.lineWidth = 2 * SS;
        ctx.save();
        ctx.translate(ox + PW / 2, PH * 0.45);
        ctx.scale(0.72, 1);
        ctx.beginPath();
        ctx.arc(0, 0, PW * 0.42, 0.6 + f, 3.6 + f);
        ctx.stroke();
        ctx.restore();
      }
      const tex = scene.textures.addCanvas('sm_portal', c);
      tex.add('0', 0, 0, 0, PW, PH);
      tex.add('1', 0, PW, 0, PW, PH);
      if (!scene.anims.exists('sm_portal_anim')) {
        scene.anims.create({ key: 'sm_portal_anim', frames: ['0', '1'].map(f => ({ key: 'sm_portal', frame: f })), frameRate: 3, repeat: -1 });
      }
    }
    {
      // smooth gravestone
      const GW = 18 * SS, GH = 22 * SS;
      const [c, ctx] = canvasOf(GW, GH);
      softShadow(ctx, GW / 2, GH * 0.92, GW * 0.9, GW * 0.3);
      const g = ctx.createLinearGradient(0, 0, GW, 0);
      g.addColorStop(0, '#9aa2b2');
      g.addColorStop(1, '#5f6675');
      ctx.fillStyle = g;
      rr(ctx, GW * 0.14, GH * 0.12, GW * 0.72, GH * 0.82, GW * 0.3);
      ctx.fill();
      ctx.strokeStyle = 'rgba(20,22,30,0.55)';
      ctx.lineWidth = 1.5 * SS;
      ctx.beginPath();
      ctx.moveTo(GW / 2, GH * 0.26); ctx.lineTo(GW / 2, GH * 0.56);
      ctx.moveTo(GW * 0.32, GH * 0.36); ctx.lineTo(GW * 0.68, GH * 0.36);
      ctx.stroke();
      scene.textures.addCanvas('sm_grave', c);
    }
    {
      // smooth water, 4 gentle wave frames (tinted per theme in-scene)
      const T2 = 16 * SS;
      const [c, ctx] = canvasOf(T2 * 4, T2);
      for (let f = 0; f < 4; f++) {
        const ox = f * T2;
        const g = ctx.createLinearGradient(0, 0, 0, T2);
        g.addColorStop(0, '#9fc8e8');
        g.addColorStop(1, '#5a85b5');
        ctx.fillStyle = g;
        ctx.fillRect(ox, 0, T2, T2);
        ctx.strokeStyle = 'rgba(255,255,255,0.35)';
        ctx.lineWidth = 1.6 * SS;
        ctx.beginPath();
        for (let x = 0; x <= T2; x += 4 * SS) {
          ctx.lineTo(ox + x, T2 * 0.3 + Math.sin((x / T2) * Math.PI * 2 + f * 1.57) * 2.4 * SS);
        }
        ctx.stroke();
      }
      const tex = scene.textures.addCanvas('sm_water', c);
      for (let f = 0; f < 4; f++) tex.add(String(f), 0, f * T2, 0, T2, T2);
      if (!scene.anims.exists('sm_water_anim')) {
        scene.anims.create({ key: 'sm_water_anim', frames: [0, 1, 2, 3].map(f => ({ key: 'sm_water', frame: String(f) })), frameRate: 3, repeat: -1 });
      }
    }
    // smooth props: bush, lamp, crate (generic, theme-tinted in scene)
    const props = {
      sm_prop_bush: ctx => {
        const T2 = 24 * SS;
        softShadow(ctx, T2 / 2, T2 * 0.85, T2 * 0.8, T2 * 0.25);
        const g = ctx.createRadialGradient(T2 * 0.4, T2 * 0.4, 2, T2 / 2, T2 * 0.55, T2 * 0.5);
        g.addColorStop(0, '#69b56f');
        g.addColorStop(1, '#2c5c36');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(T2 * 0.38, T2 * 0.58, T2 * 0.22, 0, Math.PI * 2);
        ctx.arc(T2 * 0.62, T2 * 0.52, T2 * 0.26, 0, Math.PI * 2);
        ctx.fill();
      },
      sm_prop_lamp: ctx => {
        const T2 = 24 * SS;
        ctx.fillStyle = '#3c4252';
        rr(ctx, T2 * 0.46, T2 * 0.25, T2 * 0.08, T2 * 0.6, 2 * SS);
        ctx.fill();
        const g = ctx.createRadialGradient(T2 / 2, T2 * 0.2, 1, T2 / 2, T2 * 0.2, T2 * 0.22);
        g.addColorStop(0, '#ffeeb0');
        g.addColorStop(1, 'rgba(255,200,80,0)');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(T2 / 2, T2 * 0.2, T2 * 0.22, 0, Math.PI * 2);
        ctx.fill();
      },
      sm_prop_crate: ctx => {
        const T2 = 24 * SS;
        softShadow(ctx, T2 / 2, T2 * 0.85, T2 * 0.75, T2 * 0.22);
        const g = ctx.createLinearGradient(0, 0, 0, T2);
        g.addColorStop(0, '#9a7448');
        g.addColorStop(1, '#5e4226');
        ctx.fillStyle = g;
        rr(ctx, T2 * 0.2, T2 * 0.3, T2 * 0.6, T2 * 0.55, 2 * SS);
        ctx.fill();
        ctx.strokeStyle = 'rgba(40,24,10,0.5)';
        ctx.lineWidth = 1.4 * SS;
        rr(ctx, T2 * 0.2, T2 * 0.3, T2 * 0.6, T2 * 0.55, 2 * SS);
        ctx.stroke();
      },
    };
    for (const [key, draw] of Object.entries(props)) {
      const [c, ctx] = canvasOf(24 * SS, 24 * SS);
      draw(ctx);
      scene.textures.addCanvas(key, c);
    }
    // smooth item orbs by type colour
    const ITEM_COLORS = {
      weapon: '#cdd4e2', armor: '#93a0b5', potion: '#d65a96', scroll: '#dccfa6',
      food: '#c98a4b', drink: '#7a5a36', key: '#e8c168', light: '#ffd060',
      container: '#8a6a40', treasure: '#ffd44a', wand: '#8ad0ff', other: '#9aa0b4',
    };
    for (const [kind, col] of Object.entries(ITEM_COLORS)) {
      const [c, ctx] = canvasOf(16 * SS, 16 * SS);
      const T2 = 16 * SS;
      const g = ctx.createRadialGradient(T2 * 0.38, T2 * 0.34, 1, T2 / 2, T2 / 2, T2 * 0.42);
      g.addColorStop(0, '#ffffff');
      g.addColorStop(0.35, col);
      g.addColorStop(1, shade(col, -70));
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(T2 / 2, T2 / 2, T2 * 0.34, 0, Math.PI * 2);
      ctx.fill();
      scene.textures.addCanvas(`sm_item_${kind}`, c);
    }
  }

  // ------------------------- actors -------------------------
  function drawHumanoid(ctx, ox, frame, pal) {
    const u = SS;
    const cx = ox + 12 * u;
    if (frame === 'death') {
      ctx.fillStyle = pal.outfit;
      rr(ctx, cx - 7 * u, 13 * u, 14 * u, 6 * u, 3 * u); ctx.fill();
      return;
    }
    const step = frame.endsWith('1') ? 1 : 0;
    const facing = frame.startsWith('atk_') ? frame.slice(4) : frame[0];
    softShadow(ctx, cx, 21.5 * u, 13 * u, 4 * u);
    // body capsule with gradient
    const bg = ctx.createLinearGradient(0, 9 * u, 0, 20 * u);
    bg.addColorStop(0, shade(pal.outfit, 24));
    bg.addColorStop(1, shade(pal.outfit, -22));
    ctx.fillStyle = bg;
    rr(ctx, cx - 5.5 * u, 9.5 * u, 11 * u, 10.5 * u, 4.5 * u);
    ctx.fill();
    outline(ctx);
    // feet
    ctx.fillStyle = shade(pal.outfit2, -10);
    if (facing === 's') {
      ctx.beginPath();
      ctx.arc(cx - 2.5 * u + step * u, 20 * u, 1.8 * u, 0, Math.PI * 2);
      ctx.arc(cx + 2.5 * u - step * u, 20 * u, 1.8 * u, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.arc(cx - 3 * u, (20 + step * 0.6) * u, 1.8 * u, 0, Math.PI * 2);
      ctx.arc(cx + 3 * u, (20.6 - step * 0.6) * u, 1.8 * u, 0, Math.PI * 2);
      ctx.fill();
    }
    // head
    const hg = ctx.createRadialGradient(cx - 1.5 * u, 6 * u, u, cx, 7 * u, 5.5 * u);
    hg.addColorStop(0, shade(pal.skin, 22));
    hg.addColorStop(1, shade(pal.skin, -14));
    ctx.fillStyle = hg;
    ctx.beginPath();
    ctx.arc(cx, 7 * u, 4.6 * u, 0, Math.PI * 2);
    ctx.fill();
    outline(ctx);
    // hair / hood arc
    ctx.fillStyle = pal.hair;
    if (facing === 'u') {
      ctx.beginPath(); ctx.arc(cx, 7 * u, 4.6 * u, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.beginPath(); ctx.arc(cx, 6.6 * u, 4.6 * u, Math.PI, Math.PI * 2); ctx.fill();
    }
    // face
    ctx.fillStyle = '#1c1e28';
    if (facing === 'd') {
      ctx.beginPath();
      ctx.arc(cx - 1.7 * u, 7.6 * u, 0.7 * u, 0, Math.PI * 2);
      ctx.arc(cx + 1.7 * u, 7.6 * u, 0.7 * u, 0, Math.PI * 2);
      ctx.fill();
    } else if (facing === 's') {
      ctx.beginPath();
      ctx.arc(cx + 2.2 * u, 7.4 * u, 0.7 * u, 0, Math.PI * 2);
      ctx.fill();
    }
    // belt accent
    ctx.fillStyle = pal.trim;
    rr(ctx, cx - 5.5 * u, 15.5 * u, 11 * u, 1.6 * u, 0.8 * u);
    ctx.fill();
    // weapon thrust
    if (frame.startsWith('atk_')) {
      ctx.strokeStyle = pal.weapon;
      ctx.lineWidth = 1.8 * u;
      ctx.lineCap = 'round';
      ctx.beginPath();
      if (facing === 'd') { ctx.moveTo(cx + 5 * u, 13 * u); ctx.lineTo(cx + 6.5 * u, 22 * u); }
      else if (facing === 'u') { ctx.moveTo(cx - 5 * u, 11 * u); ctx.lineTo(cx - 6.5 * u, 2 * u); }
      else { ctx.moveTo(cx + 5 * u, 12 * u); ctx.lineTo(cx + 11.5 * u, 11 * u); }
      ctx.stroke();
    }
    if (frame === 'hurt') {
      ctx.fillStyle = 'rgba(255,70,70,0.5)';
      rr(ctx, cx - 5.5 * u, 9.5 * u, 11 * u, 10.5 * u, 4.5 * u);
      ctx.fill();
    }
  }
  function drawQuad(ctx, ox, frame, pal) {
    const u = SS;
    const cx = ox + 12 * u, cy = 12 * u;
    if (frame === 'death') {
      ctx.fillStyle = pal.outfit;
      rr(ctx, cx - 8 * u, cy + 3 * u, 16 * u, 5 * u, 2.5 * u); ctx.fill();
      return;
    }
    const facing = frame.startsWith('atk_') ? frame.slice(4) : frame[0];
    const step = frame.endsWith('1') ? 0.8 : 0;
    softShadow(ctx, cx, 20.5 * u, 15 * u, 4.4 * u);
    const bg = ctx.createLinearGradient(0, cy - 6 * u, 0, cy + 8 * u);
    bg.addColorStop(0, shade(pal.outfit, 22));
    bg.addColorStop(1, shade(pal.outfit, -24));
    ctx.fillStyle = bg;
    ctx.save();
    ctx.translate(cx, cy + 2 * u);
    if (facing === 's') ctx.scale(1.45, 0.85);
    else ctx.scale(0.85, 1.45);
    ctx.beginPath();
    ctx.arc(0, 0, 5.6 * u, 0, Math.PI * 2);
    ctx.fill();
    outline(ctx);
    ctx.restore();
    // head
    ctx.fillStyle = shade(pal.outfit, 8);
    const hx = facing === 's' ? cx + 7.5 * u : cx;
    const hy = facing === 's' ? cy : (facing === 'd' ? cy + 9 * u : cy - 7 * u);
    ctx.beginPath();
    ctx.arc(hx, hy + (facing === 's' ? -2 * u : 0), 3.2 * u, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#15171f';
    if (facing !== 'u') {
      ctx.beginPath();
      ctx.arc(hx + (facing === 's' ? 1.2 * u : -1.2 * u), hy - (facing === 's' ? 2.4 : -0.6) * u, 0.6 * u, 0, Math.PI * 2);
      if (facing === 'd') ctx.arc(hx + 1.2 * u, hy + 0.6 * u, 0.6 * u, 0, Math.PI * 2);
      ctx.fill();
    }
    // paws
    ctx.fillStyle = shade(pal.outfit2, -8);
    ctx.beginPath();
    ctx.arc(cx - 4 * u + step * u, 19.4 * u, 1.6 * u, 0, Math.PI * 2);
    ctx.arc(cx + 4 * u - step * u, 19.4 * u, 1.6 * u, 0, Math.PI * 2);
    ctx.fill();
    if (frame === 'hurt') {
      ctx.fillStyle = 'rgba(255,70,70,0.45)';
      ctx.beginPath(); ctx.arc(cx, cy + 2 * u, 7 * u, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawBlob(ctx, ox, frame, pal) {
    const u = SS;
    const cx = ox + 12 * u, cy = 13 * u;
    if (frame === 'death') {
      ctx.fillStyle = pal.outfit;
      rr(ctx, cx - 6 * u, cy + 4 * u, 12 * u, 3 * u, 1.5 * u); ctx.fill();
      return;
    }
    const squish = frame.endsWith('1') ? 0.92 : 1;
    softShadow(ctx, cx, 20.5 * u, 13 * u, 4 * u);
    const g = ctx.createRadialGradient(cx - 2 * u, cy - 3 * u, u, cx, cy, 8 * u);
    g.addColorStop(0, shade(pal.outfit, 40));
    g.addColorStop(1, shade(pal.outfit, -26));
    ctx.fillStyle = g;
    ctx.save();
    ctx.translate(cx, cy + (1 - squish) * 6 * u);
    ctx.scale(1 / squish * 0.95, squish);
    ctx.beginPath();
    ctx.arc(0, 0, 6.4 * u, 0, Math.PI * 2);
    ctx.fill();
    outline(ctx);
    ctx.restore();
    ctx.fillStyle = '#15171f';
    ctx.beginPath();
    ctx.arc(cx - 2 * u, cy - u, 0.9 * u, 0, Math.PI * 2);
    ctx.arc(cx + 2 * u, cy - u, 0.9 * u, 0, Math.PI * 2);
    ctx.fill();
    if (frame === 'hurt') {
      ctx.fillStyle = 'rgba(255,70,70,0.45)';
      ctx.beginPath(); ctx.arc(cx, cy, 6.4 * u, 0, Math.PI * 2); ctx.fill();
    }
  }
  function drawFlyer(ctx, ox, frame, pal) {
    const u = SS;
    const cx = ox + 12 * u, cy = 11 * u;
    if (frame === 'death') {
      ctx.fillStyle = pal.outfit;
      rr(ctx, cx - 5 * u, cy + 6 * u, 10 * u, 3 * u, 1.5 * u); ctx.fill();
      return;
    }
    const flap = frame.endsWith('1') ? -3 : 1.5;
    softShadow(ctx, cx, 20 * u, 11 * u, 3.4 * u);
    ctx.fillStyle = shade(pal.outfit2, 6);
    [[-1, 0], [1, 0]].forEach(([sx]) => {
      ctx.save();
      ctx.translate(cx + sx * 5 * u, cy + flap * u * 0.6);
      ctx.rotate(sx * (0.5 + flap * 0.07));
      ctx.beginPath();
      ctx.ellipse(sx * 3 * u, 0, 5.5 * u, 2.4 * u, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });
    const g = ctx.createRadialGradient(cx - u, cy - 2 * u, u, cx, cy, 6 * u);
    g.addColorStop(0, shade(pal.outfit, 30));
    g.addColorStop(1, shade(pal.outfit, -24));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(cx, cy, 4 * u, 5.6 * u, 0, 0, Math.PI * 2);
    ctx.fill();
    outline(ctx);
    ctx.fillStyle = '#15171f';
    ctx.beginPath();
    ctx.arc(cx - 1.4 * u, cy - 2 * u, 0.7 * u, 0, Math.PI * 2);
    ctx.arc(cx + 1.4 * u, cy - 2 * u, 0.7 * u, 0, Math.PI * 2);
    ctx.fill();
    if (frame === 'hurt') {
      ctx.fillStyle = 'rgba(255,70,70,0.45)';
      ctx.beginPath(); ctx.ellipse(cx, cy, 4.4 * u, 6 * u, 0, 0, Math.PI * 2); ctx.fill();
    }
  }
  function accessory(ctx, ox, frame, kind, pal) {
    if (frame === 'death') return;
    const u = SS;
    const cx = ox + 12 * u;
    ctx.lineCap = 'round';
    switch (kind) {
      case 'helm': {
        const g = ctx.createLinearGradient(0, 2 * u, 0, 6 * u);
        g.addColorStop(0, '#cdd4e2'); g.addColorStop(1, '#7d8696');
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(cx, 6.4 * u, 4.8 * u, Math.PI, Math.PI * 2); ctx.fill();
        break;
      }
      case 'wizardhat':
        ctx.fillStyle = pal.trim;
        ctx.beginPath();
        ctx.moveTo(cx - 6 * u, 5.5 * u); ctx.lineTo(cx + 6 * u, 5.5 * u); ctx.lineTo(cx + 1.5 * u, -0.5 * u);
        ctx.closePath(); ctx.fill();
        break;
      case 'hood':
        ctx.fillStyle = shade(pal.outfit, -24);
        ctx.beginPath(); ctx.arc(cx, 6.8 * u, 5 * u, Math.PI * 0.95, Math.PI * 2.05); ctx.fill();
        break;
      case 'circlet':
        ctx.strokeStyle = '#e8c168';
        ctx.lineWidth = u;
        ctx.beginPath(); ctx.arc(cx, 6.6 * u, 4.4 * u, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
        break;
      case 'apron':
        ctx.fillStyle = 'rgba(238,232,218,0.9)';
        rr(ctx, cx - 3 * u, 12 * u, 6 * u, 6.5 * u, 2 * u); ctx.fill();
        break;
      case 'shield': {
        const g = ctx.createLinearGradient(0, 11 * u, 0, 18 * u);
        g.addColorStop(0, '#9aa6ba'); g.addColorStop(1, '#5f6878');
        ctx.fillStyle = g;
        rr(ctx, cx - 9.5 * u, 11 * u, 4.5 * u, 7 * u, 2 * u); ctx.fill();
        break;
      }
      default: break;
    }
  }

  function genActor(scene, key, body, pal, accs, alpha) {
    if (scene.textures.exists(key)) return;
    const [c, ctx] = canvasOf(FW * TD_FRAMES.length, FH);
    if (alpha) ctx.globalAlpha = alpha;
    TD_FRAMES.forEach((frame, i) => {
      const ox = i * FW;
      if (body === 'quad') drawQuad(ctx, ox, frame, pal);
      else if (body === 'blob') drawBlob(ctx, ox, frame, pal);
      else if (body === 'flyer') drawFlyer(ctx, ox, frame, pal);
      else { drawHumanoid(ctx, ox, frame, pal); (accs || []).forEach(a => accessory(ctx, ox, frame, a, pal)); }
    });
    const tex = scene.textures.addCanvas(key, c);
    TD_FRAMES.forEach((frame, i) => tex.add(frame, 0, i * FW, 0, FW, FH));
  }

  MH.smoothSprites = {
    generateAll(scene) {
      for (const [name, p] of Object.entries(MH.THEMES)) genTiles(scene, name, p);
      genUniversal(scene);
      for (const [cls, look] of Object.entries(MH.sprites.CLASS_LOOKS)) {
        genActor(scene, `td_player_${cls}`, 'human', look.pal, look.acc);
      }
      for (const rule of MH.sprites.MOB_RULES) {
        const pal = Object.assign({ skin: '#d8a878', hair: '#5a4a32', weapon: '#cdd4e2' }, rule.pal);
        genActor(scene, `td_mob_${rule.key}`, rule.body, pal, rule.acc, rule.alpha);
      }
      MH.tdSprites.registerAnims(scene);
    },
    itemKey(type) {
      const t = String(type || 'other').toLowerCase();
      const known = ['weapon', 'armor', 'potion', 'scroll', 'food', 'drink', 'key', 'light', 'container', 'treasure', 'wand'];
      return `sm_item_${known.includes(t) ? t : 'other'}`;
    },
  };
})();
