---
title: "Constellation: any shape as interactive light"
sub-title: "A dependency-free particle engine for SVG, text, live terminal sessions, and 3D point clouds, with scenes designed as data"
description: A dependency-free JavaScript particle engine that renders SVG logos, typed terminal text, and 3D point clouds as interactive stars, configured in YAML
excerpt: The engine behind the homepage mark, opened up — sources for SVG, text, live terminal sessions, images, and point clouds; scenes and timelines as YAML; physics you can tune.
author: "Amr Abdel-Motaleb"
layout: default
categories: [partners]
topic: dev
topic_label: "Software & integration"
level: advanced
order: 72
tags: [toolkit, partners, dev, javascript, canvas, animation, front-end, accessibility]
keywords:
  - canvas particle engine
  - particle logo animation javascript
  - svg to particles
  - terminal typing animation
  - point cloud animation javascript
  - dependency-free canvas animation
  - prefers-reduced-motion canvas
  - additive blending particles
lastmod: 2026-09-05T12:00:00.000Z
mermaid: false
sidebar:
  nav: toolkit
permalink: /tools/partners/constellation-engine/
---

The mark on our [homepage](/) is a few thousand stars that turn, scatter under the mouse, and ripple when clicked. The engine underneath is not specific to that logo. It renders any shape it is given as the same interactive light, and the shape, the look, the physics, and the sequence of scenes are all data. This guide is the reference for using it: what it can draw, how a scene is written, how to bring your own geometry, and how to extend it with a source of your own.

It follows the practice's doctrine (see [[The deterministic-first doctrine]]): the geometry is produced by scripts, the randomness is seeded, the scenes are files you can diff, and the model is spent on none of it. It is also the kind of component we wire into the sites we build for clients, so a partner should be able to read this once and ship one.

## How it works

Three ideas carry the whole engine.

- **Sources turn something into targets.** A target is a point in a unit space, where the shape's half-height is 1, plus a look (edge, inner, dust, text, point) and an optional color. A source is a function that produces targets from a Scalable Vector Graphics (SVG) file, a string of text, a scripted terminal session, an image, or a list of 3D points.
- **Every target gets a star, and stars have physics.** A star is a body with a position, a velocity, a spring back to its target, and damping. Stars with no target drift as background dust, and the next scene recruits them. That is what lets a timeline morph the same light from a logo into a line of typed text into a torus.
- **Presentation and interaction are configuration.** Palette, sizes, twinkle, halo, camera, idle spin, drag, keys, the hover physics, and the click shockwave are keys in a YAML file, merged over the engine's defaults.

The renderer is a 2D canvas with additive blending, so overlapping light adds up and no depth sort is needed; each color is one pre-rendered glow sprite, drawn scaled. Rotation is a turn and a tilt with a perspective divide. Pointer impulses are computed on screen and mapped back into the shape's own space through the inverse rotation, so a dent left on the front face turns away with the shape.

## Live scenes

Each stage below is one include and one YAML file. Drag to turn, flick to spin, hover to scatter (faster is harder and wider), click to send a wave, or tab to the stage and use the arrow keys, Home, and Enter.

### An SVG: the mark

{% include constellation.html scene="bash-mark" shape="brand/mark-shape.svg" fallback=site.logo alt="BASH Consulting logo" size="min(100%, 360px)" %}

The scene file is short because the defaults are tuned for a filled glyph. The geometry is an inline SVG the include renders, generated from the brand favicon by `scripts/generate_mark_shape.py` so it can never drift from the mark.

```yaml
# _data/constellations/bash-mark.yml
scene:
  source: svg
  depth: 0.26        # slab thickness, as a fraction of the mark's half-size
  edgeBand: 14       # SVG units either side of the outline that count as edge
  edgeShare: 0.46    # share of stars placed on the edge band
```

### A terminal session, typed live

{% include constellation.html scene="terminal-demo" aspect="16 / 10" size="min(100%, 720px)" particles="3000" %}

The `terminal` source is a scripted shell exchange. Typed lines appear glyph by glyph at a characters-per-second rate with a little human jitter; printed lines land at once. Each character is rasterized once with a monospace font and sampled into a handful of points, and the stars for a new character are recruited from the dust around the stage, so text looks like it condenses out of the field. A blinking cursor follows the typing.

