import { defineConfig, devices } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const currentDir = path.dirname(fileURLToPath(import.meta.url))
const services = JSON.parse(
  fs.readFileSync(path.join(currentDir, '..', 'nonfunctional', 'frontend', 'services.json'), 'utf8'),
)

export default defineConfig({
  testDir: path.join(currentDir, 'e2e-nonfunctional'),
  outputDir: path.join(currentDir, 'test-results'),
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  reporter: [
    ['line'],
    ['html', { outputFolder: path.join(currentDir, 'playwright-report'), open: 'never' }],
    ['json', { outputFile: path.join(currentDir, 'test-results', 'results.json') }],
  ],
  use: {
    ...devices['Pixel 7'],
    baseURL: services.web,
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'mobile-chromium', use: { ...devices['Pixel 7'] } }],
})


