# Webアプリ: VoidZero＋Go

## 用途と前提

ブラウザのUIをTypeScript、HTTP APIをGoで作る場合の初期設定。
UIの初期案はReact。Vue等へ変える場合も、整形・lint・テストの担当を揃える方針は使える。
同一リポジトリの `web/` と `api/` に分け、言語ごとの依存関係を混ぜない。

## 採用する設定

| 対象 | 初期値 | 理由 |
| --- | --- | --- |
| UI | React＋TypeScript | 型を使ってUIを組み立てる構成例として選ぶ。フレームワークは用途で変更する |
| JSの開発・build | Vite+のVite / Rolldown | VoidZeroのツールを一つのローカル依存に揃える |
| JS/TSの整形・lint・型検査 | Oxfmt＋Oxlint＋型検査を `vp check` で実行 | コマンドと設定の入口をまとめる |
| JSテスト | Vite+に含まれるVitest | ツール本体とテストランナーの版を揃える |
| CSS | Oxfmtで整形、Stylelintで検査 | JSのlintとCSSのlintは別の役割。標準CSSから始める |
| API | Go標準の `net/http` | 小さなAPIのためにWebフレームワークを必須にしない |
| Goチェック | gofmt、go vet、golangci-lint v2、go test -race | 整形、静的解析、振る舞い・raceの検出を揃える |
| 依存関係 | pnpm / pnpm-lock.yaml、go.mod | Vite+推奨のoverrideを利用。ローカルとCIはfrozen lockfileで揃える |

Vite+の `lint.options.typeAware` と `typeCheck` を両方有効にする。
buildだけでは型検査の代わりにならないため、`check` と `build` を両方実行する。
独立したVite・Vitestのコピーが混在しないよう、pnpm overridesをVite+の同梱版に合わせる。
Vite+ coreのpackage versionはVite本体と異なるため、`peerDependencyRules.allowedVersions` は
検証したcoreの版だけを許可する。更新時はこの値も合わせる。

CSSは素のCSSを初期値とし、Sass、Tailwind、CSS-in-JSを使うときに対応する設定を追加する。
Goの依存追加時は `go mod tidy` でgo.sumもコミットする（この例は標準ライブラリのみ）。

## 導入

1. このディレクトリのREADME以外を新しいリポジトリのルートへコピーする。隠しファイルも含める。
2. `web/package.json` の名前・versionと `api/go.mod` のmoduleを変更する。
   module変更時は `api/cmd/server/main.go` のimportも合わせる。
3. `web/.node-version` のNode.js、pnpm 12.4.1、Go 1.26系、golangci-lint 2.13.2を用意する。
   golangci-lintの導入例は `go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.13.2`。
   `$(go env GOPATH)/bin` がPATHに必要。
4. `make install`、`make check` を実行する。グローバルの `vp` は不要。
   pnpmは `web/` 内で起動する。Corepack利用時も、そのpackage.jsonの版指定を選ばせる。
   Socket Firewallを使う環境では `make PNPM="sfw pnpm" install` のように実行する。

```sh
# この構成例のディレクトリ（コピー後は新しいリポジトリのルート）で
make install
make check

# 別々のターミナルで起動
make dev-api
make dev-web
```

`http://localhost:5173` を開くとGo APIへの接続結果が表示される。
`GET /api/health` をVite開発サーバーから `127.0.0.1:8080` へproxyする。
フロント側は `/api/health` の相対URLを使うため、開発用にCORSを広く許可する必要がない。

このhealthはHTTPプロセスの応答確認。DB等を導入する場合のreadinessは別途設計する。
productionでは `web/dist/` の配信と `/api` の転送を同一originで用意する。
Viteの開発proxyはbuildには含まれない。デプロイ先、DB、認証、APIスキーマ生成は利用するアプリで決める。
外部からAPIへ接続する環境では `LISTEN_ADDR` とreverse proxyを設定する。

## コマンド

| 操作 | コマンド |
| --- | --- |
| 依存導入 | `make install` |
| 全チェック | `make check` |
| 整形 | `make fmt` |
| JS/TS・CSS整形の確認、JS/TS lint・型検査 | `cd web && pnpm run check` |
| CSS lint | `cd web && pnpm run lint:css` |
| JSテスト | `cd web && pnpm test` |
| production build | `cd web && pnpm run build` |
| Goのみ | `cd api` 後、`go vet ./...`、`golangci-lint run`、`go test -race ./...`、`go build ./...` |

CIもこれらのコマンドを実行する。workflowの設定はGitHub Actionsの構成例で追加する。
Goのrace検査はCGOと対応プラットフォームが必要。通常のmacOS/Linux開発環境を対象にする。

## 更新

`cd web && pnpm outdated` で候補を確認し、package.jsonとpnpm-lock.yamlを同時に更新する。
Vite+を更新したら `pnpm exec vp toolchain`（`web/` 内）で同梱版を確認し、
`pnpm-workspace.yaml` のVite / Vitest overrides も揃えてから `make check` を実行する。
Node、Go、golangci-lintの版もCIとローカルを合わせる。

## 検証記録と参考資料

2026-10-12: Node 24.16.0、Vite+ 1.0.0、Go 1.26.3、golangci-lint 2.13.2。
JS/TSの整形・lint・型検査、CSS lint、Vitest、build、Goの整形・静的解析・raceテスト・buildが成功した。
実APIと開発proxyの `/api/health` 接続、Viteによるフロントの配信も確認した。
ブラウザでの画面操作とproductionへのデプロイは未検証。

- [Vite+のローカルCLIと依存の揃え方](https://viteplus.dev/guide/local-cli)
- [Vite+ check](https://viteplus.dev/guide/check)
- [Oxfmt](https://oxc.rs/docs/guide/usage/formatter.html)
- [Stylelintの導入](https://stylelint.io/user-guide/get-started/)
- [Go net/http](https://pkg.go.dev/net/http)
- [golangci-lintの設定](https://golangci-lint.run/docs/configuration/)
