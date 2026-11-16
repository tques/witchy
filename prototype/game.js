// Witch RPG prototype: sprite-stacked characters and rooms, fixed cameras, click-to-move.
// World units are cubes. x = east, z = south, height up. Heading 0 = facing south (+z).
function startGame(DATA) {
'use strict';
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const VW = cv.width, VH = cv.height, CX = VW / 2, CY = VH * 0.56;
const $ = id => document.getElementById(id);
ctx.imageSmoothingEnabled = false;
const A = {};                       // assets: {W,H,D,n,img,layers[frame] = non-empty layer rows}
const deg = Math.PI / 180;

// ------------------------------------------------------------------ loading
function loadAssets() {
  return Promise.all(Object.entries(DATA.assets).map(([name, a]) => new Promise(res => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
      const g = c.getContext('2d'); g.drawImage(img, 0, 0);
      const px = g.getImageData(0, 0, img.width, img.height).data;
      const layers = [];
      for (let f = 0; f < a.n; f++) {
        const rows = [];
        for (let y = 0; y < a.H; y++) {
          let any = false;
          for (let zz = 0; zz < a.D && !any; zz++) {
            const row = (y * a.D + zz) * img.width;
            for (let xx = 0; xx < a.W; xx++) if (px[(row + f * a.W + xx) * 4 + 3]) { any = true; break; }
          }
          if (any) rows.push(y);
        }
        layers.push(rows);
      }
      A[name] = Object.assign({}, a, { img: c, layers });
      res();
    };
    img.src = a.src;
  })));
}

// ------------------------------------------------------------------ state
const S = {
  roomId: null, room: null, cam: null, floor: null, grid: null, objects: [], npcs: [],
  player: { x: 0, z: 0, heading: 0, anim: 'stand', phase: 0, path: [], run: false, onArrive: null, busy: false },
  flags: { note: false, spark: false, fairy: false, crystal: false, potionFound: false },
  mana: 30, maxMana: 30, potions: 0, dialog: [], hover: null, fx: [], time: 0, fade: 0,
};
const P = S.player;

// ------------------------------------------------------------------ camera / projection
// A camera is its settings (rooms.py: zone, yaw, tilt, zoom, target, follow) plus a live POSE
// {yaw, tilt, S, tx, tz} that updateCamera() advances every frame. Everything that draws or picks reads the pose.
// Modes:
//   fixed   the pose is the settings: a composed shot (interiors, set pieces)
//   follow  the pose slides after the player; the angle never changes, so cached stack images stay valid
// A later 'turn' mode would ease pose.yaw as well. Only updateCamera() needs to change; proj/unproj, the floor and
// the dead zone already work at any angle. Stack images are cached per (yaw, tilt, zoom), so a turning camera should
// round pose.yaw (e.g. to 3 degrees) before drawing and keep the cache bounded.
const VIEW_SCALE = 1.5;                 // on-screen size: 1.5x the original 960x600 framing, for a 1920x1080 canvas
const FOLLOW = { dead: [0.16, 0.14], ease: 5 };   // dead zone (fraction of the screen), how quickly it catches up
const OUT_OF_BOUNDS = 0.7;               // ground outside the current room (neighbours' too) is drawn this much darker
const GROUND_MARGIN = 560;              // outdoor ground (and neighbours' scenery) painted this far past the edges: enough to fill
                                        // the screen when a following camera reaches a corner
function setCamera(c) {
  const f = c.follow ? (c.follow === true ? {} : c.follow) : null;
  S.cam = { src: c, mode: f ? 'follow' : 'fixed', follow: f, yaw: c.yaw, tilt: c.tilt, S: c.zoom * VIEW_SCALE, tx: c.target[0], tz: c.target[1] };
  if (f) [S.cam.tx, S.cam.tz] = followGoal(true);        // a cut lands centred on her
  posePrep();
}
function posePrep() {                                    // trig + a whole-pixel screen offset for the current pose
  const k = S.cam;
  k.c = Math.cos(k.yaw * deg); k.s = Math.sin(k.yaw * deg); k.sn = Math.sin(k.tilt * deg); k.cs = Math.cos(k.tilt * deg);
  k.ox = Math.round(k.S * (k.tx * k.c - k.tz * k.s));             // snapping keeps pixel art from shimmering as it slides
  k.oy = Math.round(k.S * (k.tx * k.s + k.tz * k.c) * k.sn);
}
function proj(x, z, h = 0) {
  const k = S.cam, xr = x * k.c - z * k.s, zr = x * k.s + z * k.c;
  return [CX + k.S * xr - k.ox, CY + k.S * zr * k.sn - k.oy - h * k.S * k.cs, zr];
}
function unproj(X, Y) {
  const k = S.cam, xr = (X - CX + k.ox) / k.S, zr = (Y - CY + k.oy) / (k.S * k.sn);
  return [xr * k.c + zr * k.s, -xr * k.s + zr * k.c];
}
function followGoal(instant) {
  // where the camera centre wants to be: wherever keeps the player inside the dead zone (measured on screen, so
  // it holds at any yaw), limited to the camera's bounds (the room by default)
  const k = S.cam, f = k.follow || {};
  let gx = P.x, gz = P.z;
  if (!instant) {
    const dx = P.x - k.tx, dz = P.z - k.tz;
    const sx = k.S * (dx * k.c - dz * k.s), sy = k.S * (dx * k.s + dz * k.c) * k.sn;     // player offset on screen
    const [fx, fy] = f.dead || FOLLOW.dead, hx = VW * fx, hy = VH * fy;
    const ex = sx - Math.max(-hx, Math.min(hx, sx)), ey = sy - Math.max(-hy, Math.min(hy, sy));
    const xr = ex / k.S, zr = ey / (k.S * k.sn);                                          // back to the ground
    gx = k.tx + xr * k.c + zr * k.s; gz = k.tz - xr * k.s + zr * k.c;
  }
  const [x0, z0, x1, z1] = f.bounds || [0, 0, S.room.size[0], S.room.size[1]];
  return [Math.max(x0, Math.min(x1, gx)), Math.max(z0, Math.min(z1, gz))];
}
function updateCamera(dt) {
  const k = S.cam;
  if (k.mode === 'follow') {
    const [gx, gz] = followGoal(false), t = 1 - Math.exp(-dt * ((k.follow && k.follow.ease) || FOLLOW.ease));
    k.tx += (gx - k.tx) * t; k.tz += (gz - k.tz) * t;
  }
  posePrep();
}
function pickCamera() {
  const cams = S.room.cameras;
  const c = cams.find(c => c.zone && P.x >= c.zone[0] && P.x < c.zone[2] && P.z >= c.zone[1] && P.z < c.zone[3]) || cams.find(c => !c.zone) || cams[0];
  if (!S.cam || S.cam.src !== c) setCamera(c);           // crossing into another zone cuts to its camera
}

