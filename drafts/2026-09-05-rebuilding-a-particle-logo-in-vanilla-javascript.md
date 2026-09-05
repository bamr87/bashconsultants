---
title: "Rebuilding OpenAI's particle logo for our own brand in vanilla JavaScript"
description: "How we rebuilt OpenAI's draggable particle logo for the BASH mark in dependency-free JavaScript, and what AI-assisted building taught us"
author: "Amr Abdel-Motaleb"
layout: article
date: 2026-09-05T12:00:00.000Z
lastmod: 2026-09-05T12:00:00.000Z
draft: true
categories:
    - tech
    - AI
tags:
    - javascript
    - canvas
    - animation
    - front-end
    - jekyll
    - accessibility
    - ai-assisted-development
    - claude-code
keywords:
    - particle logo animation javascript
    - canvas particle logo
    - recreate openai logo animation
    - path2d ispointinpath sampling
    - additive blending canvas particles
    - prefers-reduced-motion canvas animation
preview: /assets/images/previews/rebuilding-a-particle-logo-in-vanilla-javascript.png
featured: false
excerpt: "OpenAI's GPT-6 Astra page opens with a logo made of light you can drag. We built the same thing for the BASH mark in one dependency-free script, and the build taught us as much about working with an AI pair as about canvas."
---

OpenAI's GPT-6 Astra announcement opens with the company's logo rendered as a cloud of light: thousands of tiny stars tracing the knot, slowly turning, and yours to spin with a drag or the arrow keys. It is the kind of hero that makes you stop scrolling. We wanted that feeling for the BASH mark, and we wanted it without adding a rendering library to a Jekyll site that ships as static files on GitHub Pages.

This is how the rebuild works, what it took to get it right, and the parts of the job where an AI pair earned its keep and the parts where it needed a browser to keep it honest.

## Reading a page you cannot fetch

The first surprise was that the page itself would not talk to us. Scripted fetches got a 403 from the bot wall, so there was no source to read. There was, however, a screenshot of the inspector, and that turned out to be all the design we needed.

The document object model (DOM) told the whole story. A `canvas` did the drawing. Next to it sat an SVG with the logo's paths, drawn as strokes with `stroke-width="80"`, hidden from view and used only as geometry. A `button` covered the canvas with the label "Drag or use arrow keys to rotate the OpenAI blossom" and a `data-dragging` attribute that flipped during a drag. A sibling `div` carried a `data-astra-shape-fallback` attribute, the static logo for browsers that could not run the effect.

That is the architecture: geometry from an SVG, a canvas that samples it, an accessible control on top, and a fallback underneath. Everything else is taste. Lesson one for working with an AI on a reverse-engineering job: give it the DOM, not the vibe. Class names and ARIA labels say more about a design than a description of how it looks.

## The recipe

Our version lives in one include and one script, about 550 lines of plain JavaScript with no dependencies. Here is what it does, in the order it does it.

### 1. Geometry from the SVG, not from a bitmap

The BASH B is a filled shape with a counter, not a stroked tube, so the sampling has to know inside from outside. The browser already has a perfect tool for that: `Path2D` objects built from the SVG `d` attributes, and the canvas hit-testing methods `isPointInPath` and `isPointInStroke`.

Particles are placed by rejection sampling. Pick a random point in the mark's bounding box, keep it if it lands inside the outer path and outside the counter, and classify it as an edge particle if it also lands inside a stroke of the outline, tested with a chosen `lineWidth`.

```js
ctx.lineWidth = 14;                       // the edge band, in SVG units
function inFill(x, y) {
  return ctx.isPointInPath(fill, x, y) && !ctx.isPointInPath(hole, x, y);
}
function onEdge(x, y) {
  return ctx.isPointInStroke(fill, x, y) || ctx.isPointInStroke(hole, x, y);
}
```

No rasterizing, no pixel reads, and it works for any SVG shape you hand it. A coarse scan of the same tests finds the ink's bounding box, so the cloud is centered on the letter rather than on the SVG page. Positions are then normalized to the mark's half-size, which makes every later number resolution-independent.

