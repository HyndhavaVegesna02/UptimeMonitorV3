// STORY-095 — throwaway Playwright harness sweeping the LIVE deployed
// dashboard (https://d3ukiib1iqmbxb.cloudfront.net) for evidence. Never
// imported by the shipped app; lives only under tools/ui-sweep/. Run one
// phase at a time via `node sweep.mjs <phase>` so a failure in one phase
// never forces a re-run of the others:
//   node sweep.mjs tabs        -- AC1/AC2: six tabs, SPA-nav + deep-load
//   node sweep.mjs theme       -- AC4: dark/light + 390px viewport
//   node sweep.mjs sample-on   -- AC3 step: toggle sample mode ON, screenshot
//   node sweep.mjs sample-off  -- AC3 step: toggle sample mode OFF, screenshot
//   node sweep.mjs maint-create -- AC3 step: schedule the probe window
//   node sweep.mjs maint-delete -- AC3 step: delete the probe window, verify clean
//
// Each phase writes screenshots + a JSON evidence log (console errors,
// failed /api/* responses) under docs/scrum/sprints/2026-07-17-sprint-51/ui-sweep/.
// findings.md is authored by hand from this raw evidence, not generated here.

import { chromium } from 'playwright'
import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const BASE_URL = 'https://d3ukiib1iqmbxb.cloudfront.net'
const OUT_DIR = path.resolve(
  __dirname,
  '../../docs/scrum/sprints/2026-07-17-sprint-51/ui-sweep',
)
mkdirSync(OUT_DIR, { recursive: true })

const TABS = [
  { slug: 'dashboard', path: '/', label: 'Dashboard' },
  { slug: 'availability', path: '/availability', label: 'Availability' },
  { slug: 'approvals', path: '/approvals', label: 'Approvals' },
  { slug: 'check-history', path: '/check-history', label: 'Check History' },
  { slug: 'maintenance', path: '/maintenance', label: 'Maintenance' },
  { slug: 'publications', path: '/publications', label: 'Publications' },
]

function attachCapture(page, evidence) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      evidence.consoleErrors.push({ text: msg.text(), location: msg.location() })
    }
  })
  page.on('response', (response) => {
    const url = response.url()
    if (url.includes('/api/') && response.status() >= 400) {
      evidence.failedRequests.push({ url, status: response.status() })
    }
  })
  page.on('pageerror', (err) => {
    evidence.pageErrors.push(String(err))
  })
}

function newEvidence() {
  return { consoleErrors: [], failedRequests: [], pageErrors: [] }
}

function writeEvidence(name, evidence) {
  writeFileSync(
    path.join(OUT_DIR, `${name}.evidence.json`),
    JSON.stringify(evidence, null, 2),
  )
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(OUT_DIR, `${name}.png`), fullPage: true })
}

async function phaseTabs(browser) {
  const allEvidence = {}

  // Deep loads: one fresh context+page per tab, direct page.goto (exercises
  // the CloudFront rewrite function for non-root paths).
  for (const tab of TABS) {
    const context = await browser.newContext()
    const page = await context.newPage()
    const evidence = newEvidence()
    attachCapture(page, evidence)
    await page.goto(`${BASE_URL}${tab.path}`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    await screenshot(page, `${tab.slug}-deep`)
    allEvidence[`${tab.slug}-deep`] = evidence
    writeEvidence(`${tab.slug}-deep`, evidence)
    await context.close()
  }

  // SPA nav: single context+page, start at Dashboard, click through the
  // sidebar links (title attribute == tab.label, stable regardless of the
  // Approvals badge count changing the aria-label).
  const context = await browser.newContext()
  const page = await context.newPage()
  const spaEvidence = newEvidence()
  attachCapture(page, spaEvidence)
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await screenshot(page, 'dashboard-spa')

  for (const tab of TABS.filter((t) => t.path !== '/')) {
    await page.locator(`a.sidebar__tab[title="${tab.label}"]`).click()
    await page.waitForTimeout(300) // let the SPA-nav fetch actually start
    await page.waitForLoadState('networkidle')
    // Some tabs show a text loading indicator briefly after networkidle
    // resolves (client-side state update lags the underlying fetch settling)
    // -- wait for any "Loading" text to clear before the screenshot.
    await page
      .getByText(/Loading/i)
      .first()
      .waitFor({ state: 'hidden', timeout: 5000 })
      .catch(() => {})
    await page.waitForTimeout(500)
    await screenshot(page, `${tab.slug}-spa`)
  }
  allEvidence['spa-session'] = spaEvidence
  writeEvidence('spa-session', spaEvidence)
  await context.close()

  console.log(JSON.stringify(allEvidence, null, 2))
}

async function phaseTheme(browser) {
  // Light: fresh context (no localStorage override), emulate light system pref.
  {
    const context = await browser.newContext({ colorScheme: 'light' })
    const page = await context.newPage()
    const evidence = newEvidence()
    attachCapture(page, evidence)
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    await screenshot(page, 'theme-light')
    writeEvidence('theme-light', evidence)
    await context.close()
  }
  // Dark: fresh context, emulate dark system pref.
  {
    const context = await browser.newContext({ colorScheme: 'dark' })
    const page = await context.newPage()
    const evidence = newEvidence()
    attachCapture(page, evidence)
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    await screenshot(page, 'theme-dark')
    writeEvidence('theme-dark', evidence)
    await context.close()
  }
  // In-app toggle click (secondary check of the localStorage-override path).
  {
    const context = await browser.newContext({ colorScheme: 'light' })
    const page = await context.newPage()
    const evidence = newEvidence()
    attachCapture(page, evidence)
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    await page.locator('button[aria-label="Switch to dark theme"]').click()
    await page.waitForTimeout(300)
    await screenshot(page, 'theme-toggle-clicked')
    writeEvidence('theme-toggle-clicked', evidence)
    await context.close()
  }
  // Narrow viewport.
  {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 } })
    const page = await context.newPage()
    const evidence = newEvidence()
    attachCapture(page, evidence)
    await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(500)
    await screenshot(page, 'viewport-390x844')
    writeEvidence('viewport-390x844', evidence)
    await context.close()
  }
}