// ------------------------------------------------------------------ floor painting (one texel per cube)
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
function groundColor(style, wx, wz, K, jit) {             // one texel of a room's ground, in that room's own coordinates
  const bx = Math.floor(wx / K), bz = Math.floor(wz / K);
  if (style === 'wood') {
    const plank = Math.floor(bz / 8), seam = (((wz % (8 * K)) + 8 * K) % (8 * K)) < 1.5 || ((bx + plank * 23) % 40 === 0 && wx % K < 1.5);
    return seam ? [92, 62, 44] : jit([[150, 104, 70], [140, 96, 64], [158, 112, 76]][((plank % 3) + 3) % 3], 10);
  }
  if (style === 'grass') return jit((((bx * 7 + bz * 13) ^ (bx * bz)) & 31) < 2 ? [120, 180, 96] : [96, 158, 84], 14);
  if (style === 'meadow') {
    const h = Math.imul(bx * 73856093 ^ bz * 19349663, 2654435761) >>> 24;               // scattered, no visible pattern
    return h < 3 ? [240, 236, 220] : h < 5 ? [236, 200, 90] : jit(h < 40 ? [128, 188, 100] : [112, 176, 92], 14);   // daisies and buttercups
  }
  return jit((((bx * 5 + bz * 11) ^ (bx * bz)) & 31) < 2 ? [92, 140, 84] : [70, 118, 74], 14);
}
function paintDecals(room, ox, oz, set, jit, K, r) {     // rugs, paths, clearings; (ox, oz) places a neighbour's decals
  for (const dc of room.floor.decals || []) {
    if (dc.kind === 'rug') {
      const [x0, z0, x1, z1] = dc.rect;
      for (let z = z0; z < z1; z++) for (let x = x0; x < x1; x++) {
        const e = Math.min(x - x0, x1 - 1 - x, z - z0, z1 - 1 - z);
        set(x + ox, z + oz, e < 2 * K ? [200, 160, 70] : e < 4 * K ? [110, 60, 130] : ((Math.floor(x / K) + Math.floor(z / K)) % 8 < 1 ? [150, 100, 170] : jit([130, 80, 150], 8)));
      }
    } else if (dc.kind === 'path') {
      const pts = dc.points, w = dc.width / 2;
      for (let i = 0; i < pts.length - 1; i++) {
        const [ax, az] = pts[i], [bx, bz] = pts[i + 1], len = Math.hypot(bx - ax, bz - az);
        for (let t = 0; t <= len; t += 1) {
          const px = ax + (bx - ax) * t / len, pz = az + (bz - az) * t / len;
          for (let oz2 = -w; oz2 <= w; oz2++) for (let ox2 = -w; ox2 <= w; ox2++) if (ox2 * ox2 + oz2 * oz2 <= w * w) {
            const x = Math.round(px + ox2), z = Math.round(pz + oz2);
            const stone = ((Math.floor(x / (6 * K)) * 31 + Math.floor(z / (5 * K)) * 17) % 5 + 5) % 5;
            const gap = ((x % (6 * K)) + 6 * K) % (6 * K) < 1.5 || ((z % (5 * K)) + 5 * K) % (5 * K) < 1.5;
            set(x + ox, z + oz, gap ? [118, 104, 90] : jit([[168, 160, 150], [156, 150, 144], [176, 166, 152], [150, 144, 140], [162, 152, 140]][stone], 6));
          }
        }
      }
    } else if (dc.kind === 'clearing') {
      const [cx0, cz0] = dc.center;
      for (let z = cz0 - dc.radius; z <= cz0 + dc.radius; z++) for (let x = cx0 - dc.radius; x <= cx0 + dc.radius; x++) {
        const q = Math.hypot(x - cx0, (z - cz0) * 1.15) / dc.radius + (r() - 0.5) * 0.12;
        if (q < 1) set(x + ox, z + oz, q < 0.8 ? jit([132, 110, 80], 10) : jit([110, 120, 78], 10));
      }
    }
  }
}
function paintFloor(room) {
  const [W, D] = room.size, outdoor = room.floor.style !== 'wood', M = outdoor ? GROUND_MARGIN : 0, K = room.floor.scale || 1;
  const c = document.createElement('canvas'); c.width = W + 2 * M; c.height = D + 2 * M;
  const g = c.getContext('2d'), img = g.createImageData(c.width, c.height), d = img.data, r = rng(7);
  const set = (x, y, col) => {
    const wx = Math.round(x), wz = Math.round(y);
    x = wx + M; y = wz + M; if (x < 0 || y < 0 || x >= c.width || y >= c.height) return;
    const k = wx < 0 || wz < 0 || wx >= W || wz >= D ? OUT_OF_BOUNDS : 1;        // anything you can't walk on here is darker
    const i = (y * c.width + x) * 4; d[i] = col[0] * k; d[i + 1] = col[1] * k; d[i + 2] = col[2] * k; d[i + 3] = 255;
  };
  const jit = (col, a) => { const k = (r() - 0.5) * a; return col.map(v => Math.max(0, Math.min(255, v + k))); };
  const nbs = (room.neighbors || []).map(n => ({ ...n, room: DATA.rooms[n.id] }));
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
    const wx = x - M, wz = y - M;
    let col;
    if (wx >= 0 && wz >= 0 && wx < W && wz < D) col = groundColor(room.floor.style, wx, wz, K, jit);
    else {
      const nb = nbs.find(n => wx >= n.off[0] && wz >= n.off[1] && wx < n.off[0] + n.room.size[0] && wz < n.off[1] + n.room.size[1]);
      if (nb) col = groundColor(nb.room.floor.style, wx - nb.off[0], wz - nb.off[1], K, jit);      // the neighbouring room's own ground
      else col = groundColor(room.floor.style, wx, wz, K, jit);
    }
    set(wx, wz, col);
  }
  for (const nb of nbs) paintDecals(nb.room, nb.off[0], nb.off[1], set, jit, K, r);
  paintDecals(room, 0, 0, set, jit, K, r);
  g.putImageData(img, 0, 0);
  return { canvas: c, M };
}
function drawFloor() {
  const k = S.cam, f = S.floor, [X, Y] = proj(-f.M, -f.M, 0);
  ctx.setTransform(k.S * k.c, k.S * k.s * k.sn, -k.S * k.s, k.S * k.c * k.sn, X, Y);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(f.canvas, 0, 0);
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

// ------------------------------------------------------------------ sprite stacks
const CACHE = new Map();                 // rendered stacks: one image per asset/frame/facing/camera
function stackImage(name, f, heading) {
  const a = A[name], k = S.cam, hq = Math.round(heading / 2) * 2;      // facings to the nearest 2 degrees
  const key = `${name}|${f}|${hq}|${k.yaw}|${k.tilt}|${k.S}`;
  let c = CACHE.get(key);
  if (c) return c;
  const rot = (k.yaw + hq) * deg, co = Math.cos(rot), si = Math.sin(rot), sc = k.S;
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (const cx of [-a.W / 2, a.W / 2]) for (const cz of [-a.D / 2, a.D / 2]) {
    const xr = cx * co - cz * si, zr = cx * si + cz * co;
    x0 = Math.min(x0, xr * sc); x1 = Math.max(x1, xr * sc);
    y0 = Math.min(y0, zr * sc * k.sn - a.H * sc * k.cs); y1 = Math.max(y1, zr * sc * k.sn);
  }
  const ox = Math.ceil(-x0) + 2, oy = Math.ceil(-y0) + 2;
  const cv2 = document.createElement('canvas'); cv2.width = Math.ceil(x1 - x0) + 4; cv2.height = Math.ceil(y1 - y0) + 4;
  const g = cv2.getContext('2d', { willReadFrequently: true }); g.imageSmoothingEnabled = false;
  const n = Math.max(1, Math.ceil(sc * k.cs)), step = sc * k.cs / n, rows = a.layers[f];
  for (let i = rows.length - 1; i >= 0; i--) {
    const y = rows[i], by = oy - (a.H - 1 - y) * sc * k.cs;
    for (let j = 0; j < n; j++) {
      g.setTransform(sc * co, sc * si * k.sn, -sc * si, sc * co * k.sn, ox, by - j * step);
      g.drawImage(a.img, f * a.W, y * a.D, a.W, a.D, -a.W / 2, -a.D / 2, a.W, a.D);
    }
  }
  c = { canvas: cv2, ox, oy };
  CACHE.set(key, c);
  if (CACHE.size > 700) CACHE.delete(CACHE.keys().next().value);       // drop the oldest
  return c;
}
function stackBox(name, frame, x, z, heading, lift = 0) {      // screen rectangle a stack will cover
  const a = A[name], k = S.cam, c = stackImage(name, frame % a.n, heading), [X, Y] = proj(x, z, 0);
  const ix = Math.round(X - c.ox), iy = Math.round(Y - c.oy - lift * k.S * k.cs);
  return [ix, iy, ix + c.canvas.width, iy + c.canvas.height];
}
function drawStack(name, frame, x, z, heading, lift = 0) {
  const a = A[name], k = S.cam, f = frame % a.n, c = stackImage(name, f, heading);
  const [X, Y] = proj(x, z, 0), up = lift * k.S * k.cs;
  const ix = Math.round(X - c.ox), iy = Math.round(Y - c.oy - up);
  ctx.drawImage(c.canvas, ix, iy);
  return { box: [ix, iy, ix + c.canvas.width, iy + c.canvas.height], canvas: c.canvas, ix, iy };   // for pixel hit tests
}
function shadow(x, z, r, alpha = 0.35) {
  const [X, Y] = proj(x, z, 0), k = S.cam;
  ctx.fillStyle = `rgba(8,6,16,${alpha})`;
  ctx.beginPath(); ctx.ellipse(X, Y, r * k.S, r * k.S * k.sn, 0, 0, 7); ctx.fill();
}

// ------------------------------------------------------------------ walk grid + A*
const CELL = 8;
function buildGrid(room) {
  const [W, D] = room.size, gw = Math.ceil(W / CELL), gd = Math.ceil(D / CELL), g = new Uint8Array(gw * gd);
  const pad = 12;
  for (let j = 0; j < gd; j++) for (let i = 0; i < gw; i++) {
    const x = (i + 0.5) * CELL, z = (j + 0.5) * CELL;
    let b = x < 14 || z < 14 || x > W - 14 || z > D - 14;
    for (const o of S.objects) if (o.block && !o.gone && Math.abs(x - o.pos[0]) < o.block[0] + pad && Math.abs(z - o.pos[1]) < o.block[1] + pad) b = true;
    for (const npc of S.npcs) if (!npc.wander && Math.hypot(x - npc.x, z - npc.z) < 22) b = true;
    for (const e of room.exits) if (x >= e.rect[0] - 4 && x <= e.rect[2] + 4 && z >= e.rect[1] - 4 && z <= e.rect[3] + 20) b = false;
    g[j * gw + i] = b ? 1 : 0;
  }
  return { gw, gd, g };
}
function cellOf(x, z) { return [Math.floor(x / CELL), Math.floor(z / CELL)]; }
function free(i, j) { const G = S.grid; return i >= 0 && j >= 0 && i < G.gw && j < G.gd && !G.g[j * G.gw + i]; }
function nearestFree(i, j) {
  if (free(i, j)) return [i, j];
  for (let r = 1; r < 60; r++) for (let dj = -r; dj <= r; dj++) for (let di = -r; di <= r; di++)
    if (Math.max(Math.abs(di), Math.abs(dj)) === r && free(i + di, j + dj)) return [i + di, j + dj];
  return null;
}
function lineFree(x0, z0, x1, z1) {
  const n = Math.ceil(Math.hypot(x1 - x0, z1 - z0) / 1.5);
  for (let t = 0; t <= n; t++) { const [i, j] = cellOf(x0 + (x1 - x0) * t / n, z0 + (z1 - z0) * t / n); if (!free(i, j)) return false; }
  return true;
}
function findPath(x0, z0, x1, z1) {
  const G = S.grid, s = nearestFree(...cellOf(x0, z0)), e = nearestFree(...cellOf(x1, z1));
  if (!s || !e) return null;
  const key = (i, j) => j * G.gw + i, open = [[0, s[0], s[1]]], came = new Map(), cost = new Map([[key(...s), 0]]);
  while (open.length) {
    open.sort((a, b) => a[0] - b[0]);
    const [, i, j] = open.shift();
    if (i === e[0] && j === e[1]) break;
    for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const ni = i + di, nj = j + dj;
      if (!free(ni, nj) || (di && dj && (!free(i + di, j) || !free(i, j + dj)))) continue;
      const nc = cost.get(key(i, j)) + Math.hypot(di, dj);
      if (nc < (cost.get(key(ni, nj)) ?? Infinity)) {
        cost.set(key(ni, nj), nc); came.set(key(ni, nj), [i, j]);
        open.push([nc + Math.hypot(e[0] - ni, e[1] - nj), ni, nj]);
      }
    }
  }
  if (!came.has(key(...e)) && (s[0] !== e[0] || s[1] !== e[1])) return null;
  const cells = []; let c = e;
  while (c) { cells.unshift(c); c = came.get(key(...c)); }
  let pts = cells.map(([i, j]) => [(i + 0.5) * CELL, (j + 0.5) * CELL]);
  const end = free(...cellOf(x1, z1)) ? [x1, z1] : pts[pts.length - 1];
  pts[pts.length - 1] = end;
  const out = [[x0, z0]];                                     // string-pull for smooth, direct paths
  for (let k = 1; k < pts.length; k++) if (!lineFree(...out[out.length - 1], ...pts[k])) out.push(pts[k - 1]);
  out.push(end);
  return out.slice(1);
}