### 2. Give it thickness

A flat letter is dull to rotate. Every particle gets a depth coordinate drawn uniformly from a thin slab, about a quarter of the mark's half-size, so the B becomes a glowing plate. Edge particles are larger and brighter, interior ones smaller and dimmer, and about one in ten edge particles is nudged just outside the outline as loose dust. Seen edge-on after a drag, the plate reads as a thin bar of light, which is exactly the cue that sells the third dimension.

### 3. Rotate and project

Two angles, a turn about the vertical axis and a tilt about the horizontal one, and a perspective divide. That is the entire 3D engine.

```js
var x1 = x * cy + z * sy, z1 = -x * sy + z * cy;   // turn about Y
var y2 = y * cx - z1 * sx, z2 = y * sx + z1 * cx;  // tilt about X
var per = focal / (focal + z2);                    // nearer is bigger
var X = centreX + x1 * radiusPx * per;
var Y = centreY + y2 * radiusPx * per;
```

Particles nearer the viewer are drawn a little larger and brighter, which is the second depth cue.

### 4. Light that adds up

The trick that makes a particle cloud look like light instead of confetti is additive blending. With `globalCompositeOperation = 'lighter'`, overlapping particles brighten each other, and because addition is commutative the draw order stops mattering. That removes the depth sort a conventional 3D renderer would need, so the frame loop is a single pass over the array.

Each particle is a pre-rendered sprite: a small canvas holding a radial gradient from a white-hot core out to the particle's color, drawn scaled with `drawImage`. One sprite per color, four in total, instead of a gradient per particle per frame. A wide, coreless wash of the teal is drawn once behind the mark so the cloud sits in a faint nebula rather than on flat black.

### 5. Make it feel alive

Every particle twinkles on its own phase and speed, a few twinkle hard and fast as sparklers, and each one drifts a hair around its home position. On load the particles fly in from scattered positions over about a second and a half, staggered per particle. When nobody is touching it, the mark turns slowly and nods a little, which keeps the slab's depth in view.

The mouse gets a reaction of its own, and it is a small physics model rather than a painted effect. Every particle is a body with a velocity, a spring pulling it back to its home position, and some damping, tuned slightly under-damped so the letter reassembles over a few seconds with a hint of wobble. The pointer is a moving body too. Its smoothed velocity sets the impulse, so a resting cursor only dents the mark while a fast sweep hits harder and reaches wider, and a share of each push is aimed along the pointer's direction of travel, which flings particles out in a wake behind a quick swipe. A quick horizontal swipe also nudges the whole mark's turn a little. Two details make it feel physical: the impulse is computed in screen space but stored in the mark's own space by running it back through the inverse rotation, so a dent left on the front face turns away with the mark instead of sticking to the glass, and moving particles flare brighter in proportion to their speed.

### 6. Make it usable

The control is the same one OpenAI used: a `button` over the canvas with an `aria-label`, focusable and keyboard-operable. Pointer events with pointer capture handle the drag; the release velocity is smoothed over the last few moves so a flick keeps the mark spinning and it eases back into the idle turn. Arrow left and right nudge the turn, up and down the tilt, Home resets, and the handler calls `preventDefault()` so the page does not scroll under the keyboard user's feet.

Three details cost little and matter a lot. `touch-action: pan-y` on the button means a vertical swipe on a phone still scrolls the page while a horizontal one turns the mark. `prefers-reduced-motion` switches the component to render once and move only in response to input, so people who asked for less motion get a still image that still answers a drag. And the static mark stays in the markup as the fallback, hidden only after the script has successfully built the cloud, so a browser with no JavaScript or no canvas sees the logo, not a hole.

The loop pauses when the mark scrolls out of view or the tab goes to the background, the device pixel ratio is capped at two, and the particle budget scales with the drawn area, so a phone renders about a third of what a desktop does.

## Keeping it governed

We run this site the way we advise clients to run their systems, so the effect had to fit the house rules rather than bend them.