async function phaseSampleOn(browser) {
  const context = await browser.newContext()
  const page = await context.newPage()
  const evidence = newEvidence()
  attachCapture(page, evidence)
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await screenshot(page, 'sample-mode-before')

  const toggle = page.locator('button[aria-label="Sample mode"]')
  await toggle.click()
  await page.waitForFunction(
    () =>
      document.querySelector('button[aria-label="Sample mode"]')?.getAttribute(
        'aria-checked',
      ) === 'true',
  )
  await page.waitForTimeout(500)
  await screenshot(page, 'sample-mode-on')
  writeEvidence('sample-mode-on', evidence)
  await context.close()
}

async function phaseSampleOff(browser) {
  const context = await browser.newContext()
  const page = await context.newPage()
  const evidence = newEvidence()
  attachCapture(page, evidence)
  await page.goto(`${BASE_URL}/`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)

  const toggle = page.locator('button[aria-label="Sample mode"]')
  const checked = await toggle.getAttribute('aria-checked')
  if (checked === 'true') {
    await toggle.click()
    await page.waitForFunction(
      () =>
        document.querySelector('button[aria-label="Sample mode"]')?.getAttribute(
          'aria-checked',
        ) === 'false',
    )
  }
  await page.waitForTimeout(500)
  await screenshot(page, 'sample-mode-off')
  writeEvidence('sample-mode-off', evidence)
  await context.close()
}

async function phaseMaintCreate(browser) {
  const context = await browser.newContext()
  const page = await context.newPage()
  const evidence = newEvidence()
  attachCapture(page, evidence)
  await page.goto(`${BASE_URL}/maintenance`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await screenshot(page, 'maintenance-before')

  function toLocalInputValue(date) {
    const pad = (n) => String(n).padStart(2, '0')
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
      date.getHours(),
    )}:${pad(date.getMinutes())}`
  }
  const now = new Date()
  const starts = new Date(now.getTime() + 60 * 60 * 1000)
  const ends = new Date(now.getTime() + 2 * 60 * 60 * 1000)

  await page.locator('#maintenance-title').fill('ui-sweep-probe')
  await page
    .locator('#maintenance-reason')
    .fill('STORY-095 automated sweep probe -- safe to delete')
  await page.locator('#maintenance-component').selectOption({ index: 1 })
  await page.locator('#maintenance-start').fill(toLocalInputValue(starts))
  await page.locator('#maintenance-end').fill(toLocalInputValue(ends))
  await screenshot(page, 'maintenance-form-filled')

  await page.getByRole('button', { name: 'Schedule window' }).click()
  await page.getByText('ui-sweep-probe').first().waitFor({ timeout: 10_000 })
  await page.waitForTimeout(500)
  await screenshot(page, 'maintenance-created')
  writeEvidence('maintenance-create', evidence)
  await context.close()
}

async function phaseMaintDelete(browser) {
  const context = await browser.newContext()
  const page = await context.newPage()
  const evidence = newEvidence()
  attachCapture(page, evidence)
  await page.goto(`${BASE_URL}/maintenance`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)

  const row = page.locator('li.maintenance-window', { hasText: 'ui-sweep-probe' })
  await row.waitFor({ timeout: 10_000 })
  await row.getByRole('button', { name: 'Delete' }).click()
  await row.getByRole('button', { name: 'Yes' }).click()
  await row.waitFor({ state: 'detached', timeout: 10_000 })
  await page.waitForTimeout(500)
  await screenshot(page, 'maintenance-deleted')

  // Reload to confirm server-side removal, not just optimistic UI removal.
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  const stillThere = await page
    .locator('li.maintenance-window', { hasText: 'ui-sweep-probe' })
    .count()
  await screenshot(page, 'maintenance-verified-clean')
  writeEvidence('maintenance-delete', evidence)
  console.log(`ui-sweep-probe rows remaining after reload: ${stillThere}`)
  await context.close()
  if (stillThere !== 0) {
    throw new Error('maintenance probe window still present after delete + reload')
  }
}

const PHASES = {
  tabs: phaseTabs,
  theme: phaseTheme,
  'sample-on': phaseSampleOn,
  'sample-off': phaseSampleOff,
  'maint-create': phaseMaintCreate,
  'maint-delete': phaseMaintDelete,
}

async function main() {
  const phase = process.argv[2]
  const fn = PHASES[phase]
  if (!fn) {
    console.error(`Usage: node sweep.mjs <${Object.keys(PHASES).join('|')}>`)
    process.exit(1)
  }
  const browser = await chromium.launch({ headless: true })
  try {
    await fn(browser)
  } finally {
    await browser.close()
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
