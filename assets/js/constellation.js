/*!
 * constellation.js — render any shape as an interactive, physical cloud of light.
 *
 * One engine, many sources. A source turns something into "targets" (points in a
 * unit space, where the shape's half-height is 1) and the engine gives every
 * target a star: a small body with a position, a velocity, a spring back to its
 * target and some damping. Stars without a target drift as background dust and
 * get recruited when the next scene needs them, so a timeline of scenes morphs
 * the same light from a logo into a line of typed terminal text into a torus.
 *
 * Sources shipped (register more with Constellation.registerSource):
 *   svg       any SVG — filled paths with holes, stroked paths, basic shapes
 *   text      a string, rasterized with a font and sampled
 *   terminal  a scripted shell session typed in real time, glyph by glyph (columns
 *             default to the longest line; `glow: point` keeps small text crisp)
 *   points    a 3D point cloud: inline, a JSON URL, or a built-in generator
 *   image     a same-origin image, sampled by alpha or brightness
 *
 * Interaction (all configurable, all optional): drag to turn and tilt with
 * inertia, arrow keys, an idle spin, a hovering pointer that scatters stars with
 * pointer-speed physics, and a click that sends a shockwave through them.
 *
 * Markup contract (see _includes/constellation.html):
 *   [data-constellation]                          root; CSS sizes it
 *     script[type=application/json][data-constellation-config]   the config (optional)
 *     canvas                                      drawing surface
 *     button.constellation__drag                  pointer surface, keyboard target
 *     [data-constellation-shape] svg              default geometry for the svg source
 *   data-accents="#hex,#hex,#hex"                 palette fallback when the config has none
 *
 * Progressive by design: without JS or canvas the fallback markup stays; under
 * prefers-reduced-motion the first scene renders once and only moves on input.
 * Deterministic: a seeded generator, so every visitor sees the same stars.
 */