// ------------------------------------------------------------------ rooms
function enterRoom(id, spawn, face) {
  const room = DATA.rooms[id];
  S.roomId = id; S.room = room; S.cam = null;
  S.objects = room.objects.map(o => Object.assign({}, o, { gone: id === 'forest' && o.asset === 'thorns' && S.flags.crystal }));
  for (const o of S.objects) if (o.swap && S.flags.crystal) o.asset = o.swap;
  S.npcs = (room.npcs || []).map(n => ({ ...n, x: n.pos[0], z: n.pos[1], heading: n.face, home: [...n.pos], anim: 'stand', phase: 0, path: [], wait: 1 + Math.random() * 2 }));
  S.context = [];                                         // neighbours' fences, walls and props, seen past the edges
  for (const nb of room.neighbors || []) {
    const other = DATA.rooms[nb.id], M = GROUND_MARGIN, [W, D] = room.size;
    for (const o of other.objects) {
      const x = o.pos[0] + nb.off[0], z = o.pos[1] + nb.off[1];
      if (x < -M || z < -M || x > W + M || z > D + M) continue;          // only what's near enough to see
      if (other.id === 'forest' && o.asset === 'thorns' && S.flags.crystal) continue;
      S.context.push({ asset: o.swap && S.flags.crystal && nb.id === 'forest' ? o.swap : o.asset, pos: [x, z], block: o.block, wall: o.wall });
    }
  }
  S.floor = paintFloor(room);
  S.grid = buildGrid(room);
  P.x = spawn[0]; P.z = spawn[1]; P.heading = face; P.path = []; P.anim = 'stand'; P.onArrive = null;
  pickCamera();
  $('room').textContent = room.name;
  updateQuest();
}
function changeRoom(exit) {
  if (S.fading) return;
  S.fading = true; P.path = []; $('fade').style.opacity = 1;
  setTimeout(() => { enterRoom(exit.to, exit.spawn, exit.face); $('fade').style.opacity = 0; setTimeout(() => S.fading = false, 250); }, 260);
}

