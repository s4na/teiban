import assert from 'node:assert/strict';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import process from 'node:process';
import test from 'node:test';
import puppeteer from 'puppeteer';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const fixture = `<!doctype html><html><head><title>Fixture</title></head><body>
  <h2 id="target" data-teiban-target="notice">定番サンプル</h2>
  <h2 id="other" data-teiban-target="notice">別の通知</h2>
  <p id="paragraph" data-teiban-target="notice">定番サンプル</p>
</body></html>`;

async function openFixture(browser, url = 'https://example.com/fixture') {
  const page = await browser.newPage();
  await page.setRequestInterception(true);
  page.on('request', request => {
    void request.respond({ status: 200, contentType: 'text/html; charset=utf-8', body: fixture });
  });
  await page.goto(url);
  await page.waitForNetworkIdle();
  return page;
}

test('loaded Manifest V3 content script', async t => {
  const browser = await puppeteer.launch({
    headless: true,
    pipe: true,
    dumpio: true,
    // Opt in only on a disposable CI runner; every page response is a local fixture.
    args: process.env.CHROME_NO_SANDBOX === '1' ? ['--no-sandbox'] : [],
    enableExtensions: [join(root, 'extension')]
  });
  t.after(() => browser.close());

  await t.test('highlights only the exact target and loads the declared CSS', async () => {
    const page = await openFixture(browser);
    try {
      await page.waitForSelector('#target.teiban-example-highlight');
      assert.equal(await page.$eval('#target', el => getComputedStyle(el).outlineStyle), 'solid');
      assert.equal(await page.$eval('#other', el => el.className), '');
      assert.equal(await page.$eval('#paragraph', el => el.className), '');
    } finally {
      await page.close();
    }
  });

  await t.test('handles elements added by a SPA', async () => {
    const page = await openFixture(browser);
    try {
      await page.evaluate(() => {
        const heading = document.createElement('h2');
        heading.id = 'late';
        heading.dataset.teibanTarget = 'notice';
        heading.textContent = '定番サンプル';
        document.body.append(heading);
      });
      await page.waitForSelector('#late.teiban-example-highlight');
    } finally {
      await page.close();
    }
  });

  await t.test('removes its styling when the target no longer matches', async () => {
    const page = await openFixture(browser);
    try {
      await page.waitForSelector('#target.teiban-example-highlight');
      await page.$eval('#target', el => { el.textContent = '別の通知'; });
      await page.waitForFunction(() => !document.querySelector('#target').classList.contains('teiban-example-highlight'));
    } finally {
      await page.close();
    }
  });

  await t.test('does not run outside the manifest match pattern', async () => {
    const page = await openFixture(browser, 'https://example.org/fixture');
    try {
      assert.equal(await page.$eval('#target', el => el.className), '');
      assert.notEqual(await page.$eval('#target', el => getComputedStyle(el).outlineStyle), 'solid');
    } finally {
      await page.close();
    }
  });

  await t.test('restores its marker after a SPA class rewrite without a mutation loop', async () => {
    const page = await openFixture(browser);
    try {
      await page.waitForSelector('#target.teiban-example-highlight');
      await page.evaluate(() => {
        globalThis.classMutations = 0;
        const target = document.querySelector('#target');
        new MutationObserver(records => { globalThis.classMutations += records.length; })
          .observe(target, { attributes: true, attributeFilter: ['class'] });
        target.className = 'site-heading';
      });
      await page.waitForSelector('#target.site-heading.teiban-example-highlight');
      await page.waitForNetworkIdle();
      assert.equal(await page.evaluate(() => globalThis.classMutations), 2);
      assert.equal(await page.$eval('#target', el => getComputedStyle(el).outlineStyle), 'solid');
    } finally {
      await page.close();
    }
  });
});
