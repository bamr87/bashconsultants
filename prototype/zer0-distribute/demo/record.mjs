// Record the zer0-distribute review dashboard as a screen capture.
//
// This drives the real prototype in a real browser: the dashboard is served by
// `zer0-distribute serve` from actual files on disk, and the Approve click actually
// writes to the queue. Nothing on screen is a mock-up, and nothing is a
// re-enactment — the video is whatever the app did.
//
// What it deliberately does NOT do: show a live post reaching LinkedIn. The app
// has not been granted API access yet, so `publish` is dry-run only and the
// recording shows the payload it would send rather than pretending to send it.
//
// Usage:
//   node record.mjs [--url http://127.0.0.1:8765] [--out ./recording]
//
// Requires: npm i playwright   (Chromium at PLAYWRIGHT_BROWSERS_PATH)

import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'
import { resolve } from 'node:path'

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`)
  return i > -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback
}

const URL = arg('url', 'http://127.0.0.1:8765')
const OUT = resolve(arg('out', './recording'))
const SIZE = { width: 1280, height: 800 }

const beat = (page, ms) => page.waitForTimeout(ms)

// Move the cursor in visible steps. A jump-cut to a click reads as an edit; a
// pointer that travels reads as someone using the thing.
async function glideTo(page, locator) {
  const box = await locator.boundingBox()
  if (!box) return null
  const target = { x: box.x + box.width / 2, y: box.y + box.height / 2 }
  await page.mouse.move(target.x, target.y, { steps: 28 })
  return target
}

async function main() {
  mkdirSync(OUT, { recursive: true })

  // Video capture needs the full browser — the default headless shell is
  // lighter but cannot record, which is the entire point here. Set
  // CHROMIUM_PATH when the local Chromium is not the build Playwright pins.
  const launch = process.env.CHROMIUM_PATH
    ? { executablePath: process.env.CHROMIUM_PATH }
    : { channel: 'chromium' }
  const browser = await chromium.launch(launch)
  const context = await browser.newContext({
    viewport: SIZE,
    deviceScaleFactor: 2,
    recordVideo: { dir: OUT, size: SIZE },
  })
  const page = await context.newPage()

  // 1. The dashboard as a developer opens it.
  await page.goto(URL, { waitUntil: 'networkidle' })
  await beat(page, 2600)

  // 2. The draft waiting for approval — composed from the repo's own git tag.
  const pending = page.locator('.card.pending').first()
  await pending.scrollIntoViewIfNeeded()
  await glideTo(page, pending.locator('.title'))
  await beat(page, 3200)

  // 3. The body, with the marker showing where LinkedIn truncates.
  await glideTo(page, pending.locator('.body'))
  await beat(page, 3400)

  // 4. The exact outgoing request. This is the audit surface: a developer can
  //    read the payload before anything is authorised to send it.
  const payload = page.locator('pre.json').first()
  await payload.scrollIntoViewIfNeeded()
  await glideTo(page, payload)
  await beat(page, 3800)

  // 5. The track record the tool accumulates — the reason to keep using it.
  const stats = page.locator('.stats').first()
  if (await stats.count()) {
    await stats.scrollIntoViewIfNeeded()
    await glideTo(page, stats)
    await beat(page, 2800)
  }

  // 6. Declared audiences. Written for, not scraped from.
  const audience = page.locator('.aud').first()
  if (await audience.count()) {
    await audience.scrollIntoViewIfNeeded()
    await beat(page, 2600)
  }

  // 7. The gate. A human clicks; only then is the post eligible to publish.
  await page.locator('.card.pending').first().scrollIntoViewIfNeeded()
  const approve = page.locator('.card.pending button[type=submit]').first()
  await glideTo(page, approve)
  await beat(page, 1800)
  await approve.click()
  await page.waitForLoadState('networkidle')
  await beat(page, 3400)

  // 8. The result: the queue now shows it approved, and nothing is pending.
  await page.locator('h2').first().scrollIntoViewIfNeeded()
  await beat(page, 3000)

  await context.close()   // video is written on close
  await browser.close()
  console.log(`recorded to ${OUT}`)
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