// ------------------------------------------------------------------ dialogue / quest
function say(lines, then) { S.dialog = lines.map(l => Array.isArray(l) ? l : ['', l]); S.afterDialog = then; showLine(); }
function showLine() {
  const d = $('dialog');
  if (!S.dialog.length) { d.style.display = 'none'; const t = S.afterDialog; S.afterDialog = null; if (t) t(); return; }
  const [who, text] = S.dialog[0];
  $('who').textContent = who; $('text').textContent = text; d.style.display = 'block';
}
function advance() { if (S.dialog.length) { S.dialog.shift(); showLine(); } }
function updateQuest() {
  const f = S.flags;
  $('obj').textContent = !f.note ? 'Read the note on the table' : !f.spark ? 'Find a spell in your bookshelf'
    : !f.fairy ? 'Find the fairy in the forest, east of the garden' : !f.crystal ? 'Rekindle the dark crystal with Spark'
    : 'Done! Thanks for playing the prototype.';
  $('spell').className = f.spark ? 'on' : '';
  $('spell').textContent = f.spark ? '✦ Spark (10)' : 'No spell';
  $('potion').textContent = `Potion ×${S.potions}`; $('potion').disabled = !S.potions || S.mana >= S.maxMana;
  $('mana').style.width = (100 * S.mana / S.maxMana) + '%';
}
$('potion').onclick = e => { e.stopPropagation(); if (S.potions && S.mana < S.maxMana) { S.potions--; S.mana = S.maxMana; burst(P.x, P.z, 40, [140, 200, 255]); updateQuest(); } };
const ME = 'Witch', FAIRY = 'Fairy';
function interact(id, obj) {
  const f = S.flags;
  switch (id) {
    case 'table': f.note = true; say([[ME, 'A note, in tiny glittering handwriting:'], ['Note', '"The heart crystal in the forest has gone dark. Please come! — F."'], [ME, 'A spark would wake it. My grimoire should have one.']], updateQuest); break;
    case 'bookshelf':
      if (!f.spark) { f.spark = true; say([[ME, 'Grimoire of Small Wonders... here it is.'], ['', '✦ You learned SPARK. Click a glowing target to cast it (10 mana).']], updateQuest); }
      else say([[ME, 'Recipes for moonlight jam and thunder tea. Later.']]); break;
    case 'cauldron': say([[ME, 'The brew bubbles happily. It smells of mint and thunder.']]); break;
    case 'bed': say([[ME, 'No napping now. There is magic to do.']]); break;
    case 'chest':
      if (!f.potionFound) { f.potionFound = true; S.potions++; say([[ME, 'Spare socks, a lucky acorn... and a mana potion!'], ['', 'Click the Potion button to drink it when you need mana.']], updateQuest); }
      else say([[ME, 'Just socks now.']]); break;
    case 'well': say([['Well', '...seek... the fairy... past the eastern gate...'], [ME, 'Thank you, well.']]); break;
    case 'sign': say([['Sign', '→ Whispering Forest']]); break;
    case 'stump': say([['', 'A hollow tree stump']]); break;
    case 'pond': say([[ME, 'Lily pads drift on the still water. A frog is pretending not to see me.']]); break;
    case 'wizard': {
      const done = () => { obj.hold = false; obj.wait = 1.5; };
      if (!f.metWizard) {
        f.metWizard = true;
        say([['Wizard', 'Hmm? Oh! Hello, hello. You haven\'t seen my Looking Glass, have you?'],
             ['Wizard', 'Round, brass, terribly important. I had it a moment ago... or was that Tuesday?'],
             [ME, 'I\'ll keep an eye out for it.'],
             ['Wizard', 'Splendid, splendid. Now, where was I going...']], done);
      } else {
        const lines = ['Looking Glass, Looking Glass... it must be around here somewhere.',
                       'Did I check behind the flowers? I\'m sure I checked behind the flowers.',
                       'Without my Looking Glass, everything looks rather... unlooked.',
                       'Oh, hello again! Any luck? No? Hmm.'];
        say([['Wizard', lines[(S.wizardLine = ((S.wizardLine ?? -1) + 1) % lines.length)]]], done);
      }
      break;
    }
    case 'fairy':
      if (!f.crystal) {
        f.fairy = true;
        say([[FAIRY, 'Oh! You came! You must be the witch from the cottage.'], [FAIRY, 'The heart crystal went dark, and thorns grew over the old path.'],
             [FAIRY, f.spark ? 'Could you rekindle it with your Spark? Just click the crystal!' : 'Do you know any spark spells? Maybe in your books at home?']], updateQuest);
      } else say([[FAIRY, 'It glows again! The thorns are gone and the old path is open.'], [FAIRY, 'Thank you, witch. Come visit any time!']]);
      break;
    case 'crystal':
      if (f.crystal) say([[ME, 'It hums warmly now.']]);
      else if (!f.spark) say([[ME, 'Cold and dark. A spell might wake it... if I knew one.']]);
      else if (S.mana < 10) say([[ME, 'Not enough mana. Maybe that potion in my chest?']]);
      else cast(obj);
      break;
  }
}

