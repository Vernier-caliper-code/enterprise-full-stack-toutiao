import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

const viewports = [
  { width: 375, height: 812 },
  { width: 390, height: 844 },
  { width: 440, height: 956 },
]

const routes = [
  { path: '/', title: '首页' },
  { path: '/category', title: '全部分类' },
  { path: '/ai-chat', title: 'AI问答' },
  { path: '/my', title: '我的' },
  { path: '/news/9000', title: '新闻详情' },
  { path: '/login', title: '用户登录' },
  { path: '/register', title: '用户注册' },
  { path: '/settings', title: '设置' },
]

test.describe('移动端布局与路由', () => {
  for (const viewport of viewports) {
    test(`无横向滚动 ${viewport.width}px`, async ({ page }) => {
      await page.setViewportSize(viewport)
      for (const route of routes) {
        await page.goto(route.path)
        await page.waitForLoadState('networkidle')
        const dimensions = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: document.documentElement.clientWidth,
        }))
        expect(
          dimensions.scrollWidth,
          `${route.path} overflow at ${viewport.width}px`,
        ).toBeLessThanOrEqual(dimensions.clientWidth + 1)
      }
    })
  }
})

test('11 个路由均可用且无页面异常', async ({ page }) => {
  const errors = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })

  const allRoutes = [
    ...routes,
    { path: '/favorites', title: '我的收藏' },
    { path: '/history', title: '浏览历史' },
    { path: '/profile', title: '个人资料' },
  ]
  for (const route of allRoutes) {
    const response = await page.goto(route.path)
    expect(response?.status()).toBe(200)
    await page.waitForLoadState('networkidle')
    if (route.path === '/login' || route.path === '/register') {
      expect(page.url()).toContain(route.path)
    } else if (['/favorites', '/history', '/profile'].includes(route.path)) {
      expect(page.url()).toMatch(/\/login\?redirect=/)
    } else {
      expect(page.url()).not.toContain('/login')
    }
  }
  expect(errors).toEqual([])
})

test('关键用户旅程', async ({ page }) => {
  const suffix = Date.now().toString(36)
  const username = `qa_${suffix}`
  const password = 'Nonfunctional#2026'

  await page.goto('/register')
  const fields = page.locator('input')
  await fields.nth(0).fill(username)
  await fields.nth(1).fill(password)
  await fields.nth(2).fill(password)
  await page.getByRole('button', { name: '注册', exact: true }).click()
  await expect(page).toHaveURL(/\/my$/)
  await expect(page.getByText(username, { exact: false }).first()).toBeVisible()

  await page.goto('/')
  const firstNews = page.locator('.news-item').first()
  await expect(firstNews).toBeVisible()
  const newsTitle = (await firstNews.locator('.news-title').textContent()).trim()
  await firstNews.click()
  await expect(page.getByRole('heading', { name: newsTitle })).toBeVisible()
  await page.getByRole('button', { name: '收藏新闻' }).click()
  await expect(page.getByRole('button', { name: '取消收藏' })).toBeVisible()

  await page.goto('/favorites')
  await expect(page.getByText(newsTitle, { exact: true })).toBeVisible()
  await page.goto('/history')
  await expect(page.getByText(newsTitle, { exact: true })).toBeVisible()
})

test('11 个路由无 axe serious/critical 违规', async ({ page }) => {
  const allRoutes = [
    ...routes,
    { path: '/favorites', title: '我的收藏' },
    { path: '/history', title: '浏览历史' },
    { path: '/profile', title: '个人资料' },
  ]
  for (const route of allRoutes) {
    await page.goto(route.path)
    await page.waitForLoadState('networkidle')
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    const blocking = results.violations.filter(
      (violation) => violation.impact === 'serious' || violation.impact === 'critical',
    )
    expect(
      blocking,
      `${route.path}: ${blocking.map((item) => item.id).join(', ')}`,
    ).toEqual([])
  }
})


