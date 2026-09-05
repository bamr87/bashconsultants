/*!
 * bash-mark.js — the BASH B mark as an interactive, rotating cloud of light.
 *
 * What it does
 *   Reads the mark's outline from the inline SVG that _includes/brand/mark-shape.svg
 *   renders beside the canvas, scatters a few thousand glowing particles inside that
 *   outline (denser and brighter along the edge), extrudes them into a thin slab,
 *   and draws the slab in 3D with additive blending. It turns on its own, follows a
 *   pointer drag with inertia, and answers the arrow keys for keyboard users.
 *
 * Why it is built this way
 *   - No dependencies: a 2D canvas, Path2D hit-testing, requestAnimationFrame.
 *   - Deterministic: a seeded PRNG, so the constellation is identical on every load.
 *   - Progressive: without JS (or canvas) the static mark stays visible; under
 *     prefers-reduced-motion the mark renders once and only moves when asked.
 *
 * Markup contract (see _includes/bash-mark.html)
 *   [data-bash-mark]              root; optional data-particles / data-depth /
 *                                 data-spin / data-seed / data-colors="#hex,#hex,#hex"
 *     canvas                      drawing surface
 *     button.bash-mark__drag      drag surface and keyboard target (carries the aria-label)
 *     svg[data-bash-mark-shape]   geometry: path[data-shape=fill] and path[data-shape=hole]
 *                                 inside an optional <g transform="translate(x,y)">
 *
 * Interaction
 *   Drag horizontally to turn, vertically to tilt; a flick keeps spinning and eases
 *   back into the idle rotation. Arrow left/right nudge the turn, arrow up/down the
 *   tilt, Home resets. Touch drags that are mostly vertical still scroll the page.
 */