// ------------------------------------------------------------------ casting
function cast(target) {
  P.busy = true; faceTo(target.pos[0], target.pos[1]);
  S.mana -= 10; updateQuest();
  playOnce('cast_raise', () => playOnce('cast_flick', () => playOnce('cast_lower', () => { P.busy = false; P.anim = 'stand'; }), 4, () => {
    const h = P.heading * deg, ox = P.x - Math.sin(h) * 22 + Math.cos(h) * 10, oz = P.z + Math.cos(h) * 22 + Math.sin(h) * 10;
    S.fx.push({ kind: 'bolt', x0: ox, z0: oz, h0: 55, x1: target.pos[0], z1: target.pos[1], h1: 45, t: 0, dur: 0.45, onHit: () => {
      S.flags.crystal = true; target.asset = target.swap;
      burst(target.pos[0], target.pos[1], 24, [150, 240, 255]);
      const th = S.objects.find(o => o.asset === 'thorns'); if (th) { th.gone = true; S.grid = buildGrid(S.room); burst(th.pos[0], th.pos[1], 10, [190, 150, 220]); }
      updateQuest();
      setTimeout(() => say([[FAIRY, 'The crystal! It\'s glowing again!'], [ME, 'Spark never fails. Well... rarely.']]), 700);
    } });
  }));
}
function playOnce(anim, done, eventFrame, onEvent) {
  P.anim = anim; P.phase = 0; P.once = { done, eventFrame, onEvent, fired: false };
}
function burst(x, z, n, col) { for (let i = 0; i < n; i++) S.fx.push({ kind: 'spark', x, z, h: 25 + Math.random() * 50, vx: (Math.random() - 0.5) * 100, vz: (Math.random() - 0.5) * 100, vh: 50 + Math.random() * 100, t: 0, dur: 0.7 + Math.random() * 0.5, col }); }

