# VoidZero＋GoでWebアプリを作るときの定番

## 用途とまず採用する構成

ブラウザ側をTypeScript、APIをGoで作るWebアプリを想定する。
VoidZeroのツール群をフロントエンドの開発基盤に寄せ、Goは独立したツールチェーンとして扱う。

| 領域 | まず採用するもの | 考え方 |
| --- | --- | --- |
| UI | TypeScript＋Reactなど | Reactは一つの選択肢。UIの要件に合わせてVue等も選ぶ |
| 開発・build | Vite+ | Vite / Rolldownを含むツール群の導入・実行をまとめる |
| JS/TS整形 | Oxfmt | formatterの入口を一つにする |
| JS/TS lint | Oxlint | 型を使う検査と、型エラーの検査も明示的に有効化する |
| JSテスト | Vite+に含まれるVitest | build系とテスト系の依存の整合性を保つ |
| CSS | 標準CSS＋必要ならStylelint | 整形とCSSのルール検査は役割を分ける |
| API | Goのnet/http | 小さく始め、routing・middleware等の必要性でframeworkを選ぶ |
| Goの品質検査 | gofmt、go vet、golangci-lint、go test | フロントのツールにGoの検査まで任せない |

「VoidZeroに寄せる」は、JSのbuild・整形・lint・テストの担当を揃えること。
CSS、Go、workflowの検査には、それぞれに適したツールを組み合わせる。

## リポジトリとツールの揃え方

同じリポジトリなら、例えば `web/` と `api/` に分ける。
package.jsonとGo moduleの境界を明確にし、言語ごとの依存を独立して更新できるようにする。
複数のJS packageが必要になるまでは、workspace・共通packageの抽出を必須にしない。

- Nodeは採用するLTS系統を決め、ローカル・CI・開発環境で揃える。
- package managerを一つに決め、packageManager欄等で版も記録する。
- JSはmanifestとlockfile、Goはgo.modと必要なgo.sumをコミットする。
- CIではJSのlockfileを更新しないインストールを使う。
- コマンドはpackage.jsonのあるディレクトリで実行する。Corepackもその設定を基準にする。

Vite+では、その版の公式導入手順に従ってVite / Vitestの依存を揃える。
pnpmのoverridesを使う場合は、同梱coreやVitestの版を確認する。
Vite+ coreのpackage versionをVite本体のversionと同じものとして扱わない。
独立したVite・Vitestや古いpluginのpeer dependencyが混ざっていないかを見る。

## JS/TS・CSSの設定で押さえる点

`vp check` に整形確認・lint・型検査をまとめる。
Vite+の `lint.options.typeAware` と `typeCheck` は役割が異なるため、両方の採用を検討する。
buildが通ることと、TypeScriptの型検査が通ることは別の確認として扱う。
既存プロジェクトを移すときは、Oxlintで扱えないESLint pluginのルールを確認する。

整形は一つのツールに担当させ、editorのformat-on-saveとCIを同じ設定に寄せる。
CSSの整形をOxfmtへ寄せても、CSSのルール検査が必要ならStylelintを追加する。
標準CSSを初期値にし、Sass・Tailwind・CSS-in-JSは採用したときに対応ルールを選ぶ。
生成物・依存ディレクトリは整形・lintの対象から外す。

テストの探索対象には、通常のTSだけでなく、採用するUIのTSX等も含める。
DOMを扱うテストには適切な実行環境を選び、純粋なロジックまでブラウザ依存にしない。
重要な画面操作やAPIとの接続は、単体テストと別に確認する。

## Goの設定で押さえる点

Goの版をローカル・CIで揃え、golangci-lintはそのGo版に対応した版を選ぶ。
linterの設定形式はmajor versionで異なるため、古い設定をそのまま流用しない。
最初から大量のlinterを有効にせず、問題を検出できるルールを選んで育てる。

| 確認 | 役割 |
| --- | --- |
| gofmt | 整形。CIでは未整形ファイルを検出する |
| go vet | Go標準の静的解析 |
| golangci-lint | 採用したlinterをまとめて実行 |
| go test | API・ロジックの振る舞いを確認 |
| go test -race | 対応環境で並行処理の問題を検出 |
| go build | 配布・起動対象をbuildできることを確認 |

race検査は対応OS・CPUとCGOの条件を確認する。
HTTP serverにはtimeout、起動・終了処理、ログの方針を持たせる。
ヘルスチェックはプロセスの応答確認と、DB等を含むreadinessを区別する。

## フロントとAPIの境界

開発時はViteのproxyで `/api` をGoへ転送し、ブラウザからは相対URLを使うと扱いやすい。
開発のためだけにCORSを広く許可する設定を、本番へ持ち込まない。
Viteの開発proxyはproduction buildに含まれない。
本番では同一originへの配信・転送、または別originにする場合のCORS・認証を別途設計する。

APIのrequest / responseとエラー形式を決める。
TSの型だけでは外部のJSONを検証できないため、必要な境界で実行時検証を行う。
APIが増えたらOpenAPI等による型生成を検討する。
ブラウザへ渡せる環境変数と、Go側だけで使うsecretを分ける。

## 導入と更新の順序

1. UI framework、Node・Goの系統、package managerを決める。
2. Vite+の公式手順でフロントを導入し、依存の重複・版の整合性を確認する。
3. JS/TS・CSS・Goのcheckコマンドと、editorの設定を揃える。
4. APIの境界と開発proxy、本番の配信方法を決める。
5. ローカルのcheck・test・buildを通し、GitHub Actionsへ同じ確認を載せる。

CIの記事は後続で追加する。コマンド名は各プロジェクトのscriptsにまとめる。
更新時はmanifestとlockfileを同時に更新し、Vite+の同梱版・overrides・pluginの互換性も確認する。
GoやNodeの更新も、linter・CI runnerとの整合性を含めて扱う。

## 参考資料

確認日: 2026-10-12。導入時は採用する版の公式資料で設定名・対応範囲を確認する。

- [Vite+のローカルCLI・依存の揃え方](https://viteplus.dev/guide/local-cli)
- [Vite+ check](https://viteplus.dev/guide/check)
- [Oxfmt](https://oxc.rs/docs/guide/usage/formatter.html)
- [Stylelintの導入](https://stylelint.io/user-guide/get-started/)
- [Go net/http](https://pkg.go.dev/net/http)
- [golangci-lintの設定](https://golangci-lint.run/docs/configuration/)
