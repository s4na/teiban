# VoidZero＋GoでWebアプリを作るときの定番

## 用途とまず採用する構成

ブラウザ側をTypeScript、APIをGoで作るWebアプリを想定する。
フロントの開発・整形・lint・テストはVite+にまとめ、Goは独立して検査する。

| 領域 | まず採用するもの | 判断の目安 |
| --- | --- | --- |
| UI | TypeScript＋Reactなど | UIの要件に合わせてVue等も選ぶ |
| 開発・build | Vite+ | 同梱Vite / Rolldownとpluginの互換性を確認する |
| JS/TS整形・lint | Oxfmt＋Oxlint | 型を使うlintと型エラーの検査を有効にする |
| JSテスト | Vite+に含まれるVitest | DOMが必要なテストだけ実行環境を変える |
| CSS | 標準CSS＋必要ならStylelint | 整形とルール検査の役割を分ける |
| API | Goのnet/http | routing・middleware等の必要性でframeworkを選ぶ |

以下はpnpm、`web/`、`api/`を選ぶ例。アプリ一式のテンプレートではない。

## リポジトリと固定する場所

```text
web/
  package.json       # scripts、依存、packageManager
  pnpm-lock.yaml
  vite.config.ts
  tsconfig.json
  src/
api/
  go.mod / go.sum    # go.sumは外部依存に応じて生成
  .golangci.yml
  cmd/server/
  internal/
```

NodeはVite+と同梱Vitestが対応するLTS系統から選び、Goとともにローカル・CIで揃える。
pnpmの版は`packageManager`に記録し、manifestとlockfile、Goのmoduleファイルをコミットする。
複数のJS packageが必要になるまでは、workspaceや共通packageを増やさない。

## フロントの設定と確認

### コマンドの入口

Vite+を開発依存に入れた後、`web/package.json`の`scripts`へ追加する。
scripts内の`vp`はプロジェクトの実行ファイルを使うため、global CLIは必須にしない。

```json
{
  "scripts": {
    "dev": "vp dev",
    "check": "vp check",
    "test": "vp test run",
    "build": "vp build"
  }
}
```

### 型検査・テスト・開発proxy

React、対応する`@vitejs/plugin-react`、TypeScript設定を用意済みの場合の`web/vite.config.ts`。
別のUIではpluginを替え、既存プロジェクトでは必要な設定を残して統合する。

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite-plus";

export default defineConfig({
  plugins: [react()],
  fmt: {
    ignorePatterns: ["dist/**", "coverage/**"],
  },
  lint: {
    ignorePatterns: ["dist/**", "coverage/**"],
    options: {
      typeAware: true, // 型情報を使うlint
      typeCheck: true, // TypeScriptの型エラーも検出
    },
  },
  test: {
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    environment: "node",
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8080",
    },
  },
});
```

`vp check`で整形・lint・型検査を行う。buildの成功だけで型検査を済ませない。
設定名は[Vite+ check](https://viteplus.dev/guide/check)、
[整形](https://viteplus.dev/config/fmt)、[lint](https://viteplus.dev/config/lint)を参照。

- テスト例は`src/`のTS・TSXを対象にする。配置や拡張子を変えたら`include`も変える。
- DOMを使うテストにはjsdom等を別途導入して環境を選ぶ。純粋なロジックはNodeで実行する。
- テストAPIは`vite-plus/test`から読み込める。[同梱runner](https://viteplus.dev/guide/test)と独立したVitestを不用意に混ぜない。
- ESLintから移す場合は、Oxlintで扱えないpluginやルールを確認する。

整形はeditorとCIで同じ設定を使い、依存・生成物を対象から外す。
CSSのルール検査が必要なら[Stylelint](https://stylelint.io/user-guide/get-started/)を追加する。
標準CSSは`stylelint-config-standard`を起点にし、Sass・Tailwind・CSS-in-JSでは対応設定を選ぶ。

### ローカルとCIの共通手順

リポジトリのルートから実行する。失敗した時点で止め、CIではlockfileを更新しない。

```sh
set -eu
cd web
pnpm install --frozen-lockfile
pnpm run check
pnpm run test
pnpm run build
```

lockfileの扱いは[pnpm install](https://pnpm.io/cli/install)を参照。
Stylelintを採用したら、CSS用のscriptもこの手順へ加える。

## Goの設定と確認

golangci-lintは採用するGo版に対応した版を選ぶ。
v2用の`api/.golangci.yml`は標準のlinter群で始め、必要なルールを足す。

```yaml
version: "2"
linters:
  default: standard
```

v1の設定を混ぜず、[設定形式](https://golangci-lint.run/docs/configuration/file/)を確認する。
リポジトリのルートから実行する例:

```sh
set -eu
cd api

unformatted="$(gofmt -l cmd internal)"
if [ -n "$unformatted" ]; then
  printf 'gofmtが必要なファイル:\n%s\n' "$unformatted"
  exit 1
fi

go vet ./...
golangci-lint run
go test ./...
go build ./...
```

`gofmt -l`の出力があれば失敗させる。Goコードの配置を増やしたら整形対象も追加する。
対応OS・CPUとCコンパイラを用意した環境では、`api/`で`CGO_ENABLED=1 go test -race ./...`も実行する。
[gofmt](https://pkg.go.dev/cmd/gofmt)、[Goコマンド](https://pkg.go.dev/cmd/go)、
[race detectorの条件](https://go.dev/doc/articles/race_detector)を参照。

## フロントとAPIの境界

上のproxyは`/api`を削らずにGoへ転送する。Go側も`/api/...`で受け、
ブラウザ側は`fetch("/api/...")`のように相対URLを使う。
[Viteのproxy設定](https://vite.dev/config/server-options.html#server-proxy)を参照。

- 開発proxyはproduction buildに含まれない。本番の同一origin配信・転送、または別originのCORS・認証は別途設計する。
- 開発の都合でCORSを広く許可し、その設定を本番へ持ち込まない。
- request・response・エラー形式を決める。外部JSONはTSの型だけで信用せず、必要な境界で実行時検証する。
- APIが増えたらOpenAPI等の型生成を検討する。ブラウザへ渡す値とGo側だけのsecretを分ける。
- HTTP serverのtimeout、起動・終了処理、ログを決める。プロセスの応答確認と、DB等を含むreadinessを分ける。

重要な画面操作とAPI接続は単体テストとは別に確認する。
serverの設定は[Go net/http](https://pkg.go.dev/net/http)を参照。

## 導入・更新時の確認

- 導入・手動更新も[依存管理ポリシー](dependency-updates.md)の7日待機に従う。
- Vite+のmanifest・lockfile・core alias・同梱Vitestを一緒に確認する。coreのpackage versionをVite本体の版と取り違えず、pluginのpeer dependencyも確認する。
- Node・Goの更新はlinter・CI runnerとの対応も見る。上のcheck・test・buildを通し、[GitHub Actions](github-actions.md)にも同じ確認を載せる。

overridesが必要な場合は、[Vite+の公式導入手順](https://viteplus.dev/guide/local-cli)に従う。
同梱Vitestの版は`web/`で`pnpm exec vp toolchain vitest`を実行して確認する。

確認日: 2026-10-13。設定・コマンドは公式資料に照合したが、例のbuild・testは未実行。
採用する版・UI・実行環境で確認する。React pluginは[公式README](https://github.com/vitejs/vite-plugin-react/tree/main/packages/plugin-react)を参照。