(function () {
  'use strict';

  /* ======================================================================
   * Defaults — every knob a scene file can override. Lengths are in
   * half-sizes (the shape's half-height = 1) unless a comment says px or S
   * (S = the shorter canvas side in CSS px). Speeds are per second.
   * ==================================================================== */
  var DEFAULTS = {
    particles: 3600,          // pool size at a 400px canvas; scaled by area, clamped below
    minParticles: 900,
    maxParticles: 4200,
    seed: 20260905,
    palette: {
      base: '#ffffff',
      accents: ['#ffe900', '#376986', '#a11111'],
      edgeWeights: [0.56, 0.22, 0.17, 0.05],    // base, accent 1, accent 2, accent 3
      innerWeights: [0.22, 0.12, 0.56, 0.10]
    },
    look: {
      edge:  { size: [0.010, 0.022], alpha: 0.9 },   // sizes are fractions of S
      inner: { size: [0.006, 0.013], alpha: 0.55 },
      dust:  { size: [0.005, 0.010], alpha: 0.4 },
      text:  { size: [0.009, 0.017], alpha: 0.9 },
      glyph: { size: [0.005, 0.010], alpha: 0.95 },   // terminal characters: small and crisp
      point: { size: [0.008, 0.016], alpha: 0.8 },
      free:  { size: [0.004, 0.009], alpha: 0.22 },
      sparklers: 0.05,        // share of edge stars that twinkle hard and fast
      twinkle: true,
      jitter: 0.008,          // idle wander around the target
      glow: 'soft',           // 'soft' halo sprites, or 'point' for crisper dots
      halo: { accent: 1, alpha: 0.16, scale: 2.6 },   // wash behind the shape; accent index, or -1
      stars: 110,             // fixed backdrop stars (not part of the pool)
      intro: 'scatter',       // 'scatter' flies the first scene in; 'none' starts assembled
      scatter: 1.4            // radius of the free-star field
    },
    camera: { focal: 4, radius: 0.40, restTilt: 0.16, startYaw: -0.55, maxTilt: 1.2 },
    motion: {
      spin: 0.3, nod: 0.08,   // idle turn and the slow tilt that shows depth
      spring: 6, damping: 2.2, maxSpeed: 6,      // star physics toward its target
      freeSpring: 1.2, freeDamping: 2.0
    },
    interaction: {
      drag: true, keys: true, dragYaw: 2.8, dragPitch: 2.0, inertia: 2.4,
      hover: { enabled: true, radius: 0.2, reach: 0.7, force: 0.8, speedGain: 2.0, wake: 0.7, torque: 0.25, fullSpeed: 8 },
      click: { enabled: true, force: 2.0, radius: 0.16, ring: true, ringSpeed: 1.6, ringWidth: 0.05, ringForce: 0.9, life: 0.9, flash: 0.8 }
    },
    scene: { source: 'svg' },
    timeline: null,           // [{ ...scene, hold: seconds }] cycles through scenes
    loop: true,
    settle: 2.0,              // seconds a scene waits for its stars before it plays or holds
    hold: 4                   // default seconds a finished scene stays before the next
  };

  var SCENE_DEFAULTS = {
    svg:      { depth: 0.26, edgeBand: 14, edgeShare: 0.46, dust: 0.09, strokeWidth: 8, fit: 'max' },
    text:     { font: 'bold 160px system-ui, -apple-system, "Segoe UI", sans-serif', width: 1.8, lineHeight: 1.15, density: 5, depth: 0.12 },
    terminal: { font: 'bold 40px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace', cols: 0, width: 2.4, cellAspect: 1.9, density: 3, cps: 16, pause: 0.5, endPause: 1.5, cursor: true, depth: 0.08 },   // cols 0 = the longest line
    points:   { depth: 1, count: 1800, generator: 'sphere' },
    image:    { width: 1.8, density: 4, threshold: 96, depth: 0.12 }
  };

  var SPRITE = 64, WHITE = [255, 255, 255];
  var reduceMotion = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  /* ======================================================================
   * Helpers
   * ==================================================================== */
  function mulberry32(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashString(s) {          // small deterministic hash for per-key randomness
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  function hexToRgb(hex) {
    var m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(hex).trim());
    if (!m) return null;
    var h = m[1];
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  function mix(a, b, t) { return [Math.round(a[0] + (b[0] - a[0]) * t), Math.round(a[1] + (b[1] - a[1]) * t), Math.round(a[2] + (b[2] - a[2]) * t)]; }
  function rgba(c, a) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  function isObj(v) { return v && typeof v === 'object' && !Array.isArray(v); }
  function merge(base, over) {      // deep merge; arrays and scalars replace
    var out = {};
    var k;
    for (k in base) if (Object.prototype.hasOwnProperty.call(base, k)) out[k] = isObj(base[k]) ? merge(base[k], {}) : base[k];
    for (k in over) if (Object.prototype.hasOwnProperty.call(over, k)) {
      out[k] = isObj(over[k]) && isObj(out[k]) ? merge(out[k], over[k]) : (isObj(over[k]) ? merge(over[k], {}) : over[k]);
    }
    return out;
  }
  function pick(weights, r) {
    var acc = 0;
    for (var i = 0; i < weights.length; i++) { acc += weights[i]; if (r < acc) return i; }
    return weights.length - 1;
  }

  function makeSprite(rgb, style) {
    var c = document.createElement('canvas');
    c.width = c.height = SPRITE;
    var g = c.getContext('2d'), r = SPRITE / 2;
    var grad = g.createRadialGradient(r, r, 0, r, r, r);
    if (style === 'point') {
      grad.addColorStop(0.00, rgba(WHITE, 1));
      grad.addColorStop(0.30, rgba(mix(rgb, WHITE, 0.4), 0.95));
      grad.addColorStop(0.42, rgba(rgb, 0.25));
      grad.addColorStop(1.00, rgba(rgb, 0));
    } else {
      grad.addColorStop(0.00, rgba(WHITE, 1));
      grad.addColorStop(0.16, rgba(mix(rgb, WHITE, 0.55), 0.9));
      grad.addColorStop(0.40, rgba(rgb, 0.32));
      grad.addColorStop(1.00, rgba(rgb, 0));
    }
    g.fillStyle = grad; g.fillRect(0, 0, SPRITE, SPRITE);
    return c;
  }
  function makeHalo(rgb) {
    var c = document.createElement('canvas');
    c.width = c.height = SPRITE;
    var g = c.getContext('2d'), r = SPRITE / 2;
    var grad = g.createRadialGradient(r, r, 0, r, r, r);
    grad.addColorStop(0.00, rgba(rgb, 0.55));
    grad.addColorStop(0.45, rgba(rgb, 0.18));
    grad.addColorStop(1.00, rgba(rgb, 0));
    g.fillStyle = grad; g.fillRect(0, 0, SPRITE, SPRITE);
    return c;
  }

  // Draw something on an offscreen canvas and return the lit pixels on a grid.
  function rasterSample(draw, w, h, step, threshold) {
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    var g = c.getContext('2d');
    if (!g) return [];
    draw(g, w, h);
    var data;
    try { data = g.getImageData(0, 0, w, h).data; } catch (err) { return []; }   // tainted (cross-origin image)
    var pts = [];
    for (var y = step / 2; y < h; y += step) {
      for (var x = step / 2; x < w; x += step) {
        var i = ((y | 0) * w + (x | 0)) * 4;
        if (data[i + 3] > threshold) pts.push([x, y]);
      }
    }
    return pts;
  }

  function fetchText(url) {
    return fetch(url, { credentials: 'same-origin' }).then(function (r) { if (!r.ok) throw new Error(url + ': ' + r.status); return r.text(); });
  }

  /* ======================================================================
   * SVG geometry: any path or basic shape, as fill, hole or stroke
   * ==================================================================== */
  function shapeToPath(el) {
    var tag = el.tagName.toLowerCase();
    function a(n, d) { var v = parseFloat(el.getAttribute(n)); return isNaN(v) ? (d || 0) : v; }
    switch (tag) {
      case 'path': return el.getAttribute('d') || '';
      case 'rect': { var x = a('x'), y = a('y'), w = a('width'), h = a('height'); return 'M' + x + ' ' + y + 'h' + w + 'v' + h + 'h' + (-w) + 'z'; }
      case 'circle': { var cx = a('cx'), cy = a('cy'), r = a('r'); return 'M' + (cx - r) + ' ' + cy + 'a' + r + ' ' + r + ' 0 1 0 ' + (2 * r) + ' 0a' + r + ' ' + r + ' 0 1 0 ' + (-2 * r) + ' 0z'; }
      case 'ellipse': { var ex = a('cx'), ey = a('cy'), rx = a('rx'), ry = a('ry'); return 'M' + (ex - rx) + ' ' + ey + 'a' + rx + ' ' + ry + ' 0 1 0 ' + (2 * rx) + ' 0a' + rx + ' ' + ry + ' 0 1 0 ' + (-2 * rx) + ' 0z'; }
      case 'polygon': case 'polyline': {
        var pts = (el.getAttribute('points') || '').trim().split(/[\s,]+/);
        if (pts.length < 4) return '';
        var d = 'M' + pts[0] + ' ' + pts[1];
        for (var i = 2; i + 1 < pts.length; i += 2) d += 'L' + pts[i] + ' ' + pts[i + 1];
        return tag === 'polygon' ? d + 'z' : d;
      }
      case 'line': return 'M' + a('x1') + ' ' + a('y1') + 'L' + a('x2') + ' ' + a('y2');
    }
    return '';
  }
  function translateOf(el, stop) {   // translate() offsets up the tree (the only transform honoured)
    var tx = 0, ty = 0, n = el;
    while (n && n !== stop && n.getAttribute) {
      var tr = n.getAttribute('transform');
      var m = tr && /translate\(\s*([-+\d.eE]+)(?:[\s,]+([-+\d.eE]+))?\s*\)/.exec(tr);
      if (m) { tx += parseFloat(m[1]); ty += parseFloat(m[2] || '0'); }
      n = n.parentNode;
    }
    return [tx, ty];
  }
  function styleProp(el, name) {
    var v = el.getAttribute(name);
    if (v) return v;
    var m = new RegExp('(?:^|;)\\s*' + name + '\\s*:\\s*([^;]+)').exec(el.getAttribute('style') || '');
    return m ? m[1].trim() : null;
  }

  function sampleSvg(svgEl, cfg, rand, budget) {
    if (typeof Path2D === 'undefined') return [];
    var vb = (svgEl.getAttribute('viewBox') || ('0 0 ' + (parseFloat(svgEl.getAttribute('width')) || 512) + ' ' + (parseFloat(svgEl.getAttribute('height')) || 512))).split(/[\s,]+/).map(Number);
    var els = svgEl.querySelectorAll('path, rect, circle, ellipse, polygon, polyline, line');
    var fills = [], holes = [], strokes = [];
    for (var i = 0; i < els.length; i++) {
      var el = els[i], d = shapeToPath(el);
      if (!d) continue;
      var role = el.getAttribute('data-shape');
      if (!role) {
        var fill = styleProp(el, 'fill'), stroke = styleProp(el, 'stroke'), tag = el.tagName.toLowerCase();
        role = ((fill === 'none' || tag === 'line' || tag === 'polyline') && stroke && stroke !== 'none') ? 'stroke' : 'fill';
      }
      var item = { path: new Path2D(d), off: translateOf(el, svgEl), width: parseFloat(styleProp(el, 'stroke-width')) || cfg.strokeWidth };
      (role === 'hole' ? holes : role === 'stroke' ? strokes : fills).push(item);
    }
    if (!fills.length && !strokes.length) return [];

    var probe = document.createElement('canvas');
    probe.width = Math.ceil(vb[2]) || 1; probe.height = Math.ceil(vb[3]) || 1;
    var ctx = probe.getContext('2d');
    if (!ctx || !ctx.isPointInStroke) return [];
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';

    function hit(list, x, y, stroke, width) {
      for (var k = 0; k < list.length; k++) {
        var it = list[k], px = x - it.off[0], py = y - it.off[1];
        if (stroke) { ctx.lineWidth = width || it.width; if (ctx.isPointInStroke(it.path, px, py)) return true; }
        else if (ctx.isPointInPath(it.path, px, py)) return true;
      }
      return false;
    }
    function inFill(x, y) { return hit(fills, x, y) && !hit(holes, x, y); }
    function onEdge(x, y) { return hit(fills, x, y, true, cfg.edgeBand) || hit(holes, x, y, true, cfg.edgeBand); }
    function onStroke(x, y) { return hit(strokes, x, y, true); }

    var step = Math.max(2, Math.min(vb[2], vb[3]) / 128);
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (var sy = vb[1]; sy <= vb[1] + vb[3]; sy += step) {
      for (var sx = vb[0]; sx <= vb[0] + vb[2]; sx += step) {
        if (inFill(sx, sy) || onEdge(sx, sy) || onStroke(sx, sy)) {
          if (sx < minX) minX = sx; if (sx > maxX) maxX = sx;
          if (sy < minY) minY = sy; if (sy > maxY) maxY = sy;
        }
      }
    }
    if (minX === Infinity) return [];
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    var R = cfg.fit === 'height' ? (maxY - minY) / 2 : cfg.fit === 'width' ? (maxX - minX) / 2 : Math.max(maxX - minX, maxY - minY) / 2;
    var bx = minX - step, by = minY - step, bw = maxX - minX + 2 * step, bh = maxY - minY + 2 * step;

    var count = cfg.count || budget;
    var hasFill = fills.length > 0;
    var nEdge = hasFill ? Math.round(count * cfg.edgeShare) : count;
    var guard = count * 80, out = [];
    function sample(edge) {
      while (guard-- > 0) {
        var x = bx + rand() * bw, y = by + rand() * bh;
        if (edge) { if (onEdge(x, y) || onStroke(x, y)) return [x, y]; }
        else if (inFill(x, y) && !onEdge(x, y)) return [x, y];
      }
      return null;
    }
    for (var n = 0; n < count; n++) {
      var edge = n < nEdge;
      var p = sample(edge);
      if (!p) break;
      var x = (p[0] - cx) / R, y = (p[1] - cy) / R, z = (rand() - 0.5) * cfg.depth;
      var dust = edge && rand() < cfg.dust;
      if (dust) { var ang = rand() * Math.PI * 2, dist = 0.03 + rand() * 0.14; x += Math.cos(ang) * dist; y += Math.sin(ang) * dist; z *= 1.6; }
      out.push({ key: 'svg:' + n, x: x, y: y, z: z, look: dust ? 'dust' : edge ? 'edge' : 'inner' });
    }
    return out;
  }

  /* ======================================================================
   * Sources
   * ==================================================================== */
  var sources = {};
  function registerSource(name, fn) { sources[name] = fn; }

  // svg: cfg.svg may be omitted (the shape inside the root), a selector, { selector },
  // { url } (fetched, same-origin), or { markup } (an SVG string).
  registerSource('svg', function (cfg, ctx) {
    var spec = cfg.svg;
    function fromMarkup(text) {
      var doc = new DOMParser().parseFromString(text, 'image/svg+xml');
      return doc.querySelector('svg');
    }
    var el = null;
    if (!spec) el = ctx.root.querySelector('[data-constellation-shape] svg, svg[data-constellation-shape]');
    else if (typeof spec === 'string') el = document.querySelector(spec);
    else if (spec.selector) el = document.querySelector(spec.selector);
    else if (spec.markup) el = fromMarkup(spec.markup);
    else if (spec.url) return fetchText(spec.url).then(function (t) { var e = fromMarkup(t); return { targets: e ? sampleSvg(e, cfg, ctx.rand, ctx.budget) : [] }; });
    return { targets: el ? sampleSvg(el, cfg, ctx.rand, ctx.budget) : [] };
  });

  function sampleText(cfg, rand, look, keyPrefix) {
    var lines = String(cfg.text || '').split('\n');
    var m = /(\d+(?:\.\d+)?)px/.exec(cfg.font), fs = m ? parseFloat(m[1]) : 120;
    var probe = document.createElement('canvas').getContext('2d');
    probe.font = cfg.font;
    var w = 0;
    for (var i = 0; i < lines.length; i++) w = Math.max(w, probe.measureText(lines[i]).width);
    var lh = fs * cfg.lineHeight, pad = fs * 0.2;
    var W = Math.ceil(w + pad * 2), H = Math.ceil(lh * lines.length + pad * 2);
    var pts = rasterSample(function (g) {
      g.font = cfg.font; g.fillStyle = '#fff'; g.textBaseline = 'top'; g.textAlign = cfg.align || 'center';
      var x = cfg.align === 'left' ? pad : cfg.align === 'right' ? W - pad : W / 2;
      for (var j = 0; j < lines.length; j++) g.fillText(lines[j], x, pad + j * lh + (lh - fs) / 2);
    }, W, H, cfg.density, 100);
    var scale = cfg.width / W, out = [];
    for (var k = 0; k < pts.length; k++) {
      out.push({ key: (keyPrefix || 'text:') + k, x: (pts[k][0] - W / 2) * scale, y: (pts[k][1] - H / 2) * scale, z: (rand() - 0.5) * cfg.depth, look: look || 'text' });
    }
    return out;
  }
  registerSource('text', function (cfg, ctx) { return { targets: sampleText(cfg, ctx.rand) }; });

  // terminal: a scripted session. Each line is { prompt, type } (typed at cps),
  // { print } (appears at once), optionally with `role` (prompt|input|output|error|comment)
  // and `pause` (seconds after the line). Glyphs are rasterized once per character.
  var glyphCache = {};
  function glyphPoints(ch, font, density) {
    var key = font + '|' + density + '|' + ch;
    if (glyphCache[key]) return glyphCache[key];
    var m = /(\d+(?:\.\d+)?)px/.exec(font), fs = m ? parseFloat(m[1]) : 40;
    var W = Math.ceil(fs * 0.7), H = Math.ceil(fs * 1.3);
    var pts = rasterSample(function (g) {
      g.font = font; g.fillStyle = '#fff'; g.textBaseline = 'middle'; g.textAlign = 'center';
      g.fillText(ch, W / 2, H / 2);
    }, W, H, density, 100).map(function (p) { return [p[0] / W, p[1] / H]; });
    glyphCache[key] = pts;
    return pts;
  }
  var ROLE_COLOR = { prompt: 1, input: 0, output: 2, error: 3, comment: 2 };
  registerSource('terminal', function (cfg, ctx) {
    var lines = cfg.lines || [];
    var events = [], t = 0, rows = 0;
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i], row = rows++;
      var col = 0;
      if (ln.prompt) { for (var a = 0; a < ln.prompt.length; a++) events.push({ t: t, row: row, col: col++, ch: ln.prompt[a], role: 'prompt' }); }
      var typed = ln.type != null ? String(ln.type) : null, printed = ln.print != null ? String(ln.print) : null;
      if (typed !== null) {
        for (var b = 0; b < typed.length; b++) { t += 1 / cfg.cps * (0.7 + 0.6 * ((hashString(row + ':' + b) % 100) / 100)); events.push({ t: t, row: row, col: col++, ch: typed[b], role: ln.role || 'input' }); }
      }
      if (printed !== null) {
        t += ln.delay != null ? ln.delay : 0.25;
        for (var c = 0; c < printed.length; c++) events.push({ t: t, row: row, col: col++, ch: printed[c], role: ln.role || 'output' });
      }
      t += ln.pause != null ? ln.pause : cfg.pause;
      if (rows >= (cfg.rows || 12)) break;
    }
    var longest = 1;
    for (var L = 0; L < lines.length; L++) longest = Math.max(longest, (lines[L].prompt || '').length + String(lines[L].type != null ? lines[L].type : lines[L].print != null ? lines[L].print : '').length);
    var cols = cfg.cols > 0 ? cfg.cols : longest + 1, cellW = cfg.width / cols, cellH = cellW * cfg.cellAspect;
    var height = rows * cellH, x0 = -cfg.width / 2, y0 = -height / 2;
    var screen = [], cursor = { row: 0, col: 0 }, next = 0, targets = [], done = false, endAt = t + cfg.endPause;

    function cell(ev) {
      var pts = glyphPoints(ev.ch, cfg.font, cfg.density), out = [];
      var color = ROLE_COLOR[ev.role] != null ? ROLE_COLOR[ev.role] : 0;
      for (var k = 0; k < pts.length; k++) {
        var key = 't:' + ev.row + ':' + ev.col + ':' + k;
        out.push({ key: key, x: x0 + (ev.col + pts[k][0]) * cellW, y: y0 + (ev.row + pts[k][1]) * cellH,
          z: ((hashString(key) % 1000) / 1000 - 0.5) * cfg.depth, look: 'glyph', color: color, alpha: ev.role === 'comment' ? 0.6 : 1 });
      }
      return out;
    }
    function build() {
      var out = [];
      for (var s = 0; s < screen.length; s++) out = out.concat(screen[s]);
      if (cfg.cursor && !done) {
        for (var q = 0; q < 6; q++) out.push({ key: 'cursor:' + q, x: x0 + (cursor.col + 0.15 + 0.7 * ((q % 3) / 2)) * cellW, y: y0 + (cursor.row + 0.3 + 0.5 * (q < 3 ? 0 : 1)) * cellH, z: 0, look: 'glyph', color: 1, blink: true });
      }
      return out;
    }
    return {
      targets: build(),
      update: function (tPlay) {
        if (done) return null;
        var changed = false;
        while (next < events.length && events[next].t <= tPlay) {
          var ev = events[next++];
          screen.push(cell(ev));
          cursor = { row: ev.row, col: ev.col + 1 };
          changed = true;
        }
        if (next >= events.length && tPlay >= endAt) { done = true; changed = true; }
        this.done = done;
        return changed ? build() : null;
      },
      done: false
    };
  });

  // points: { points: [[x,y,z],...] } | { url } (JSON: array or {points}) | { generator }
  var generators = {
    sphere: function (n, rand) { var out = []; for (var i = 0; i < n; i++) { var u = rand() * 2 - 1, th = rand() * Math.PI * 2, r = Math.sqrt(1 - u * u); out.push([r * Math.cos(th), u, r * Math.sin(th)]); } return out; },
    torus: function (n, rand, cfg) { var out = [], R = 0.7, r = cfg.tube || 0.3; for (var i = 0; i < n; i++) { var a = rand() * Math.PI * 2, b = rand() * Math.PI * 2; out.push([(R + r * Math.cos(b)) * Math.cos(a), r * Math.sin(b), (R + r * Math.cos(b)) * Math.sin(a)]); } return out; },
    helix: function (n, rand, cfg) { var out = [], turns = cfg.turns || 4; for (var i = 0; i < n; i++) { var s = rand(), a = s * Math.PI * 2 * turns, k = i % 2 ? 1 : -1; out.push([0.6 * Math.cos(a) * k, s * 2 - 1, 0.6 * Math.sin(a) * k]); } return out; },
    cube: function (n, rand) { var out = []; for (var i = 0; i < n; i++) { var f = (rand() * 6) | 0, u = rand() * 2 - 1, v = rand() * 2 - 1, s = f % 2 ? 1 : -1; out.push(f < 2 ? [s, u, v] : f < 4 ? [u, s, v] : [u, v, s]); } return out; }
  };
  function normalisePoints(raw, cfg) {
    var pts = Array.isArray(raw) ? raw : (raw && raw.points) || [];
    var minX = Infinity, minY = Infinity, minZ = Infinity, maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;
    for (var i = 0; i < pts.length; i++) { var p = pts[i]; if (p[0] < minX) minX = p[0]; if (p[0] > maxX) maxX = p[0]; if (p[1] < minY) minY = p[1]; if (p[1] > maxY) maxY = p[1]; if ((p[2] || 0) < minZ) minZ = p[2] || 0; if ((p[2] || 0) > maxZ) maxZ = p[2] || 0; }
    if (!pts.length) return [];
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2, cz = (minZ + maxZ) / 2;
    var R = Math.max(maxX - minX, maxY - minY, maxZ - minZ) / 2 || 1;
    var out = [], flipY = cfg.yUp !== false;   // most 3D data is y-up; the canvas is y-down
    for (var k = 0; k < pts.length; k++) {
      out.push({ key: 'pt:' + k, x: (pts[k][0] - cx) / R, y: (flipY ? -1 : 1) * (pts[k][1] - cy) / R, z: ((pts[k][2] || 0) - cz) / R * cfg.depth, look: 'point' });
    }
    return out;
  }
  registerSource('points', function (cfg, ctx) {
    if (cfg.points) return { targets: normalisePoints(cfg.points, cfg) };
    if (cfg.url) return fetchText(cfg.url).then(function (t) { return { targets: normalisePoints(JSON.parse(t), cfg) }; });
    var gen = generators[cfg.generator] || generators.sphere;
    return { targets: normalisePoints(gen(Math.min(cfg.count, ctx.budget), ctx.rand, cfg), cfg) };
  });
  registerSource('image', function (cfg, ctx) {
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () {
        var W = Math.min(img.naturalWidth, 320), H = Math.round(img.naturalHeight * W / img.naturalWidth);
        var pts = rasterSample(function (g) { g.drawImage(img, 0, 0, W, H); }, W, H, cfg.density, cfg.threshold);
        var scale = cfg.width / W, out = [];
        for (var k = 0; k < pts.length; k++) out.push({ key: 'img:' + k, x: (pts[k][0] - W / 2) * scale, y: (pts[k][1] - H / 2) * scale, z: (ctx.rand() - 0.5) * cfg.depth, look: 'text' });
        resolve({ targets: out });
      };
      img.onerror = function () { resolve({ targets: [] }); };
      img.src = cfg.image && cfg.image.url ? cfg.image.url : cfg.image;
    });
  });

  /* ======================================================================
   * The engine
   * ==================================================================== */
  function Constellation(root) {
    this.root = root;
    this.canvas = root.querySelector('canvas');
    this.drag = root.querySelector('.constellation__drag') || root.querySelector('button');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    if (!this.ctx) return;

    var cfgEl = root.querySelector('script[data-constellation-config]');
    var user = {};
    if (cfgEl) { try { user = JSON.parse(cfgEl.textContent || '{}') || {}; } catch (err) { user = {}; } }
    var cfg = this.cfg = merge(DEFAULTS, user);
    if (!user.palette && root.dataset.accents) cfg.palette.accents = root.dataset.accents.split(',');
    if (root.dataset.particles) cfg.particles = parseInt(root.dataset.particles, 10) || cfg.particles;

    this.W = 0; this.H = 0; this.S = 0; this.dpr = 1;
    this.measure();
    var scale = this.S > 0 ? Math.pow(this.S / 400, 2) : 1;
    this.budget = Math.round(clamp(cfg.particles * scale, cfg.minParticles, cfg.maxParticles));

    this.rand = mulberry32(cfg.seed);
    var accents = cfg.palette.accents.map(hexToRgb).filter(Boolean);
    while (accents.length < 3) accents.push(WHITE);
    this.palette = [hexToRgb(cfg.palette.base) || WHITE].concat(accents);
    this.sprites = this.palette.map(function (c) { return makeSprite(c, cfg.look.glow); });
    var hi = cfg.look.halo.accent;
    this.halo = hi >= 0 && this.palette[hi + 1] ? makeHalo(this.palette[hi + 1]) : null;

    this.particles = []; this.free = []; this.byKey = {};
    this.stars = [];
    for (var i = 0; i < cfg.look.stars; i++) this.stars.push({ x: this.rand() * 2 - 1, y: this.rand() * 2 - 1, r: 0.4 + this.rand() * 1.1, a: 0.25 + this.rand() * 0.6, tw: this.rand() * Math.PI * 2, ts: 0.3 + this.rand() * 0.8, depth: 0.3 + this.rand() * 0.7 });

    this.t0 = performance.now() / 1000; this.tPrev = null;
    this.rx = cfg.camera.restTilt; this.ry = cfg.camera.startYaw; this.vx = 0; this.vy = 0; this.rxTarget = null;
    this.dragging = false; this.pointer = null; this.ptrVel = { x: 0, y: 0 }; this.ptrT = 0; this.press = null;
    this.waves = [];
    this.lastInteraction = -Infinity;
    this.reduced = !!(reduceMotion && reduceMotion.matches);
    this.visible = true; this.dirty = true; this.raf = 0; this.disturbed = false;

    this.scenes = cfg.timeline && cfg.timeline.length ? cfg.timeline : [cfg.scene];
    this.sceneIndex = -1; this.active = null;

    this.applySize();
    this.bind();
    root.classList.add('is-live');
    root.setAttribute('data-constellation-ready', 'true');
    this.playScene(0);
    this.start();
  }

  Constellation.prototype.now = function () { return performance.now() / 1000 - this.t0; };

  Constellation.prototype.measure = function () {
    var rect = this.root.getBoundingClientRect();
    var W = Math.round(rect.width || 0), H = Math.round(rect.height || rect.width || 0);
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var changed = W !== this.W || H !== this.H || dpr !== this.dpr;
    this.W = W; this.H = H; this.S = Math.min(W, H); this.dpr = dpr;
    return changed;
  };
  Constellation.prototype.applySize = function () {
    var w = Math.max(1, Math.round(this.W * this.dpr)), h = Math.max(1, Math.round(this.H * this.dpr));
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    this.dirty = true;
  };

  /* ---------- the pool ---------- */
  Constellation.prototype.spawn = function () {
    var look = this.cfg.look, r = this.rand, aspect = this.W && this.H ? this.W / this.H : 1;
    var ang = r() * Math.PI * 2, rad = look.scatter * (0.6 + r() * 0.7);
    var p = {
      x: Math.cos(ang) * rad * Math.max(1, aspect), y: Math.sin(ang) * rad, z: (r() - 0.5) * 1.2,
      vx: 0, vy: 0, vz: 0, hx: 0, hy: 0, hz: 0, key: null, look: 'free', color: pick(look.free.weights || [0.4, 0.2, 0.3, 0.1], r()),
      u: r(), alphaScale: 1, size: 0, alpha: 0, blink: false,
      sparkler: false, twSpeed: 0.8 + r() * 1.6, twPhase: r() * Math.PI * 2, twDepth: 0.28,
      jx: r() * Math.PI * 2, jy: r() * Math.PI * 2, jz: r() * Math.PI * 2
    };
    p.fx = p.x; p.fy = p.y; p.fz = p.z;                 // its resting place as free dust
    if (look.intro === 'none' && !this.particles.length) { /* first scene assembled: handled in setTargets */ }
    this.applyLook(p, 'free', null);
    this.particles.push(p);
    return p;
  };
  Constellation.prototype.applyLook = function (p, name, target) {
    var lk = this.cfg.look[name] || this.cfg.look.inner, pal = this.cfg.palette;
    p.look = name;
    p.size = (lk.size[0] + p.u * (lk.size[1] - lk.size[0])) * (target && target.size ? target.size : 1);
    p.alpha = lk.alpha * (target && target.alpha != null ? target.alpha : 1);
    p.blink = !!(target && target.blink);
    if (target && target.color != null) p.color = clamp(target.color, 0, this.palette.length - 1);
    else if (name === 'edge' || name === 'dust') p.color = pick(pal.edgeWeights, this.rand());
    else if (name === 'inner') p.color = pick(pal.innerWeights, this.rand());
    else if (name === 'text' || name === 'point' || name === 'glyph') p.color = pick(pal.edgeWeights, this.rand());
    p.sparkler = name === 'edge' && this.rand() < this.cfg.look.sparklers;
    p.twDepth = p.sparkler ? 0.7 : 0.28; p.twSpeed = p.sparkler ? 3 + this.rand() * 3 : 0.8 + this.rand() * 1.6;
    if (p.sparkler) p.size *= 1.9;
  };

  // Give every target a star: keep matches by key, free the rest, recruit free
  // stars (or spawn new ones) for new keys. Assembled = place them at home now.
  Constellation.prototype.setTargets = function (targets, assembled) {
    var keep = {}, i, p, t;
    for (i = 0; i < targets.length; i++) keep[targets[i].key] = targets[i];
    for (i = 0; i < this.particles.length; i++) {
      p = this.particles[i];
      if (p.key && !keep[p.key]) { delete this.byKey[p.key]; p.key = null; this.applyLook(p, 'free', null); this.free.push(p); }
    }
    for (i = 0; i < targets.length; i++) {
      t = targets[i];
      p = this.byKey[t.key];
      if (!p) {
        p = this.free.length ? this.free.pop() : (this.particles.length < this.budget * 2 ? this.spawn() : null);
        if (!p) break;
        p.key = t.key; this.byKey[t.key] = p;
        this.applyLook(p, t.look || 'inner', t);
        if (assembled) { p.x = t.x; p.y = t.y; p.z = t.z; p.vx = p.vy = p.vz = 0; }
      } else if (p.look !== (t.look || 'inner') || t.color != null) {
        this.applyLook(p, t.look || 'inner', t);
      }
      p.hx = t.x; p.hy = t.y; p.hz = t.z;
    }
    this.dirty = true;
  };

  /* ---------- scenes ---------- */
  Constellation.prototype.sceneConfig = function (i) {
    var s = this.scenes[i] || {};
    var name = s.source || 'svg';
    return merge(SCENE_DEFAULTS[name] || {}, s);
  };
  Constellation.prototype.playScene = function (i) {
    var self = this, cfg = this.sceneConfig(i), fn = sources[cfg.source];
    this.sceneIndex = i;
    if (!fn) { this.active = null; return; }
    var token = {};
    this.pending = token;
    var ctx = { root: this.root, rand: mulberry32(this.cfg.seed + i * 7919), budget: this.budget, engine: this };
    var first = !this.active && !this.particles.length;
    Promise.resolve(fn(cfg, ctx)).then(function (res) {
      if (self.pending !== token) return;                        // a newer scene won
      // Fill the pool on the first scene so the field has dust to recruit from.
      while (self.particles.length < self.budget) self.free.push(self.spawn());
      var assembled = first && (self.cfg.look.intro === 'none' || self.reduced);
      self.setTargets(res.targets || [], assembled);
      self.active = { cfg: cfg, res: res, start: self.now(), holdFrom: null, settled: false };
      self.start();
    }).catch(function (err) { if (window.console) console.warn('constellation: scene ' + i + ' failed', err); });
  };
  Constellation.prototype.next = function () { if (this.scenes.length > 1) this.playScene((this.sceneIndex + 1) % this.scenes.length); };
  Constellation.prototype.setScene = function (scene) { this.scenes = [scene]; this.playScene(0); };
  Constellation.prototype.setTimeline = function (list, loop) { this.scenes = list; if (loop != null) this.cfg.loop = loop; this.playScene(0); };

  Constellation.prototype.runScene = function (t) {
    var a = this.active;
    if (!a || this.reduced) return;
    var elapsed = t - a.start;
    if (!a.settled) { if (elapsed >= this.cfg.settle) { a.settled = true; a.playStart = t; } else return; }
    var res = a.res;
    if (res.update && !res.done) {
      var targets = res.update(t - a.playStart, this);
      if (targets) this.setTargets(targets, false);
      if (!res.done) return;
    }
    if (a.holdFrom == null) a.holdFrom = t;
    var hold = a.cfg.hold != null ? a.cfg.hold : this.cfg.hold;
    if (this.scenes.length > 1 && t - a.holdFrom >= hold) {
      var last = this.sceneIndex >= this.scenes.length - 1;
      if (!last || this.cfg.loop) { this.active = null; this.next(); }
    }
  };

  /* ---------- interaction ---------- */
  Constellation.prototype.bind = function () {
    var self = this, el = this.drag, ia = this.cfg.interaction, last = null;
    function touched() { self.lastInteraction = self.now(); self.root.classList.add('is-touched'); self.dirty = true; self.start(); }

    if (el) {
      el.addEventListener('pointerdown', function (e) {
        if (e.button != null && e.button !== 0) return;
        self.press = { x: e.clientX, y: e.clientY, t: performance.now() };
        self.pointer = null;
        if (!ia.drag) return;
        self.dragging = true;
        self.vx = self.vy = 0; self.rxTarget = null;
        last = { x: e.clientX, y: e.clientY, t: performance.now() };
        el.setAttribute('data-dragging', 'true');
        if (el.setPointerCapture) { try { el.setPointerCapture(e.pointerId); } catch (err) { /* not capturable */ } }
        touched();
      });
      el.addEventListener('pointermove', function (e) {
        if (!self.dragging || !last) { self.hover(e); return; }
        var now = performance.now(), dt = Math.max((now - last.t) / 1000, 1 / 240);
        var dyaw = (e.clientX - last.x) / self.S * ia.dragYaw, dpitch = (e.clientY - last.y) / self.S * ia.dragPitch;
        self.ry += dyaw;
        self.rx = clamp(self.rx + dpitch, -self.cfg.camera.maxTilt, self.cfg.camera.maxTilt);
        self.vy = self.vy * 0.5 + (dyaw / dt) * 0.5;
        self.vx = self.vx * 0.5 + (dpitch / dt) * 0.5;
        last = { x: e.clientX, y: e.clientY, t: now };
        touched();
      });
      function release(e) {
        var press = self.press; self.press = null;
        if (self.dragging) {
          self.dragging = false; last = null;
          el.setAttribute('data-dragging', 'false');
          self.vy = clamp(self.vy, -8, 8); self.vx = clamp(self.vx, -6, 6);
          if (el.releasePointerCapture && e && e.pointerId != null) { try { el.releasePointerCapture(e.pointerId); } catch (err) { /* released */ } }
        }
        // A press that barely moved is a click: send a shockwave from that point.
        if (press && e && e.type === 'pointerup' && Math.hypot(e.clientX - press.x, e.clientY - press.y) < 6 && performance.now() - press.t < 500) {
          var r = self.root.getBoundingClientRect();
          self.burst(e.clientX - r.left, e.clientY - r.top);
        }
        touched();
      }
      el.addEventListener('pointerup', release);
      el.addEventListener('pointercancel', release);
      el.addEventListener('lostpointercapture', function (e) { if (self.dragging) release(e); });
      el.addEventListener('pointerleave', function () { self.pointer = null; });

      el.addEventListener('keydown', function (e) {
        if (!ia.keys) return;
        var cam = self.cfg.camera, tilt = self.rxTarget == null ? self.rx : self.rxTarget;
        switch (e.key) {
          case 'ArrowLeft':  self.vy -= 1.8; break;
          case 'ArrowRight': self.vy += 1.8; break;
          case 'ArrowUp':    self.rxTarget = clamp(tilt - 0.22, -cam.maxTilt, cam.maxTilt); break;
          case 'ArrowDown':  self.rxTarget = clamp(tilt + 0.22, -cam.maxTilt, cam.maxTilt); break;
          case 'Home':       self.ry = cam.startYaw; self.rx = cam.restTilt; self.vx = self.vy = 0; self.rxTarget = null; break;
          case 'Enter': case ' ': self.burst(self.W / 2, self.H / 2); break;
          default: return;
        }
        e.preventDefault();
        self.vy = clamp(self.vy, -8, 8);
        touched();
      });
    }

    function onResize() { if (self.measure()) { self.applySize(); self.start(); } }
    if ('ResizeObserver' in window) new ResizeObserver(onResize).observe(this.root);
    else window.addEventListener('resize', onResize);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) { self.visible = entries[entries.length - 1].isIntersecting; if (self.visible) self.start(); else self.stop(); }, { threshold: 0 }).observe(this.root);
    }
    document.addEventListener('visibilitychange', function () { if (document.hidden) self.stop(); else self.start(); });
    if (reduceMotion && reduceMotion.addEventListener) reduceMotion.addEventListener('change', function (e) { self.reduced = e.matches; self.dirty = true; self.start(); });
  };

  Constellation.prototype.hover = function (e) {
    if (!this.cfg.interaction.hover.enabled || this.reduced || e.pointerType === 'touch') return;
    var r = this.root.getBoundingClientRect();
    var x = e.clientX - r.left, y = e.clientY - r.top, now = performance.now();
    if (this.pointer) {
      var dt = Math.max((now - this.ptrT) / 1000, 1 / 240);
      this.ptrVel.x = this.ptrVel.x * 0.4 + ((x - this.pointer.x) / dt) * 0.6;
      this.ptrVel.y = this.ptrVel.y * 0.4 + ((y - this.pointer.y) / dt) * 0.6;
    } else { this.ptrVel.x = this.ptrVel.y = 0; }
    this.pointer = { x: x, y: y }; this.ptrT = now;
    this.start();
  };

  // A shockwave from a canvas point: an outward pop, then a ring that pushes stars as it passes.
  Constellation.prototype.burst = function (x, y) {
    var ck = this.cfg.interaction.click;
    if (!ck.enabled || this.reduced) return;
    this.waves.push({ x: x, y: y, t: this.now(), popped: false });
    this.lastInteraction = this.now();
    this.root.classList.add('is-touched');
    this.start();
  };

  /* ---------- the loop ---------- */
  Constellation.prototype.start = function () {
    if (this.raf || !this.visible || document.hidden) return;
    var self = this;
    this.tPrev = null;
    this.raf = requestAnimationFrame(function step(ts) {
      self.raf = 0;
      if (!self.visible || document.hidden) return;
      if (self.frame(ts)) self.raf = requestAnimationFrame(step);
    });
  };
  Constellation.prototype.stop = function () { if (this.raf) { cancelAnimationFrame(this.raf); this.raf = 0; } };

  Constellation.prototype.frame = function (ts) {
    var t = ts / 1000 - this.t0;
    var dt = this.tPrev == null ? 0 : clamp(t - this.tPrev, 0, 0.05);
    this.tPrev = t;
    var mo = this.cfg.motion, cam = this.cfg.camera, ia = this.cfg.interaction;
    var sinceTouch = t - this.lastInteraction;
    var moving = this.dragging;

    this.runScene(t);

    if (!this.dragging) {
      var damp = Math.exp(-ia.inertia * dt);
      this.vy *= damp; this.vx *= damp;
      if (Math.abs(this.vy) < 0.004) this.vy = 0; else moving = true;
      if (Math.abs(this.vx) < 0.004) this.vx = 0; else moving = true;
      this.ry += this.vy * dt;
      this.rx = clamp(this.rx + this.vx * dt, -cam.maxTilt, cam.maxTilt);
      if (this.rxTarget != null) {
        this.rx += (this.rxTarget - this.rx) * (1 - Math.exp(-8 * dt));
        if (Math.abs(this.rxTarget - this.rx) < 0.002) { this.rx = this.rxTarget; this.rxTarget = null; }
        moving = true;
      }
      if (!this.reduced && sinceTouch > 1.2) {
        var ramp = clamp((sinceTouch - 1.2) / 2, 0, 1);
        this.ry += mo.spin * ramp * dt;
        if (this.rxTarget == null) { var rest = cam.restTilt + mo.nod * Math.sin(t * 0.35); this.rx += (rest - this.rx) * (1 - Math.exp(-0.8 * ramp * dt)); }
        moving = true;
      }
    }
    if (this.disturbed || this.waves.length) moving = true;
    if (!this.reduced) moving = true;
    if (moving || this.dirty) { this.draw(t, dt); this.dirty = false; }
    return moving;
  };

  Constellation.prototype.draw = function (t, dt) {
    var ctx = this.ctx, W = this.W, H = this.H, S = this.S, dpr = this.dpr, cfg = this.cfg;
    var look = cfg.look, mo = cfg.motion, ia = cfg.interaction, o = ia.hover, ck = ia.click;
    dt = dt || 0;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var Rpx = S * cfg.camera.radius, cX = W / 2, cY = H / 2, f = cfg.camera.focal;
    var cy = Math.cos(this.ry), sy = Math.sin(this.ry), cx = Math.cos(this.rx), sx = Math.sin(this.rx);
    var still = this.reduced;

    // backdrop stars with a little parallax
    var px = Math.sin(this.ry) * 0.05 * S, py = Math.sin(this.rx) * 0.05 * S;
    ctx.fillStyle = '#ffffff';
    for (var i = 0; i < this.stars.length; i++) {
      var st = this.stars[i], tw = still ? 1 : 0.7 + 0.3 * Math.sin(t * st.ts + st.tw);
      ctx.globalAlpha = st.a * tw;
      ctx.beginPath(); ctx.arc(cX + st.x * W * 0.5 + px * st.depth, cY + st.y * H * 0.5 + py * st.depth, st.r, 0, Math.PI * 2); ctx.fill();
    }

    ctx.globalCompositeOperation = 'lighter';
    if (this.halo && look.halo.alpha > 0) { var hd = Rpx * look.halo.scale; ctx.globalAlpha = look.halo.alpha; ctx.drawImage(this.halo, cX - hd / 2, cY - hd / 2, hd, hd); }

    // pointer physics (see hover): speed-driven reach, force and wake
    var ptr = this.dragging ? null : this.pointer;
    var bleed = Math.exp(-6 * dt);
    this.ptrVel.x *= bleed; this.ptrVel.y *= bleed;
    var pvx = this.ptrVel.x / Rpx, pvy = this.ptrVel.y / Rpx, spd = Math.sqrt(pvx * pvx + pvy * pvy);
    var quick = Math.min(spd / o.fullSpeed, 1);
    var hr = o.radius * S * (1 + o.reach * quick), hr2 = hr * hr;
    var accel = (o.force + o.speedGain * spd) * dt, wake = o.wake * quick;
    var mdx = spd > 0 ? pvx / spd : 0, mdy = spd > 0 ? pvy / spd : 0;

    // click shockwaves: an outward pop, then a travelling ring
    var waves = this.waves, alive = [];
    for (var w = 0; w < waves.length; w++) {
      var wv = waves[w], age = t - wv.t;
      if (age <= ck.life) { wv.age = age; wv.r = ck.ringSpeed * S * age; wv.band = ck.ringWidth * S * (1 + age); wv.k = 1 - age / ck.life; alive.push(wv); }
    }
    this.waves = alive;
    var popR = ck.radius * S, popR2 = popR * popR;

    var damp = Math.exp(-mo.damping * dt), spring = mo.spring * dt;
    var fdamp = Math.exp(-mo.freeDamping * dt), fspring = mo.freeSpring * dt;
    var maxV2 = mo.maxSpeed * mo.maxSpeed;
    var disturbed = false, blinkOn = (t % 1) < 0.6;

    var sprites = this.sprites, list = this.particles;
    for (var j = 0; j < list.length; j++) {
      var p = list[j], isFree = !p.key;
      // integrate toward home (or the free resting place)
      var hx = isFree ? p.fx : p.hx, hy = isFree ? p.fy : p.hy, hz = isFree ? p.fz : p.hz;
      var kS = isFree ? fspring : spring, kD = isFree ? fdamp : damp;
      p.vx = (p.vx + (hx - p.x) * kS) * kD; p.vy = (p.vy + (hy - p.y) * kS) * kD; p.vz = (p.vz + (hz - p.z) * kS) * kD;
      var v2 = p.vx * p.vx + p.vy * p.vy + p.vz * p.vz;
      if (v2 > maxV2) { var vs = mo.maxSpeed / Math.sqrt(v2); p.vx *= vs; p.vy *= vs; p.vz *= vs; v2 = maxV2; }
      p.x += p.vx * dt; p.y += p.vy * dt; p.z += p.vz * dt;
      var dx0 = p.x - hx, dy0 = p.y - hy, dz0 = p.z - hz, off2 = dx0 * dx0 + dy0 * dy0 + dz0 * dz0;
      if (v2 > 1e-6 || off2 > 1e-5) disturbed = true;

      var x = p.x, y = p.y, z = p.z;
      if (!still && look.twinkle) { var jw = look.jitter; x += Math.sin(t * 0.9 + p.jx) * jw; y += Math.sin(t * 1.1 + p.jy) * jw; z += Math.sin(t * 0.7 + p.jz) * jw * 2; }
      var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;
      var y2 = y * cx - z1 * sx, z2 = y * sx + z1 * cx;
      var per = f / (f + z2);
      var X = cX + x1 * Rpx * per, Y = cY + y2 * Rpx * per;

      var bright = still || !look.twinkle ? 1 : (1 - p.twDepth) + p.twDepth * (0.5 + 0.5 * Math.sin(t * p.twSpeed + p.twPhase));
      var ix = 0, iy = 0;   // screen-plane impulse to apply, half-size units

      if (ptr && !isFree) {
        var ddx = X - ptr.x, ddy = Y - ptr.y, d2 = ddx * ddx + ddy * ddy;
        if (d2 < hr2 && d2 > 0) {
          var dist = Math.sqrt(d2), fall = 1 - dist / hr;
          var dirx = ddx / dist + mdx * wake, diry = ddy / dist + mdy * wake, dl = Math.sqrt(dirx * dirx + diry * diry) || 1;
          var imp = accel * fall * fall / dl;
          ix += dirx * imp; iy += diry * imp;
        }
      }
      for (var q = 0; q < alive.length; q++) {
        var wq = alive[q], wdx = X - wq.x, wdy = Y - wq.y, wd2 = wdx * wdx + wdy * wdy, wd = Math.sqrt(wd2) || 0.001;
        if (!wq.popped && wd2 < popR2) { var pf = ck.force * (1 - wd / popR); ix += wdx / wd * pf; iy += wdy / wd * pf; }
        if (ck.ring) {
          var ringD = Math.abs(wd - wq.r);
          if (ringD < wq.band) { var rf = ck.ringForce * (1 - ringD / wq.band) * wq.k * dt * 12; ix += wdx / wd * rf; iy += wdy / wd * rf; bright += ck.flash * (1 - ringD / wq.band) * wq.k; }
        }
      }
      if (ix || iy) {
        p.vx += ix * cy + iy * sx * sy; p.vy += iy * cx; p.vz += ix * sy - iy * sx * cy;   // inverse of turn-then-tilt
        disturbed = true;
      }
      if (v2 > 0 || off2 > 0) bright += Math.min(Math.sqrt(v2) * 0.4 + Math.sqrt(off2) * 0.8, 0.7);

      var shade = 0.55 + 0.45 * clamp(0.5 - z2 * 0.5, 0, 1);
      var alpha = p.alpha * bright * shade;
      if (p.blink && !blinkOn) alpha = 0;
      if (alpha <= 0.003) continue;
      var dia = p.size * S * per * (0.85 + 0.15 * bright);
      ctx.globalAlpha = Math.min(alpha, 1);
      ctx.drawImage(sprites[p.color], X - dia / 2, Y - dia / 2, dia, dia);
    }
    for (var q2 = 0; q2 < alive.length; q2++) alive[q2].popped = true;
    if (ptr && quick > 0) this.vy += pvx * o.torque * quick * dt;
    this.disturbed = disturbed;
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
  };

  /* ======================================================================
   * Boot + public API
   * ==================================================================== */
  var instances = [];
  function init(scope) {
    var roots = (scope || document).querySelectorAll('[data-constellation]:not([data-constellation-ready])');
    for (var i = 0; i < roots.length; i++) { var c = new Constellation(roots[i]); if (c.ctx) instances.push(c); }
    return instances;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();

  window.Constellation = window.Constellation || {
    init: init,
    instances: instances,
    registerSource: registerSource,
    sources: sources,
    generators: generators,
    defaults: DEFAULTS,
    sceneDefaults: SCENE_DEFAULTS
  };
})();