// ------------------------------------------------------------------ movement
function faceTo(x, z) { const dx = x - P.x, dz = z - P.z; if (dx || dz) P.heading = Math.atan2(-dx, dz) / deg; }
function walkTo(x, z, run, onArrive) {
  if (P.busy) return;
  const path = findPath(P.x, P.z, x, z);
  if (!path || !path.length) { if (onArrive) onArrive(); return; }
  P.path = path; P.run = run; P.onArrive = onArrive || null;
}
function stepNpcs(dt) {
  for (const n of S.npcs) {
    if (!n.wander) continue;
    if (n.hold || S.dialog.length) { if (n.anim !== 'stand') { n.anim = 'stand'; n.phase = 0; n.path = []; } continue; }
    if (!n.path.length) {
      n.anim = 'stand'; n.wait -= dt;
      if (n.wait <= 0) {                                       // pick somewhere nearby to potter over to
        const w = n.wander;
        for (let tries = 0; tries < 8; tries++) {
          const a = Math.random() * Math.PI * 2, r = w.radius * (0.4 + 0.6 * Math.random());
          const tx = n.home[0] + Math.cos(a) * r, tz = n.home[1] + Math.sin(a) * r;
          if (!free(...cellOf(tx, tz))) continue;
          const p = findPath(n.x, n.z, tx, tz);
          if (p && p.length) { n.path = p; n.anim = 'walk'; n.phase = 0; break; }
        }
        n.wait = w.pause[0] + Math.random() * (w.pause[1] - w.pause[0]);
      }
      continue;
    }
    const a = A[n.asset + '_walk'], speed = a.speed * a.fps * 0.9;
    let left = speed * dt;
    while (left > 0 && n.path.length) {
      const [tx, tz] = n.path[0], dx = tx - n.x, dz = tz - n.z, d = Math.hypot(dx, dz);
      if (d > 0.01) n.heading = Math.atan2(-dx, dz) / deg;
      if (d <= left) { n.x = tx; n.z = tz; left -= d; n.path.shift(); } else { n.x += dx / d * left; n.z += dz / d * left; left = 0; }
    }
    n.phase += dt * a.fps * 0.9;
    if (!n.path.length) { n.anim = 'stand'; n.phase = 0; }
  }
}
function step(dt) {
  if (P.once) {                                          // one-shot animation (casting)
    const a = A['witch_' + P.anim]; P.phase += dt * a.fps;
    if (!P.once.fired && P.once.eventFrame !== undefined && P.phase >= P.once.eventFrame) { P.once.fired = true; P.once.onEvent(); }
    if (P.phase >= a.n) { const d = P.once.done; P.once = null; P.phase = 0; d(); }
    return;
  }
  if (!P.path.length) { if (P.anim !== 'stand') { P.anim = 'stand'; P.phase = 0; } return; }
  const anim = P.run ? 'run' : 'walk', a = A['witch_' + anim];
  if (P.anim !== anim) { P.anim = anim; P.phase = 0; }
  const pace = P.run ? 1.25 : 1.4;                        // play cycles faster in-game; speed stays matched to the stride
  const speed = a.speed * a.fps * pace;                  // cubes per second
  let left = speed * dt;
  while (left > 0 && P.path.length) {
    const [tx, tz] = P.path[0], dx = tx - P.x, dz = tz - P.z, d = Math.hypot(dx, dz);
    if (d > 0.01) P.heading = Math.atan2(-dx, dz) / deg;
    if (d <= left) { P.x = tx; P.z = tz; left -= d; P.path.shift(); }
    else { P.x += dx / d * left; P.z += dz / d * left; left = 0; }
  }
  P.phase += dt * a.fps * pace;
  for (const e of S.room.exits) if (P.x >= e.rect[0] && P.x <= e.rect[2] && P.z >= e.rect[1] && P.z <= e.rect[3]) { changeRoom(e); return; }
  if (!P.path.length) { P.anim = 'stand'; const cb = P.onArrive; P.onArrive = null; if (cb) cb(); }
}