(function () {
  'use strict';

  var DEFAULTS = {
    particles: 3600,   // at a 400px canvas; scaled by area and clamped below
    depth: 0.26,       // slab thickness as a fraction of the mark's half-size
    spin: 0.3,         // idle rotation, radians per second
    seed: 20260905,
    edgeBand: 14,      // SVG units either side of the outline that count as "edge"
    edgeShare: 0.46,   // share of particles placed on the edge band
    focal: 4,          // perspective strength: camera distance in half-sizes
    restTilt: 0.16,    // idle tilt about X so the slab's thickness shows
    startYaw: -0.55,   // initial turn so the mark loads three-quarter on
    maxTilt: 1.2
  };
  var MIN_PARTICLES = 900, MAX_PARTICLES = 4200, REFERENCE_SIZE = 400;
  var SPRITE = 64, WHITE = [255, 255, 255];

  var reduceMotion = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  /* ---------- helpers ---------- */

  // mulberry32: small, fast, and good enough for scatter — seeded so every
  // visitor sees the same constellation and screenshots are reproducible.
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

  function hexToRgb(hex) {
    var m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(String(hex).trim());
    if (!m) return null;
    var h = m[1];
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function mix(a, b, t) {
    return [
      Math.round(a[0] + (b[0] - a[0]) * t),
      Math.round(a[1] + (b[1] - a[1]) * t),
      Math.round(a[2] + (b[2] - a[2]) * t)
    ];
  }

  function rgba(c, a) { return 'rgba(' + c[0] + ',' + c[1] + ',' + c[2] + ',' + a + ')'; }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }
  function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

  function pick(weights, r) {
    var acc = 0;
    for (var i = 0; i < weights.length; i++) { acc += weights[i]; if (r < acc) return i; }
    return weights.length - 1;
  }

  // A soft glow: a white-hot core that falls off into the particle's color.
  // One sprite per color, drawn scaled — far cheaper than a gradient per particle.
  function makeSprite(rgb) {
    var c = document.createElement('canvas');
    c.width = c.height = SPRITE;
    var g = c.getContext('2d');
    var r = SPRITE / 2;
    var grad = g.createRadialGradient(r, r, 0, r, r, r);
    grad.addColorStop(0.00, rgba(WHITE, 1));
    grad.addColorStop(0.16, rgba(mix(rgb, WHITE, 0.55), 0.9));
    grad.addColorStop(0.40, rgba(rgb, 0.32));
    grad.addColorStop(1.00, rgba(rgb, 0));
    g.fillStyle = grad;
    g.fillRect(0, 0, SPRITE, SPRITE);
    return c;
  }

  // A wide, coreless wash of color drawn once behind the mark, so the cloud
  // sits in a faint nebula instead of on flat black.
  function makeHalo(rgb) {
    var c = document.createElement('canvas');
    c.width = c.height = SPRITE;
    var g = c.getContext('2d');
    var r = SPRITE / 2;
    var grad = g.createRadialGradient(r, r, 0, r, r, r);
    grad.addColorStop(0.00, rgba(rgb, 0.55));
    grad.addColorStop(0.45, rgba(rgb, 0.18));
    grad.addColorStop(1.00, rgba(rgb, 0));
    g.fillStyle = grad;
    g.fillRect(0, 0, SPRITE, SPRITE);
    return c;
  }

  /* ---------- geometry: sample the SVG mark ---------- */

  function readShape(root) {
    if (typeof Path2D === 'undefined') return null;
    var svg = root.querySelector('[data-bash-mark-shape]');
    var fillEl = svg && svg.querySelector('[data-shape="fill"]');
    if (!fillEl) return null;
    var holeEl = svg.querySelector('[data-shape="hole"]');

    var vb = (svg.getAttribute('viewBox') || '0 0 512 512').split(/[\s,]+/).map(Number);
    var tx = 0, ty = 0;
    var tr = fillEl.parentNode && fillEl.parentNode.getAttribute ? fillEl.parentNode.getAttribute('transform') : null;
    var m = tr && /translate\(\s*([-+\d.eE]+)[\s,]+([-+\d.eE]+)\s*\)/.exec(tr);
    if (m) { tx = parseFloat(m[1]); ty = parseFloat(m[2]); }

    return {
      x: vb[0], y: vb[1], w: vb[2], h: vb[3], tx: tx, ty: ty,
      fill: new Path2D(fillEl.getAttribute('d')),
      hole: holeEl ? new Path2D(holeEl.getAttribute('d')) : null
    };
  }

  function buildParticles(shape, opts, rand) {
    var probe = document.createElement('canvas');
    probe.width = Math.ceil(shape.w); probe.height = Math.ceil(shape.h);
    var ctx = probe.getContext('2d');
    if (!ctx || !ctx.isPointInStroke) return null;
    ctx.lineWidth = opts.edgeBand;
    ctx.lineJoin = 'round';

    // The group's translate() is a plain offset, so test in path space rather
    // than relying on how each browser applies the CTM to Path2D hit-tests.
    function inFill(x, y) {
      x -= shape.tx; y -= shape.ty;
      if (!ctx.isPointInPath(shape.fill, x, y)) return false;
      return !(shape.hole && ctx.isPointInPath(shape.hole, x, y));
    }
    function onEdge(x, y) {
      x -= shape.tx; y -= shape.ty;
      if (ctx.isPointInStroke(shape.fill, x, y)) return true;
      return shape.hole ? ctx.isPointInStroke(shape.hole, x, y) : false;
    }

    // Bounding box of the drawn mark, from a coarse scan of the viewBox, so the
    // cloud is centered on the ink rather than on the SVG page.
    var step = 4, minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (var sy = shape.y; sy <= shape.y + shape.h; sy += step) {
      for (var sx = shape.x; sx <= shape.x + shape.w; sx += step) {
        if (inFill(sx, sy) || onEdge(sx, sy)) {
          if (sx < minX) minX = sx;
          if (sx > maxX) maxX = sx;
          if (sy < minY) minY = sy;
          if (sy > maxY) maxY = sy;
        }
      }
    }
    if (minX === Infinity) return null;
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    var R = Math.max(maxX - minX, maxY - minY) / 2;
    var bx = minX - step, by = minY - step, bw = maxX - minX + 2 * step, bh = maxY - minY + 2 * step;

    var count = opts.particles;
    var nEdge = Math.round(count * opts.edgeShare);
    var guard = count * 80;

    function sample(edge) {
      while (guard-- > 0) {
        var x = bx + rand() * bw, y = by + rand() * bh;
        var e = onEdge(x, y);
        if (edge ? e : (!e && inFill(x, y))) return [x, y];
      }
      return null;
    }

    var weightsEdge = [0.56, 0.22, 0.17, 0.05];   // white, accent 1, accent 2, accent 3
    var weightsInner = [0.22, 0.12, 0.56, 0.10];
    var list = [];

    for (var i = 0; i < count; i++) {
      var edge = i < nEdge;
      var p = sample(edge);
      if (!p) break;
      var x = (p[0] - cx) / R, y = (p[1] - cy) / R;
      var z = (rand() - 0.5) * opts.depth;
      var dust = edge && rand() < 0.09;
      if (dust) {                                   // loose light just outside the outline
        var ang = rand() * Math.PI * 2, dist = 0.03 + rand() * 0.14;
        x += Math.cos(ang) * dist; y += Math.sin(ang) * dist; z *= 1.6;
      }
      var size = edge ? 0.010 + rand() * 0.012 : 0.006 + rand() * 0.007;
      if (dust) size *= 0.7;
      var sparkler = edge && rand() < 0.05;          // a few bright, fast-twinkling stars
      if (sparkler) size *= 1.9;
      var sa = rand() * Math.PI * 2, sd = 0.9 + rand() * 0.9;   // intro scatter
      list.push({
        x: x, y: y, z: z,
        sx: x + Math.cos(sa) * sd, sy: y + Math.sin(sa) * sd, sz: z + (rand() - 0.5) * 1.5,
        delay: rand() * 0.45,
        color: pick(edge ? weightsEdge : weightsInner, rand()),
        size: size,
        alpha: sparkler ? 1 : dust ? 0.4 : edge ? 0.9 : 0.55,
        twSpeed: sparkler ? 3 + rand() * 3 : 0.8 + rand() * 1.6,
        twPhase: rand() * Math.PI * 2,
        twDepth: sparkler ? 0.7 : 0.28,
        jx: rand() * Math.PI * 2, jy: rand() * Math.PI * 2, jz: rand() * Math.PI * 2,
        jAmp: 0.006 + rand() * 0.01
      });
    }
    return list;
  }

  function buildStars(rand, n) {
    var stars = [];
    for (var i = 0; i < n; i++) {
      stars.push({
        x: rand() * 2 - 1, y: rand() * 2 - 1,        // canvas fractions, center = 0
        r: 0.4 + rand() * 1.1,
        a: 0.25 + rand() * 0.6,
        tw: rand() * Math.PI * 2, ts: 0.3 + rand() * 0.8,
        depth: 0.3 + rand() * 0.7                    // parallax factor
      });
    }
    return stars;
  }

  /* ---------- the component ---------- */

  function BashMark(root) {
    this.root = root;
    this.canvas = root.querySelector('canvas');
    this.drag = root.querySelector('.bash-mark__drag') || root.querySelector('button');
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    if (!this.ctx) return;

    var d = root.dataset;
    this.opts = {
      particles: parseInt(d.particles, 10) || DEFAULTS.particles,
      depth: parseFloat(d.depth) || DEFAULTS.depth,
      spin: d.spin != null && d.spin !== '' && !isNaN(parseFloat(d.spin)) ? parseFloat(d.spin) : DEFAULTS.spin,
      seed: parseInt(d.seed, 10) || DEFAULTS.seed,
      edgeBand: DEFAULTS.edgeBand, edgeShare: DEFAULTS.edgeShare,
      focal: DEFAULTS.focal, restTilt: DEFAULTS.restTilt, startYaw: DEFAULTS.startYaw, maxTilt: DEFAULTS.maxTilt
    };

    var shape = readShape(root);
    if (!shape) return;

    // Scale the particle budget with the drawn area so phones do less work.
    this.size = 0; this.dpr = 1;
    this.measure();
    var scale = this.size > 0 ? Math.pow(this.size / REFERENCE_SIZE, 2) : 1;
    this.opts.particles = Math.round(clamp(this.opts.particles * scale, MIN_PARTICLES, MAX_PARTICLES));

    var rand = mulberry32(this.opts.seed);
    var accents = (d.colors || '#ffe900,#376986,#a11111').split(',').map(hexToRgb).filter(Boolean);
    while (accents.length < 3) accents.push(WHITE);
    this.palette = [WHITE].concat(accents.slice(0, 3));
    this.sprites = this.palette.map(makeSprite);
    this.halo = makeHalo(this.palette[2]);

    this.particles = buildParticles(shape, this.opts, rand);
    if (!this.particles || !this.particles.length) return;
    this.stars = buildStars(rand, 110);

    this.t0 = performance.now() / 1000;
    this.tPrev = null;
    this.rx = this.opts.restTilt; this.ry = this.opts.startYaw;
    this.vx = 0; this.vy = 0;
    this.rxTarget = null;
    this.dragging = false;
    this.lastInteraction = -Infinity;
    this.reduced = !!(reduceMotion && reduceMotion.matches);
    this.visible = true;
    this.dirty = true;
    this.raf = 0;

    this.applySize();
    this.bind();
    root.classList.add('is-live');
    root.setAttribute('data-bash-mark-ready', 'true');
    this.start();
  }

  BashMark.prototype.now = function () { return performance.now() / 1000 - this.t0; };

  BashMark.prototype.measure = function () {
    var rect = this.root.getBoundingClientRect();
    var size = Math.round(Math.min(rect.width, rect.height) || rect.width || 0);
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var changed = size !== this.size || dpr !== this.dpr;
    this.size = size; this.dpr = dpr;
    return changed;
  };

  BashMark.prototype.applySize = function () {
    var px = Math.max(1, Math.round(this.size * this.dpr));
    if (this.canvas.width !== px || this.canvas.height !== px) {
      this.canvas.width = px; this.canvas.height = px;
    }
    this.dirty = true;
  };

  BashMark.prototype.bind = function () {
    var self = this, el = this.drag;
    var last = null;

    function touched() {
      self.lastInteraction = self.now();
      self.root.classList.add('is-touched');
      self.dirty = true;
      self.start();
    }

    if (el) {
      el.addEventListener('pointerdown', function (e) {
        if (e.button != null && e.button !== 0) return;
        self.dragging = true;
        self.vx = self.vy = 0; self.rxTarget = null;
        last = { x: e.clientX, y: e.clientY, t: performance.now() };
        el.setAttribute('data-dragging', 'true');
        if (el.setPointerCapture) { try { el.setPointerCapture(e.pointerId); } catch (err) { /* not capturable */ } }
        touched();
      });

      el.addEventListener('pointermove', function (e) {
        if (!self.dragging || !last) return;
        var now = performance.now();
        var dt = Math.max((now - last.t) / 1000, 1 / 240);
        var dyaw = (e.clientX - last.x) / self.size * 2.8;
        var dpitch = (e.clientY - last.y) / self.size * 2.0;
        self.ry += dyaw;
        self.rx = clamp(self.rx + dpitch, -self.opts.maxTilt, self.opts.maxTilt);
        // Smoothed release velocity, so a flick keeps the mark spinning.
        self.vy = self.vy * 0.5 + (dyaw / dt) * 0.5;
        self.vx = self.vx * 0.5 + (dpitch / dt) * 0.5;
        last = { x: e.clientX, y: e.clientY, t: now };
        touched();
      });

      function release(e) {
        if (!self.dragging) return;
        self.dragging = false;
        last = null;
        el.setAttribute('data-dragging', 'false');
        self.vy = clamp(self.vy, -8, 8); self.vx = clamp(self.vx, -6, 6);
        if (el.releasePointerCapture && e && e.pointerId != null) { try { el.releasePointerCapture(e.pointerId); } catch (err) { /* already released */ } }
        touched();
      }
      el.addEventListener('pointerup', release);
      el.addEventListener('pointercancel', release);
      el.addEventListener('lostpointercapture', release);

      el.addEventListener('keydown', function (e) {
        var tilt = self.rxTarget == null ? self.rx : self.rxTarget;
        switch (e.key) {
          case 'ArrowLeft':  self.vy -= 1.8; break;
          case 'ArrowRight': self.vy += 1.8; break;
          case 'ArrowUp':    self.rxTarget = clamp(tilt - 0.22, -self.opts.maxTilt, self.opts.maxTilt); break;
          case 'ArrowDown':  self.rxTarget = clamp(tilt + 0.22, -self.opts.maxTilt, self.opts.maxTilt); break;
          case 'Home':       self.ry = self.opts.startYaw; self.rx = self.opts.restTilt; self.vx = self.vy = 0; self.rxTarget = null; break;
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
      new IntersectionObserver(function (entries) {
        self.visible = entries[entries.length - 1].isIntersecting;
        if (self.visible) self.start(); else self.stop();
      }, { threshold: 0 }).observe(this.root);
    }
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) self.stop(); else self.start();
    });
    if (reduceMotion && reduceMotion.addEventListener) {
      reduceMotion.addEventListener('change', function (e) { self.reduced = e.matches; self.dirty = true; self.start(); });
    }
  };

  BashMark.prototype.start = function () {
    if (this.raf || !this.visible || document.hidden) return;
    var self = this;
    this.tPrev = null;                      // never integrate across a pause
    this.raf = requestAnimationFrame(function step(ts) {
      self.raf = 0;
      if (!self.visible || document.hidden) return;
      if (self.frame(ts)) self.raf = requestAnimationFrame(step);
    });
  };

  BashMark.prototype.stop = function () {
    if (this.raf) { cancelAnimationFrame(this.raf); this.raf = 0; }
  };

  // Advance the simulation and draw. Returns false once nothing is left to
  // animate (reduced motion, at rest), so the loop can idle until the next input.
  BashMark.prototype.frame = function (ts) {
    var t = ts / 1000 - this.t0;
    var dt = this.tPrev == null ? 0 : clamp(t - this.tPrev, 0, 0.05);
    this.tPrev = t;

    var intro = this.reduced ? 0 : 1.6;
    var sinceTouch = t - this.lastInteraction;
    var moving = this.dragging || (intro > 0 && t < intro + 0.5);

    if (!this.dragging) {
      // Inertia after a flick or an arrow key.
      var damp = Math.exp(-2.4 * dt);
      this.vy *= damp; this.vx *= damp;
      if (Math.abs(this.vy) < 0.004) this.vy = 0; else moving = true;
      if (Math.abs(this.vx) < 0.004) this.vx = 0; else moving = true;
      this.ry += this.vy * dt;
      this.rx = clamp(this.rx + this.vx * dt, -this.opts.maxTilt, this.opts.maxTilt);

      if (this.rxTarget != null) {          // arrow up/down ease to a target tilt
        this.rx += (this.rxTarget - this.rx) * (1 - Math.exp(-8 * dt));
        if (Math.abs(this.rxTarget - this.rx) < 0.002) { this.rx = this.rxTarget; this.rxTarget = null; }
        moving = true;
      }

      if (!this.reduced && sinceTouch > 1.2) {
        // Ease back into the idle turn, with a slow nod that shows the slab's depth.
        var ramp = clamp((sinceTouch - 1.2) / 2, 0, 1);
        this.ry += this.opts.spin * ramp * dt;
        if (this.rxTarget == null) {
          var rest = this.opts.restTilt + 0.08 * Math.sin(t * 0.35);
          this.rx += (rest - this.rx) * (1 - Math.exp(-0.8 * ramp * dt));
        }
        moving = true;
      }
    }

    if (!this.reduced) moving = true;       // twinkle keeps the normal mode alive
    if (moving || this.dirty) { this.draw(t, intro); this.dirty = false; }
    return moving;
  };

  BashMark.prototype.draw = function (t, intro) {
    var ctx = this.ctx, S = this.size, dpr = this.dpr;
    var W = this.canvas.width, H = this.canvas.height;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.clearRect(0, 0, W, H);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    var Rpx = S * 0.40, cX = S / 2, cY = S / 2;
    var f = this.opts.focal;
    var cy = Math.cos(this.ry), sy = Math.sin(this.ry);
    var cx = Math.cos(this.rx), sx = Math.sin(this.rx);
    var still = this.reduced;

    // Backdrop stars, with a touch of parallax so the turn reads as depth.
    var px = Math.sin(this.ry) * 0.05 * S, py = Math.sin(this.rx) * 0.05 * S;
    ctx.fillStyle = '#ffffff';
    for (var i = 0; i < this.stars.length; i++) {
      var st = this.stars[i];
      var tw = still ? 1 : 0.7 + 0.3 * Math.sin(t * st.ts + st.tw);
      ctx.globalAlpha = st.a * tw;
      ctx.beginPath();
      ctx.arc(cX + st.x * S * 0.5 + px * st.depth, cY + st.y * S * 0.5 + py * st.depth, st.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // The mark: additive sprites, so overlapping light adds up and draw order
    // does not matter — no depth sort needed.
    ctx.globalCompositeOperation = 'lighter';
    var haloD = Rpx * 2.6;
    ctx.globalAlpha = 0.16;
    ctx.drawImage(this.halo, cX - haloD / 2, cY - haloD / 2, haloD, haloD);
    var sprites = this.sprites, list = this.particles;
    for (var j = 0; j < list.length; j++) {
      var p = list[j];
      var x = p.x, y = p.y, z = p.z;
      if (!still) {
        var w = p.jAmp;
        x += Math.sin(t * 0.9 + p.jx) * w;
        y += Math.sin(t * 1.1 + p.jy) * w;
        z += Math.sin(t * 0.7 + p.jz) * w * 2;
      }
      var k = 1;
      if (intro > 0 && t < intro + p.delay) {   // fly in from the scatter position
        k = easeOutCubic(clamp((t - p.delay) / intro, 0, 1));
        x = p.sx + (x - p.sx) * k; y = p.sy + (y - p.sy) * k; z = p.sz + (z - p.sz) * k;
      }
      var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;       // turn about Y
      var y2 = y * cx - z1 * sx, z2 = y * sx + z1 * cx;      // tilt about X
      var per = f / (f + z2);
      var X = cX + x1 * Rpx * per, Y = cY + y2 * Rpx * per;
      var bright = still ? 1 : (1 - p.twDepth) + p.twDepth * (0.5 + 0.5 * Math.sin(t * p.twSpeed + p.twPhase));
      var shade = 0.55 + 0.45 * clamp(0.5 - z2 * 0.5, 0, 1);  // nearer is brighter
      var dia = p.size * S * per * (0.85 + 0.15 * bright);
      ctx.globalAlpha = p.alpha * bright * shade * (0.35 + 0.65 * k);
      ctx.drawImage(sprites[p.color], X - dia / 2, Y - dia / 2, dia, dia);
    }
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
  };

  /* ---------- boot ---------- */

  var instances = [];

  function init(scope) {
    var roots = (scope || document).querySelectorAll('[data-bash-mark]:not([data-bash-mark-ready])');
    for (var i = 0; i < roots.length; i++) {
      var mark = new BashMark(roots[i]);
      if (mark.particles) instances.push(mark);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { init(); });
  else init();

  // Exposed for debugging and tests: BashMark.instances[0].ry is the current turn.
  window.BashMark = window.BashMark || { init: init, instances: instances };
})();
