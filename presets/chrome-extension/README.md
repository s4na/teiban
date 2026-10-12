# 小さなChrome拡張の定番

## 用途と前提

特定サイトのDOMに小さな機能を足すChrome拡張。
参照は [chatgpt-rate-limit-modal-dismiss](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/tree/2aee4c8eec89e6d58e7126bf463ee5dd641438ba)。
2026-10-12にmainの `2aee4c8eec89e6d58e7126bf463ee5dd641438ba` とmanifest・lint・CI・テストを確認した。

この例はManifest V3、素のJavaScript、ESLint、Node標準test＋Puppeteer。
popupや複数画面が必要になるまで、React・bundler・service workerを必須にしない。
npmとpackage-lock.jsonを使い、参照例と同じ小さな開発構成を初期値にする。

## 採用する設定

| 対象 | 初期値・判断 |
| --- | --- |
| manifest | V3。name、version、descriptionとcontent_scriptsを明示 |
| URL | `matches` を必要なHTTPS originへ限定する |
| 権限 | content scriptだけで足りる場合はpermissionsを増やさない |
| 注入時期 | 通常は `document_idle`。描画前の処理が必要な場合だけ `document_start` |
| DOM | selectorと条件で対象を限定。SPAの後から来る要素も扱う |
| 終了・失敗 | 条件外なら操作しない。隠す処理なら失敗時の復元を用意する |
| JS lint | ESLint。ブラウザとNodeのglobalsを対象ファイルに分ける |
| テスト | 実Chromeへ拡張をloadし、manifestのURL判定とDOMの結果を確認 |
| 配布 | 明示したファイルだけをZIPへ入れ、manifestをZIPのルートへ置く |

例の機能は `https://example.com/*` で、`h2[data-teiban-target="notice"]` の本文が
「定番サンプル」の場合だけoutlineを付けること。本文や属性が変わって条件外になれば外す。
対象URL・selector・文字列は持ち込み先の機能へ置き換える。

参照元のモーダル自動dismissでは、selector、見出し、ボタンをすべて確認し、
クリック完了・画面の操作状態・失敗時の復元もテストしている。
その機能固有の処理を全拡張へコピーするのではなく、この判断と確認の仕方を定番にする。

## 配置と導入

```text
extension/manifest.json   ブラウザへ読み込む設定
extension/content.js     DOM操作
extension/content.css    対象を限定したCSS
eslint.config.js         JS lint
package.json             開発用コマンド（配布物には入れない）
package-lock.json        開発依存の固定
scripts/package.js       明示した配布ファイルだけをZIPにする
test/extension.test.js    Chromeに実際にloadするテスト
.github/workflows/ci.yml  コピー用CI
```

1. README以外を利用先リポジトリのルートへコピーする。隠しファイルも含める。
2. package名、manifestのname・version・description・matchesを変える。
3. selector・処理・テストfixtureを実際の機能に合わせる。
4. Node 24.16.0を用意し、ルートで次を実行する（macOS / Linux、packageにはzipが必要）。

```sh
npm ci
npm run lint
npm test
npm run package
```

Puppeteerがテスト用Chromeを取得するため、初回導入にはネットワークが必要。
テストは別プロファイルのChromeを起動し、サイトの応答をfixtureへ差し替える。
実サービスへのログインは不要。個人のChromeプロファイルは使用しない。

Ubuntu 24.04のGitHub hosted runnerでは、AppArmorとChrome for Testingの組み合わせに
対応するため、CI jobだけで `CHROME_NO_SANDBOX=1` を指定する。
この指定は破棄されるrunnerで、すべてのページ応答を管理下のfixtureへ差し替えるテスト用。
ローカル実行ではsandboxを有効にする。実サイトや信頼できないページを開くテストに
変更するときは、この指定を外してsandboxの動く実行環境を用意する。
背景は [PuppeteerのUbuntu AppArmorに関する説明](https://pptr.dev/troubleshooting#issues-with-apparmor-on-ubuntu) を参照。

手動確認は `chrome://extensions/` でデベロッパーモードを有効にし、
「パッケージ化されていない拡張機能を読み込む」で `extension/` を指定する。
JS変更後は拡張と対象ページをreloadする。実サイトでの対象・対象外の操作も確認する。

CIのAction依存は [GHA部品](../../parts/github-actions/README.md) に従い、コピー先でlockを生成する。
未対応環境では添付workflowのSHA固定を維持する。

## テストの定番

- 条件が一致した要素だけに適用される。
- 見出し・要素の種類などが異なる対象へ作用しない。
- 後から追加されたSPAの要素にも適用される。
- 条件が変わったときに自分の装飾を外せる。
- matches外のoriginではJSもCSSも適用されない。

参照元のように自動クリック・一時非表示がある場合は、再試行の上限、
イベントhandlerの準備遅延、失敗時の表示復元、scroll lockの解除まで確認する。
既存のサイト状態を壊さないことを、fixtureと実サイトの両方で確認する。

## 配布と更新

`npm run package` は `dist/extension.zip` を生成する。
node_modules、テスト、開発設定は入れない。ファイルを追加した場合はpackage.jsのallowlistも更新する。
Chrome Web Storeへ出す場合はicons・掲載情報・必要なプライバシー説明等も整え、manifest versionを上げる。
ZIPを検証してから公開する。ストアへのupload・公開はこのCIには含めない。

依存の更新は `npm outdated` で候補を確認し、package.jsonとlockを揃え、
Chromeの実テストも実行する。manifestのmatches・権限を増やした場合は対象外テストも更新する。

## 検証記録と参考資料

2026-10-12: Node 24.16.0、ESLint 10.8.1、Puppeteer 25.6.0。
lint、Manifest V3拡張をloadしたChromeテスト（5件）が成功。
ZIPはmanifest.json・content.js・content.cssのみで、manifestがルートにあることを確認した。
利用先の実サイトでの手動確認とChrome Web Storeへの公開は未実施。

- [参照元のmanifest](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/manifest.json)
- [参照元のテスト](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/test/extension.test.js)
- [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)
- [Puppeteerでの拡張load](https://pptr.dev/guides/chrome-extensions)
- [Chrome Web Storeの配布準備](https://developer.chrome.com/docs/webstore/prepare)
