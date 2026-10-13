# GitHub Actionsの定番

CIはローカルのcheck・test・buildを再現する。言語ごとのjobとworkflow自体の検査を分け、
共通の依存更新ルールは[依存管理テンプレート](dependency-updates.md)を使う。

## 最初のworkflow

`api/` にGo moduleがある場合の `.github/workflows/ci.yml` の例。
Go版はコミット済みの `api/go.mod` の `go` / `toolchain` とローカルで揃える。
JSやgolangci-lint等の検査は、対象のツールを準備したjobで[Webの定番](web-voidzero-go.md)と同じコマンドを実行する。

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
jobs:
  go:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    defaults:
      run:
        working-directory: api
    env:
      GOFLAGS: -mod=readonly
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          persist-credentials: false
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e # v7.0.0
        with:
          go-version-file: api/go.mod
          cache: false
      - name: Check, test, build
        run: |
          unformatted="$(gofmt -l .)"
          test -z "$unformatted"
          go vet ./...
          go test ./...
          go build ./...
          dependency_changes="$(git status --porcelain -- go.mod go.sum)"
          test -z "$dependency_changes"
```

例のActionは2026-10-13時点で公開後7日以上経過した版のSHAを確認済み。転記時にも版とrunner互換性を確認する。
通常のPRはcheckout既定のmerge結果を検査し、公開jobへ流用しない。
並行処理を使うGoでは、対応OS・CPU・CGOを確認して `go test -race ./...` も加える。

- 必須jobをpath filterだけで省略すると結果待ちが残る。monorepoは変更なしでも最終結果を返す構成にする。
- job名を変えるときはbranch protection等の必須チェック名も更新する。
- JSの依存導入は採用したpackage managerのfrozen-lockfile相当を使う。

## Actionの固定方式を選ぶ

| 条件 | 採用する方式 | 注意点 |
| --- | --- | --- |
| runnerがnative lockを適用する環境 | `gh actions-lock` | 対応repo・runner・schema / CLI、lockを強制するポリシーを別々に確認 |
| それ以外 | pinactで40桁SHA固定＋版コメント | 外部Actionと再利用workflowが対象。推移依存まで固定する保証はない |

2026-10-13時点でnative lockはEnterprise Cloud向けプレビュー、GHESは対象外。
Free・Pro・TeamではSHA固定を使う。CLIでlockを生成できることと、runnerで適用されることを混同しない。
SHA固定ではcomposite Action内部の可変参照も確認し、必要なら内部参照を管理できるActionを選ぶ。
pinactの固定・checkは[共通テンプレート](dependency-updates.md)を参照する。

### native lockを採用する場合

互換性を確認したCLIを使う。以下はv0.1.6の例。

```sh
gh extension install github/gh-actions-lock --pin v0.1.6
gh actions-lock                         # 生成。workflowと一緒にコミット
gh actions-lock --verify                # 上流の参照・identityを検証
gh actions-lock --verify-local --no-fix  # offlineで読み取りのみ
```

- `--relock` は依存を更新するときに使う。追加・削除時もlockを再生成し、workflowの変更を含む差分を確認する。
- v0.1.6の `--verify-local` 単独はローカル参照を移行し得る。offline検査は上流検証の代わりにならない。
- 移動・改名で失敗したら理由を調べ、`--accept-moved` で自動承認しない。
- 再利用workflowの内部は定義元のlockで管理する。実行時に取得する任意のpackageまでは固定されない。

## workflowを検査する

版を揃えたツールを導入し、リポジトリのルートで実行する。

```sh
actionlint
zizmor --strict-collection .
```

`.yml` / `.yaml` と再利用workflowも対象にする。actionlintは構文・式、zizmorは権限・入力・未固定参照等を検査する。
native lockへの対応はツールの採用版で確認する。確認済みのzizmor 1.30.0はlockを認識しないため、
SHA固定にするか、lock検証を必須にして該当行だけに理由付き除外を置く。監査全体は無効にしない。

## 入力・公開・キャッシュ

PRタイトル等をshellへ直接埋め込まず、env経由で引用する。既存jobへ加えるstepの例:

```yaml
- name: Show PR title
  if: github.event_name == 'pull_request'
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: printf '%s\n' "$PR_TITLE"
```

- 通常のPR検査に `pull_request_target` を使わない。管理イベントでwrite権限を使うときはPR headを実行しない。
- デプロイは検査とjob・権限を分け、environmentの保護条件と、対応先ではOIDCを使う。fork PRへsecretが渡らない前提にする。
- キャッシュはCIが通ってから導入する。lockfile・OS・toolchainをキーに含め、キャッシュなしでも検証し、secretを入れない。
- Dependabotが記事内のAction例まで更新するとは限らない。設定と記事の版も追随させる。

## 参考資料

確認日: 2026-10-13。例のGitHub上での実行・lintは未実施。導入先で検証する。

- [workflow構文](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)、[concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [checkout v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1)、[setup-go v7.0.0](https://github.com/actions/setup-go/releases/tag/v7.0.0)
- [native lockの利用条件](https://docs.github.com/en/enterprise-cloud%40latest/actions/how-tos/secure-your-work/lock-workflow-dependencies)、[lockの強制とDependabot](https://docs.github.com/en/actions/how-tos/administer/enforce-workflow-lockfiles)
- [gh-actions-lock v0.1.6](https://github.com/github/gh-actions-lock/blob/047fddf38163b304f1e6ef5649f5ac1646edc6a3/README.md)、[verify-localの実装](https://github.com/github/gh-actions-lock/blob/047fddf38163b304f1e6ef5649f5ac1646edc6a3/cmd/gh-actions-lock/verify.go#L35-L42)
- [actionlint](https://github.com/rhysd/actionlint)、[zizmor](https://docs.zizmor.sh/)、[確認済みzizmor 1.30.0](https://github.com/zizmorcore/zizmor/tree/fb814d6687450fc8e0b0fba8d958b1ac40c0647f)