// ------------------------------------------------------------------ input
function toCanvas(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * VW / r.width, (e.clientY - r.top) * VH / r.height]; }
function opaqueNear(d, X, Y) {                          // is there a visible pixel of this object under the pointer?
  const px = d.hit.canvas.getContext('2d', { willReadFrequently: true })
    .getImageData(Math.round(X - d.hit.ix) - 2, Math.round(Y - d.hit.iy) - 2, 5, 5).data;
  for (let i = 3; i < px.length; i += 4) if (px[i] > 0) return true;
  return false;
}
function targetsAt(X, Y) {
  const hits = [];
  for (const d of S.drawn || []) if (d.hit && d.label && X >= d.box[0] && X <= d.box[2] && Y >= d.box[1] && Y <= d.box[3] && opaqueNear(d, X, Y)) hits.push(d);
  for (const e of S.room.exits) {
    const xs = [e.rect[0], e.rect[2]], zs = [e.rect[1], e.rect[3]], pts = [];
    for (const x of xs) for (const z of zs) for (const h of [0, 85]) pts.push(proj(x, z, h));
    const b = [Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1])), Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))];
    if (X >= b[0] && X <= b[2] && Y >= b[1] && Y <= b[3]) hits.push({ label: e.label, exit: e, depth: 1e9 });
  }
  hits.sort((a, b) => b.depth - a.depth);                // front-most first
  return hits[0] || null;
}
cv.addEventListener('mousemove', e => {
  const [X, Y] = toCanvas(e); const t = S.dialog.length ? null : targetsAt(X, Y);
  S.hover = t; cv.style.cursor = t ? 'pointer' : 'default';
  const l = $('label');
  if (t) { const r = cv.getBoundingClientRect(); l.style.display = 'block'; l.textContent = t.label; l.style.left = (e.clientX - r.left) + 'px'; l.style.top = (e.clientY - r.top) + 'px'; }
  else l.style.display = 'none';
});
cv.addEventListener('mouseleave', () => { $('label').style.display = 'none'; });
function act(t, run) {
  if (t.exit) { const e = t.exit; walkTo((e.rect[0] + e.rect[2]) / 2, (e.rect[1] + e.rect[3]) / 2, run); return; }
  const it = t.interact, obj = t.obj;
  let at = it.at;
  if (obj.wander) {                                        // a wanderer waits for you; meet them where they are
    obj.hold = true;
    const dx = P.x - obj.x, dz = P.z - obj.z, d = Math.hypot(dx, dz) || 1;
    at = [obj.x + dx / d * 42, obj.z + dz / d * 42];
  }
  walkTo(at[0], at[1], run, () => { faceTo(obj.pos ? obj.pos[0] : obj.x, obj.pos ? obj.pos[1] : obj.z); interact(it.id, obj); });
}
cv.addEventListener('click', e => {
  if (S.dialog.length) { advance(); return; }
  if (S.fading || P.busy) return;
  const [X, Y] = toCanvas(e), t = targetsAt(X, Y);
  if (t) act(t, P.run && P.path.length > 0);
  else { const [x, z] = unproj(X, Y); walkTo(x, z, false); S.fx.push({ kind: 'ping', x, z, t: 0, dur: 0.5 }); }
});
cv.addEventListener('dblclick', () => { if (P.path.length) P.run = true; });
$('dialog').addEventListener('click', advance);
addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') { if (S.dialog.length) { e.preventDefault(); advance(); } } });

