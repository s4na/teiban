# 小さなChrome拡張を作るときの定番

## 用途と前提

特定サイトのDOMへ小さな機能を加える拡張は、Manifest V3と素のJavaScriptから始める。
lintはESLint、テストはNode標準testとPuppeteer。popup・options・service workerは必要になってから追加する。
bundleや複数画面が必要なら [VoidZero等の構成](web-voidzero-go.md) を検討する。

以下は利用先へ写して調整する例。`example.com` は説明用で、参照元のモーダル操作は実装しない。
参照元から一般化するのは、権限・対象判定・失敗時の復旧・テストの方針。

## 1. manifestで注入先を絞る

`extension/manifest.json`。対象のHTTPS origin・pathとトップフレームへ限定する。

```json
{
  "manifest_version": 3,
  "name": "Example Helper",
  "version": "0.1.0",
  "description": "対象ページのDOMへ小さな機能を追加する例",
  "content_scripts": [
    {
      "matches": ["https://example.com/tasks/*"],
      "js": ["content.js"],
      "run_at": "document_idle",
      "all_frames": false
    }
  ]
}
```

CSSが必要ならcontent_scriptsの項目に `"css": ["content.css"]` を追加する。描画前の処理が必要な場合だけ `document_start` を検討する。
`permissions`・`host_permissions` は使うAPIに応じて追加し、`tabs` や広いhost権限を一律に付けない。
権限・matchesを広げる更新では、対象外ページと利用者への影響も確認する。
content scriptとページのJS環境は既定では別。message通信を足すなら、入力と受け付ける範囲を検証する。

## 2. ブラウザ用とNode用のlintを分ける

`eslint`・`@eslint/js`・`globals`・`puppeteer` を開発依存に入れ、lockfileもcommitする。
package managerは一つに揃え、採用版と更新方法は [依存管理の方針](dependency-updates.md) に従う。

`eslint.config.mjs`。Nodeのglobalをcontent scriptへ混ぜない。

```js
import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['dist/**'] },
  js.configs.recommended,
  {
    files: ['extension/**/*.js'],
    languageOptions: {
      sourceType: 'script',
      globals: { ...globals.browser, chrome: 'readonly' },
    },
  },
  {
    files: ['test/**/*.mjs', 'eslint.config.mjs'],
    languageOptions: { globals: globals.node },
  },
];
```

`sourceType: 'script'` はmanifestから読み込む通常のcontent script用。
TypeScriptやbundleを採用した場合は、型検査とbuildを分け、配布物も検査する。

## 3. 拡張をloadしてDOMの結果を待つ

注入経路を確認するため、`extension/content.js` はfixtureの対象要素へ属性を付けるだけにする。

```js
const target = document.querySelector('main[data-feature="teiban-example"]');
if (target instanceof HTMLElement) {
  target.dataset.teibanReady = 'true';
}
```

`test/extension.test.mjs`。対象URLの応答をfixtureへ置き換え、manifest経由の実行を検査する。
このページのリクエストは応答または中断し、実サイトへは送らない。

```js
import test from 'node:test';
import { resolve } from 'node:path';
import puppeteer from 'puppeteer';

test('manifest経由でcontent scriptが実行される', async () => {
  const browser = await puppeteer.launch({
    enableExtensions: [resolve('extension')],
    headless: true,
  });
  try {
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', (request) => {
      if (request.isInterceptResolutionHandled()) return;
      if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
        return request.respond({
          status: 200,
          contentType: 'text/html; charset=utf-8',
          body: '<!doctype html><meta charset="utf-8"><main data-feature="teiban-example"></main>',
        });
      }
      return request.abort();
    });
    await page.goto('https://example.com/tasks/1');
    await page.waitForSelector('main[data-teiban-ready="true"]', { timeout: 5000 });
  } finally {
    await browser.close();
  }
});
```

`package.json` へ追加するscripts:

```json
{
  "scripts": {
    "lint": "eslint .",
    "browser:install": "puppeteer browsers install chrome",
    "test": "node --test test/*.test.mjs"
  }
}
```

利用先のプロジェクトルートで実行する。

```sh
set -eu
npm ci
npm run browser:install
npm run lint
npm test
```

`enableExtensions` はPuppeteer 25.13.0の公式資料で確認した。
採用版に対応するNodeとPuppeteerが取得するChromeを使い、個人の `userDataDir` は渡さない。
CIの共通部分は [GitHub Actionsの方針](github-actions.md) を参照。
sandboxが起動できなければ、まず対応環境を整える。`--no-sandbox` を使う場合も、
破棄されるrunnerで管理下のfixtureだけを開くテストに限定し、実サイトへ流用しない。

## 4. 実機能へ置き換えるときの確認

smoke testは初回の注入だけを確かめる。属性の確認を実機能の結果へ置き換え、次を追加する。

- selectorだけでなく要素の種類・見出し・状態も確認し、似た別UIやDOM変更時は誤操作せず見送る。
- matches外の新しいdocumentではJS・CSSが注入されない。同一documentのSPA遷移では自動で注入・解除されないため、URL変更の検出と有効化・解除を実装する。
- 動的DOMを監視する範囲を絞る。ノードの追加・削除・置換は `childList`、既存テキストノードの変更は `characterData`、属性変更は `attributes` と `attributeFilter`、子孫も対象なら `subtree` を使う。
- 再処理してもイベント登録・操作が重複せず、自分の変更でobserverがループしない。サイト側のclass・styleを壊さず、書き換えられた場合も必要な状態を復元する。
- モーダルは非表示だけで成功にせず、handlerの準備・閉じた結果・scroll lockも確認する。一時非表示や再試行には回数・待ち時間の上限を設け、失敗時は操作できる状態へ戻す。

fixtureでは文字コードを明示し、実サイトでもselector・動作・対象外への影響を手動確認する。
サイトのDOM変更は依存更新とは別に起こるため、対象判定が崩れた場合のテストも保つ。

## 5. 配布ファイルをallowlistで指定する

POSIX shellと `zip`・`unzip` がある環境で、上の2ファイルだけをまとめる。
CSS・icons等を追加したら、manifestとallowlistの両方を更新する。

```sh
set -eu
mkdir -p dist
# 古いZIPの余分なentryを残さない
rm -f dist/extension.zip
(
  cd extension
  zip -X ../dist/extension.zip manifest.json content.js
)
unzip -l dist/extension.zip
```

ZIPのルートに `manifest.json` があり、node_modules・テスト・開発設定・secretが入っていないことを確認する。
展開した配布物をChromeへloadし、Web Store向けにはicons・掲載情報・必要なプライバシー説明を整える。
依存更新ではpackage.json・lockfileを揃えて実Chromeのテストを行う。拡張公開時はmanifestのversionを別途上げ、配布物の版と揃える。
CIのZIP生成とストア公開は、別の権限・操作にする。

## 参考資料

確認日: 2026-10-13。API・設定は公式資料で確認した。例のlint・Chrome起動・ZIP読込は利用先で検証する。

- 参照元: [manifest](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/manifest.json)、[テスト](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/test/extension.test.js)。commitを固定し、機能固有の処理は一般化しない。
- Chrome: [manifest](https://developer.chrome.com/docs/extensions/reference/manifest)、[content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)、[配布準備](https://developer.chrome.com/docs/webstore/prepare)
- ESLint: [languageOptions](https://eslint.org/docs/latest/use/configure/language-options)
- Puppeteer: [拡張load](https://pptr.dev/guides/chrome-extensions)、[request interception](https://pptr.dev/guides/network-interception)、[Chrome取得](https://pptr.dev/guides/configuration)、[browser取得CLI](https://pptr.dev/browsers-api)、[実行環境とsandbox](https://pptr.dev/troubleshooting)
- MDN: [MutationObserverの監視設定](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver/observe)