```yaml
# _data/constellations/terminal-demo.yml
look:
  glow: point        # crisp dots read as text better than soft halos
scene:
  source: terminal
  width: 3.4         # stage width in half-sizes (a square is 2.0 across)
  cps: 18            # typing speed; columns default to the longest line
  lines:
    - prompt: "$ "
      type: "bash --version | head -1"
    - print: "GNU bash, version 5.2"
      pause: 0.6
    - prompt: "$ "
      type: "./close-books --period 2026-08"
    - print: "✓ 3 ledgers reconciled"
```

Roles set the color: `prompt` is the first accent, typed `input` the base white, `output` the second accent, `error` the third, and `comment` a dimmer output. Use `role:` on a line to override.

### Text

{% include constellation.html scene="text-demo" size="min(100%, 360px)" %}

Any string, with a font you name, rasterized and sampled. Newlines make lines. The `glow: point` look here gives crisper dots than the soft halo of the mark.

```yaml
scene:
  source: text
  text: "BASH\nConsulting"
  font: "bold 150px system-ui, sans-serif"
  width: 1.9
  density: 5         # sampling grid in raster pixels: lower is denser
```

### A 3D point cloud

{% include constellation.html scene="points-demo" size="min(100%, 360px)" %}

The `points` source takes a list of `[x, y, z]` triples and normalizes them to the unit space. Built-in generators (`sphere`, `torus`, `helix`, `cube`) need no data. For a real model, `scripts/sample_mesh_points.py` samples a Wavefront OBJ surface uniformly by area into a JSON file the scene loads with `url:`.

```yaml
scene:
  source: points
  generator: helix   # or: url: /assets/data/constellations/model.json
  turns: 5
  count: 1800
  depth: 1           # full depth; lower flattens the cloud toward the screen
```

### A timeline that morphs

{% include constellation.html scene="timeline-demo" shape="brand/mark-shape.svg" size="min(100%, 420px)" particles="3000" %}

A `timeline` is a list of scenes. After a scene settles (`settle` seconds), a dynamic source plays to its end, the scene holds for `hold` seconds, and the next scene takes over the same stars. Whatever a scene does not need waits as dust.

```yaml
loop: true
settle: 2.5
timeline:
  - source: svg
    hold: 5
  - source: terminal
    lines:
      - { prompt: "$ ", type: "deploy --env prod" }
      - { print: "✓ 12 services healthy", pause: 1.0 }
    hold: 2.5
  - source: points
    generator: torus
    count: 1600
    hold: 5
```

## Designing a scene

A scene file lives at `_data/constellations/<name>.yml` and is rendered by one include:

```liquid
{% raw %}{% include constellation.html scene="<name>" size="min(100%, 480px)" aspect="16 / 10" %}{% endraw %}
```