// ------------------------------------------------------------------ frame
function render() {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#0c0a16'; ctx.fillRect(0, 0, VW, VH);
  drawFloor();
  for (const e of S.room.exits) {                                   // soft glow on exits
    const [X, Y] = proj((e.rect[0] + e.rect[2]) / 2, (e.rect[1] + e.rect[3]) / 2), k = S.cam, p = 0.5 + 0.5 * Math.sin(S.time * 3);
    ctx.fillStyle = `rgba(230,210,140,${0.18 + 0.15 * p})`; ctx.beginPath(); ctx.ellipse(X, Y, 18 * k.S, 18 * k.S * k.sn, 0, 0, 7); ctx.fill();
  }
  const list = [];
  for (const o of S.context) {                           // look-only scenery from neighbouring rooms
    const depth = o.wall ? Math.min(...[o.pos[0] - o.block[0], o.pos[0] + o.block[0]].flatMap(x => [o.pos[1] - o.block[1], o.pos[1] + o.block[1]].map(z => proj(x, z)[2]))) : proj(o.pos[0], o.pos[1])[2];
    list.push({ depth, obj: o, s: [o.asset, 0, o.pos[0], o.pos[1], 0, 0], wall: o.wall });
  }
  for (const o of S.objects) {
    if (o.gone) continue;
    let depth;
    if (o.wall) { const xs = [o.pos[0] - o.block[0], o.pos[0] + o.block[0]], zs = [o.pos[1] - o.block[1], o.pos[1] + o.block[1]]; depth = Math.min(...xs.flatMap(x => zs.map(z => proj(x, z)[2]))); }
    else depth = proj(o.pos[0], o.pos[1])[2];
    list.push({ depth, obj: o, s: [o.asset, 0, o.pos[0], o.pos[1], 0, 0], label: o.interact && o.interact.label, interact: o.interact, wall: o.wall });
  }
  for (const n of S.npcs) {
    if (n.anim !== 'walk' && Math.hypot(P.x - n.x, P.z - n.z) < 150) { const want = Math.atan2(-(P.x - n.x), P.z - n.z) / deg; n.heading += ((((want - n.heading) % 360) + 540) % 360 - 180) * 0.08; }
    const lift = n.bob ? 14 + n.bob * 2 * Math.sin(S.time * 2.5) : 0;
    list.push({ depth: proj(n.x, n.z)[2], obj: n, s: [n.asset + '_' + n.anim, Math.floor(n.phase), n.x, n.z, n.heading, lift], shadow: [n.x, n.z, n.bob ? 14 : 16, n.bob ? 0.25 : 0.35], label: n.interact.label, interact: n.interact });
  }
  const me = { depth: proj(P.x, P.z)[2], s: ['witch_' + P.anim, Math.floor(P.phase), P.x, P.z, P.heading, 0], shadow: [P.x, P.z, 16], player: true };
  list.push(me);
  list.sort((a, b) => a.depth - b.depth);
  // anything drawn in front of her that covers her body fades, so she never disappears behind a tree
  const pb = stackBox(...me.s), core = [pb[0] + (pb[2] - pb[0]) * 0.3, pb[1] + (pb[3] - pb[1]) * 0.25, pb[2] - (pb[2] - pb[0]) * 0.3, pb[3] - (pb[3] - pb[1]) * 0.15];
  let after = false;
  for (const d of list) {
    if (d.player) { after = true; }
    let alpha = 1;
    if (after && !d.player && !d.label) {
      const b = stackBox(...d.s);
      if (b[0] < core[2] && b[2] > core[0] && b[1] < core[3] && b[3] > core[1] && b[3] - b[1] > (pb[3] - pb[1]) * 0.5) alpha = 0.4;
    }
    if (d.shadow) shadow(...d.shadow);
    ctx.globalAlpha = alpha; d.hit = drawStack(...d.s); d.box = d.hit.box; ctx.globalAlpha = 1;
  }
  S.drawn = list;
  drawFx();
}
function drawFx(dt) {
  for (const f of S.fx) {
    const k = f.t / f.dur;
    if (f.kind === 'ping') { const [X, Y] = proj(f.x, f.z); ctx.strokeStyle = `rgba(230,220,255,${1 - k})`; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(X, Y, (6 + 14 * k) * S.cam.S, (6 + 14 * k) * S.cam.S * S.cam.sn, 0, 0, 7); ctx.stroke(); }
    if (f.kind === 'spark') { const [X, Y] = proj(f.x + f.vx * f.t, f.z + f.vz * f.t, f.h + f.vh * f.t - 100 * f.t * f.t); const s = S.cam.S * 3 * (1 - k); ctx.fillStyle = `rgba(${f.col},${1 - k})`; ctx.fillRect(X - s, Y - s / 3, 2 * s, 2 * s / 3); ctx.fillRect(X - s / 3, Y - s, 2 * s / 3, 2 * s); }
    if (f.kind === 'bolt') {
      for (let i = 0; i < 6; i++) {
        const q = Math.max(0, k - i * 0.04), [X, Y] = proj(f.x0 + (f.x1 - f.x0) * q, f.z0 + (f.z1 - f.z0) * q, f.h0 + (f.h1 - f.h0) * q + 30 * Math.sin(Math.PI * q));
        const s = S.cam.S * (5 - i * 0.7); ctx.fillStyle = i ? `rgba(200,180,255,${0.7 - i * 0.1})` : '#fff'; ctx.fillRect(X - s, Y - s, 2 * s, 2 * s);
      }
    }
  }
}
function updateFx(dt) {
  for (const f of S.fx) { f.t += dt; if (f.kind === 'bolt' && f.t >= f.dur && f.onHit) { f.onHit(); f.onHit = null; } }
  S.fx = S.fx.filter(f => f.t < f.dur);
}

let last = 0;
function tick(now) {
  const dt = last ? Math.min(0.05, (now - last) / 1000) : 0; last = now; S.time += dt;
  if (!S.fading && (!S.dialog.length || P.once)) step(dt);       // casts keep playing under dialogue
  if (!S.fading) stepNpcs(dt);
  if (S.mana < S.maxMana && !P.busy) { S.mana = Math.min(S.maxMana, S.mana + dt * 0.8); if (Math.random() < 0.05) updateQuest(); }
  pickCamera(); updateCamera(dt); updateFx(dt); render();
  requestAnimationFrame(tick);
}

loadAssets().then(() => {
  $('loading').style.display = 'none';
  const st = DATA.rooms[DATA.start];
  enterRoom(DATA.start, st.start, st.start_face);
  say([['', 'Click the ground to walk. Double-click to run. Click things to look, talk, or cast.'], ['Witch', 'Morning already? Something feels... off. Is that a note on my table?']]);
  requestAnimationFrame(tick);
});
window.__S = S; window.__G = { enterRoom, walkTo, targetsAt, proj, interact, act, findPath };   // for debugging / tests
}
