const { test, expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');
const path = require('node:path');

// Render the real templates and mock API data so these UI checks need no database.
const fixtures = JSON.parse(execFileSync('python3', ['-c', `
import json
from jinja2 import Environment, FileSystemLoader
from types import SimpleNamespace
env = Environment(loader=FileSystemLoader('web/templates'))
print(json.dumps({name + ('-partial' if partial else ''): env.get_template(name + '.html').render(
    htmx_request=partial, request=SimpleNamespace(path='/'),
    url_for=lambda *args, **kw: '/static/' + kw.get('filename', ''))
    for name in ['dashboard', 'favorites'] for partial in [False, True]}))
`], { encoding: 'utf8' }));

test('dashboard fits viewport and supports keyboard and repeated page navigation', async ({ page }) => {
    test.setTimeout(90000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('http://layout.test/**', async route => {
        const url = new URL(route.request().url());
        if (url.pathname.startsWith('/static/')) {
            return route.fulfill({ path: path.join(process.cwd(), 'web', url.pathname),
                contentType: url.pathname.endsWith('.css') ? 'text/css' : 'application/javascript' });
        }
        if (url.pathname.startsWith('/api/')) {
            return route.fulfill({ json: url.pathname === '/api/metrics' ? {
                total_trades: 0, win_rate: 0, total_pnl: 0, profit_factor: 0,
                avg_win: 0, avg_loss: 0, best_trade: 0, worst_trade: 0, recent_pnl: []
            } : { accounts: [], favorites: [], trades: [], authenticated: true,
                user: { name: 'Test User' } } });
        }
        const partial = route.request().headers()['hx-request'] === 'true';
        if (partial) await new Promise(resolve => setTimeout(resolve, 200));
        const name = url.pathname === '/favorites' ? 'favorites' : 'dashboard';
        return route.fulfill({ body: fixtures[name + (partial ? '-partial' : '')], contentType: 'text/html' });
    });
    await page.goto('http://layout.test/');
    await expect(page.locator('#total-trades')).toHaveText('0');
    for (const [width, height] of [[1920, 1080], [1280, 800], [768, 1024], [390, 844], [375, 667], [844, 390]]) {
        await page.setViewportSize({ width, height });
        await expect.poll(() => page.evaluate(() => {
            const main = document.querySelector('main');
            const cards = [...document.querySelectorAll('.metric-card')].map(el => el.getBoundingClientRect());
            const metrics = document.querySelector('.dashboard-metrics');
            const charts = document.querySelector('.dashboard-charts');
            return main.scrollHeight <= main.clientHeight + 1 &&
                document.documentElement.scrollWidth <= innerWidth &&
                cards.every(card => Math.abs(card.height - cards[0].height) < 1 && Math.abs(card.width - cards[0].width) < 1) &&
                Math.abs(metrics.clientHeight - charts.clientHeight) <= 1;
        })).toBe(true);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    const toggle = page.getByRole('button', { name: 'Expand sidebar' });
    await toggle.focus();
    await page.keyboard.press('Enter');
    await expect(page.locator('#sidebar-toggle')).toHaveAttribute('aria-expanded', 'true');
    await expect(page.locator('main')).toHaveAttribute('inert', '');
    await page.keyboard.press('Escape');
    await expect(page.locator('#sidebar-toggle')).toBeFocused();
    await expect(page.locator('#sidebar-toggle')).toHaveAttribute('aria-expanded', 'false');
    await page.setViewportSize({ width: 1280, height: 800 });
    for (let visit = 0; visit < 2; visit++) {
        await page.getByRole('link', { name: 'Favorites', exact: true }).click();
        await expect(page.locator('main')).toHaveAttribute('aria-busy', 'true');
        await expect(page.locator('main h1')).toHaveText('Favorite Products');
        await expect(page.locator('main h1')).toBeFocused();
        await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
        await expect(page.locator('main h1')).toHaveText('Dashboard');
        await expect(page.locator('#total-trades')).toHaveText('0');
        await expect(page.locator('main')).toHaveCount(1);
        await expect(page.locator('.sidebar')).toHaveCount(1);
    }
    expect(errors).toEqual([]);
});