The include takes `scene`, `shape` (an include path for an inline SVG), `fallback` and `alt` (the image shown when the engine cannot run), `size`, `aspect`, `label` (the control's accessible name), `hint`, and `particles`. Everything else is the YAML, merged over the engine's defaults. The keys that matter most:

| Key | What it controls |
|---|---|
| `scene` or `timeline` | One scene, or a list of scenes each with an optional `hold` |
| `particles`, `seed` | Pool size at a 400px stage (scaled by area) and the random seed |
| `palette` | `base`, `accents` (three hex colors), and the weights that spread them over edge and inner stars |
| `look` | Size and alpha per star kind (`edge`, `inner`, `dust`, `text`, `glyph`, `point`, `free`), `sparklers`, `twinkle`, `jitter`, `glow` (`soft` or `point`), `halo`, backdrop `stars`, `intro` |
| `camera` | `focal` (perspective), `radius` (shape size on the stage), `restTilt`, `startYaw`, `maxTilt` |
| `motion` | Idle `spin` and `nod`, and the star `spring`, `damping`, and `maxSpeed` |
| `interaction.drag`, `interaction.keys` | Turn the pointer drag and the keyboard on or off |
| `interaction.hover` | `radius`, `reach`, `force`, `speedGain`, `wake`, `torque`: how a moving pointer scatters stars |
| `interaction.click` | `force` and `radius` of the pop, then the `ring` with its `ringSpeed`, `ringWidth`, `ringForce`, `life`, and `flash` |
| `settle`, `hold`, `loop` | Timeline pacing |

Per-source keys sit inside the scene: `depth`, `edgeBand`, `edgeShare`, `dust`, `strokeWidth`, and `fit` for `svg`; `text`, `font`, `width`, `lineHeight`, `density`, `align` for `text`; `lines`, `width`, `cols` (default: the longest line), `cps`, `pause`, `endPause`, `cursor`, `font`, `density` for `terminal`; `points`, `url`, `generator`, `count`, `yUp` for `points`; `image`, `width`, `density`, `threshold` for `image`. The defaults for each are the `SCENE_DEFAULTS` block at the top of `assets/js/constellation.js`, with a comment on every unit.

## Bringing your own geometry

**SVG.** The `svg` source samples any `path`, `rect`, `circle`, `ellipse`, `polygon`, `polyline`, or `line`. Filled shapes are sampled inside, densest along their outline; a shape with `fill="none"` and a stroke is sampled along the stroke at its stroke width, which is how a knot or a line drawing works. Mark an element `data-shape="hole"` to cut it out of the fill, or set the role explicitly with `data-shape="fill"` or `"stroke"`. The only transform honoured is `translate()`, so flatten anything else in your editor before exporting. Point the scene at inline markup with `shape=` on the include, at an element with `svg: "#selector"`, or at a same-origin file with `svg: { url: /path.svg }`.

**Meshes.** Export an OBJ, sample it, and reference the JSON:

```bash
python3 scripts/sample_mesh_points.py model.obj --count 2400 \
  -o assets/data/constellations/model.json
```

**Images.** `image: /path.png` samples a same-origin image by alpha; a cross-origin image taints the canvas and yields nothing, by design of the browser.

## Extending it

Sources are a registry. A new one is a function that returns targets, or a promise of them, or an object with an `update(tPlay)` method for something that changes over time:

```js
Constellation.registerSource('ring', function (cfg, ctx) {
  var targets = [];
  for (var i = 0; i < ctx.budget; i++) {
    var a = ctx.rand() * Math.PI * 2;
    targets.push({ key: 'ring:' + i, x: Math.cos(a), y: Math.sin(a), z: 0, look: 'edge' });
  }
  return { targets: targets };
});
```

`ctx.rand` is the scene's seeded generator, `ctx.budget` the pool size, `ctx.root` the stage element. Stable `key` values are what make morphing work: a target that keeps its key keeps its star. Each running stage is in `Constellation.instances`, and an instance answers `setScene(cfg)`, `setTimeline(list, loop)`, `next()`, and `burst(x, y)` for wiring the stars to your own events.

## Accessibility and performance

The pointer surface is a real `button` with an accessible name, so keyboard users can turn (arrows), reset (Home), and ripple (Enter or Space) without a mouse, and the page never scrolls under those keys. Vertical touch drags still scroll. Under `prefers-reduced-motion` the first scene renders once and moves only when asked; hover and click effects stay off. Without JavaScript or canvas, the fallback image is all that renders.

The loop pauses when a stage leaves the viewport or the tab goes to the background, the device pixel ratio is capped at two, and the pool scales with the drawn area, so a phone renders about a third of what a desktop does. Several stages on one page, as here, cost roughly one stage each, and only the visible ones run. The relevant platform references are [Path2D](https://developer.mozilla.org/en-US/docs/Web/API/Path2D) and [isPointInStroke](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/isPointInStroke) for the sampling, [globalCompositeOperation](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation) for the additive light, and [prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion) for the motion contract.

## Where it lives

| File | Role |
|---|---|
| `assets/js/constellation.js` | The engine: sources, pool, physics, renderer, interaction, timeline |
| `_includes/constellation.html` | The stage markup and styles; emits the scene as JSON |
| `_data/constellations/*.yml` | Scenes and timelines, designed as data |
| `_includes/brand/mark-shape.svg` | The mark's geometry, generated from `assets/brand/favicon.svg` |
| `scripts/generate_mark_shape.py` | Regenerates that geometry; `--check` fails when stale |
| `scripts/sample_mesh_points.py` | Samples an OBJ mesh into a point-cloud JSON |

For the context framework that keeps a component like this governed, see [[Building a native Claude context framework]]. If you would like one built into your own site, [book a conversation](/contact/).
