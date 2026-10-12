# 小さなChrome拡張を作るときの定番

## 用途とまず採用する構成

特定サイトのDOMへ小さな機能を加えるChrome拡張を想定する。
参考は [chatgpt-rate-limit-modal-dismiss](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/tree/2aee4c8eec89e6d58e7126bf463ee5dd641438ba)。
確認時点のcommitは `2aee4c8eec89e6d58e7126bf463ee5dd641438ba`。
サイト固有のモーダルdismiss処理より、権限・対象判定・失敗時の扱い・テストの方針を定番にする。

| 項目 | まず採用するもの | 追加が必要になる目安 |
| --- | --- | --- |
| manifest | Manifest V3 | 対応ブラウザの仕様を確認する |
| ページ操作 | content script | ページ側のJS環境との通信が必要なら境界を設計 |
| JS | 素のJavaScript＋ESLint | 規模・型・UI要件に応じてTypeScript等を追加 |
| UI | content scriptと必要なCSS | popup・options等の画面が必要なら別途設計 |
| background | 必要になるまで置かない | イベント・API等に応じてservice workerを追加 |
| テスト | Node標準test等＋Puppeteer | 実Chromeへ拡張をloadして結果を見る |
| package manager | npm等を一つ選ぶ | package managerとlockfileを揃える |

Webアプリと同じbuild基盤が必要とは限らない。
複数画面・依存のbundleが必要になってから、[VoidZero等の構成](web-voidzero-go.md)を検討する。

## manifestと権限

name・version・description、content_scriptsのmatches・JS・CSS・run_atを明示する。
matchesは必要なHTTPS originへ絞り、URLのpathやframeの範囲も確認する。
通常はdocument_idleを起点にし、描画前の処理が必要な場合にdocument_startを選ぶ。

必要な機能を先に決め、permissions・host_permissionsはAPIや処理に必要なものだけ追加する。
content scriptだけで足りる機能に、tabsや広いhost権限を一律に付けない。
権限やmatchesを増やす更新は、対象外での動作と利用者への影響も確認する。

content scriptのJS実行環境とページのJS実行環境を区別する。
DOMを操作できることと、ページの変数・関数へ直接アクセスできることは同じではない。
ページとのmessage通信が必要なら、入力の検証と受け付ける範囲を決める。

## DOM操作とSPAへの対応

対象をselectorだけで判定せず、要素の種類・見出し・状態等も組み合わせる。
自動クリックや非表示の操作は、似ている別のUIへ作用しないことを優先する。
サイトのDOM変更で条件が合わなくなったら、誤操作せず処理を見送れるようにする。

初回の走査だけでは、SPAが後から追加・更新する要素を扱えない。
MutationObserver等を使う場合は、子要素の追加・削除（childList）、既存のテキストノードの変更
（characterData）、必要な属性（attributes）のどれを監視するかを決める。
テキストノード自体が置き換わる変更はchildList、既存ノードの本文だけの変更はcharacterDataで扱う。
毎回ページ全体を走査する必要があるか、対象範囲を絞れるかも考える。

- 同じ対象へ何度実行しても、イベント登録や操作が重複しないようにする。
- 自分のDOM変更でobserverが再発火しても、不要な書き換えを繰り返さない。
- SPAがclassや属性を書き換えた場合も、必要な装飾・処理を維持できるようにする。
- 元のclass・style等を変更するときは、サイト側の状態を不用意に失わない。

参照元のようなモーダル操作では、表示を隠しただけで成功としない。
クリックhandlerの準備、閉じた結果、scroll lock等の画面状態も確認する。
一時非表示や再試行を使うなら、回数・待ち時間に上限を設け、失敗時は操作できる状態へ戻す。

## lintとテスト

ESLintでは、ブラウザ用のcontent scriptと、Node用のtest・package処理を分けて設定する。
配布するコードの整形・lintと、開発用コードの検査の範囲を明確にする。
TypeScriptを採用する場合はbuildと型検査を分け、配布物に不要な開発設定を混ぜない。

DOMへJSを直接注入するテストだけでは、manifestのmatchesや注入時期は確認できない。
Puppeteerでは対応するChromeへunpacked extensionをloadし、拡張としての動作を確認する。
別プロファイルを使い、個人のブラウザ状態へ依存しないようにする。

| 確認すること | 目的 |
| --- | --- |
| 対象条件に一致するDOM | 必要な機能が実行される |
| 似ているが条件外のDOM | 誤操作しない |
| SPAによる追加・更新 | 初回load以外にも対応できる |
| matches外のURL | JS・CSSが適用されない |
| class・属性の書き換え | 状態を復元でき、変更ループしない |
| 非表示・自動クリックの失敗 | 表示や操作状態を復旧できる |

fixtureは実サイトの状態を再現し、文字コードも明示する。
ローカルfixtureで条件を検査し、実サイトでもselector・動作・対象外の操作を手動確認する。
CIは [GitHub Actionsの方針](github-actions.md) に沿ってlint・test・配布物の生成確認を行う。

PuppeteerのChrome取得や拡張load APIは、採用する版と環境に合わせて確認する。
UbuntuのAppArmor等でsandboxが起動できない場合も、まず対応環境を整える。
`--no-sandbox` を選ぶのは、破棄されるrunnerで管理下のfixtureだけを開く等、
適用条件を限定したテストにする。実サイトや信頼できないページのテストへ流用しない。

## 配布と更新

配布ZIPのルートにmanifest.jsonを置く。
配布対象を明示したallowlistでまとめ、node_modules・テスト・開発設定・secretを入れない。
ZIPの中身を確認してから、実際に読み込めることを確認する。

Chrome Web Storeへ出す場合は、icons・掲載情報・必要なプライバシー説明を整える。
公開する更新ではmanifest versionを上げ、配布物の版と揃える。
CIでのpackage生成とストアでの公開は、別の権限・操作として設計する。

依存更新時はpackage.jsonとlockfileを揃え、実Chromeのテストも実行する。
Chromeのmanifest.jsonのversionは、拡張の新しい版を公開するときに別途更新する。
サイト側のDOM変更は依存更新とは別に起こるため、対象判定が崩れた場合の挙動も残しておく。

## 導入するときの順序

1. 対象URL、追加する機能、必要な権限を決める。
2. content scriptで足りるか、popup・service worker等が必要か判断する。
3. 対象条件、SPA対応、重複実行・失敗時の扱いを決める。
4. lintと、拡張をloadしたテスト、実サイトの手動確認を揃える。
5. 配布ファイル・ZIP・version更新・公開手順を決める。

## 参考資料

確認日: 2026-10-12。参照元の機能固有の実装ではなく、判断と確認方法を一般化した。

- [参照元のmanifest](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/manifest.json)
- [参照元のテスト](https://github.com/s4na/chatgpt-rate-limit-modal-dismiss/blob/2aee4c8eec89e6d58e7126bf463ee5dd641438ba/test/extension.test.js)
- [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)
- [Puppeteerでの拡張load](https://pptr.dev/guides/chrome-extensions)
- [Puppeteerの実行環境とsandbox](https://pptr.dev/troubleshooting)
- [Chrome Web Storeの配布準備](https://developer.chrome.com/docs/webstore/prepare)