The geometry is not hand-copied. A short Python script reads the canonical favicon SVG, finds the two paths and the layer's translate by their Inkscape labels, and writes a minimal SVG include. A `--check` flag fails when the include is stale, so the outline cannot drift from the mark the site actually ships.

The cloud is deterministic. A seeded random number generator means every visitor sees the same constellation, and a screenshot taken today matches one taken next month. That made visual review possible at all.

The colors come from the theme configuration, the same place the brand palette is defined for everything else, so there is one file of record. And because the site consumes a remote theme, the one layout it forks is listed in an overrides file with an honest reason, which we updated to describe the new hero.

## What the AI pair got wrong, and how we caught it

The first working version had two bugs that no amount of reading the code would have shown.

The mark had a faint rectangular frame around it. The cause was a rule in the theme's stylesheet that styles every `button` that is not a copy button with a one-pixel border, and that selector outranks a lone class on specificity. The fix was a doubled-up selector, with a comment explaining why it is doubled.

The tagline under the headline was almost invisible. The hero uses Bootstrap's scoped dark theme, and the scoped attribute only redefines CSS variables; it does not re-apply `color` to the element. Inherited text stayed the light-mode body color while the utility classes next to it flipped correctly. One line, `color: var(--bs-body-color)`, on the band fixed it.

Both were found the same way: build the site, serve it, and drive it in headless Chromium. The verification script screenshots the hero, drags it and confirms the turn changed, presses the arrow keys and confirms the page did not scroll, checks the loop idles under reduced motion, loads the page with JavaScript off, and fails on any console error. A probe of computed styles then pointed straight at the two rules. Screenshots are a test. Computed styles are a debugger.

A third snag was pure environment: the local Jekyll build failed with an invalid US-ASCII character in the theme's Sass. The container had no UTF-8 locale set, so Ruby read an em-dash as a byte it could not place. `LC_ALL=C.UTF-8` and the build passed. Worth remembering the next time a build fails on a character in someone else's file.

## Tips for building this kind of thing with an AI

1. **Give it the DOM, not the vibe.** A screenshot of the inspector, with its class names and ARIA labels, is a specification. "Make it look like the OpenAI one" is not.
2. **Make it prove the work in a browser.** Ask for a headless run that screenshots the result and asserts on behavior. The two bugs above were invisible in the source and obvious in a picture.
3. **Ask for determinism up front.** A seeded generator, a script that produces the geometry, and a check that fails when the output is stale turn a visual effect into something you can review and diff.
4. **Let it tune from pictures, but keep the taste.** The first render was chunky confetti. Narrowing the edge band, shrinking the particles, and pulling the red back to a few sparks were judgment calls made from screenshots, not from code.
5. **Keep the boring parts as scripts.** Extracting paths from an SVG is a deterministic job. Spend the model on the parts that need judgment, like the interaction feel, and let a forty-line script own the rest.

## It turned into a framework

Once the logo worked, the obvious question was what else the same stars could draw. The answer was to split the script in two: sources, which turn something into targets (points in a unit space with a look and a color), and the engine, which gives every target a star with physics and renders the lot. A source for SVG, one for text, one for a typed terminal session, one for 3D point clouds, one for images, and a registry for your own. Scenes became YAML files rendered by one include, so an animation is designed as data and reviewed in a diff, and a timeline morphs the same light from one scene to the next while the stars a scene does not need wait as background dust.

The terminal source is the one that surprised us. Each character is rasterized once with a monospace font and sampled into a dozen points, and because new targets recruit stars from the dust around the stage, typed text looks like it condenses out of the field rather than being drawn on it. A click got physics too: a pop under the pointer and a ring that travels outward, pushing stars as it passes.

The engine, five scenes, a mesh sampler, and the full reference live in the [BASH toolkit](https://bash-365.com/tools/partners/constellation-engine/).

## Try it

The mark is live on the [BASH Consulting homepage](https://bash-365.com/). Drag it, flick it, or tab to it and use the arrow keys. The include, the script, and the generator are in the site's public repository, and the whole thing is small enough to read in one sitting.
