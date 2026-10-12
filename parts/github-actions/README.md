# GitHub Actionsの定番

## 用途と前提

Web＋Go構成のCIと、Action依存の固定・更新・検証を揃える部品。
`ci.yml` は新しいリポジトリの `.github/workflows/ci.yml` へコピーする例。
`teiban` 自身の [CI](../../.github/workflows/ci.yml) は、構成例の配置に合わせた実行版。

## 初期設定

| 項目 | 方針 |
| --- | --- |
| 起動 | `pull_request` とmainへのpush。必須チェックをpath filterで消さない |
| 権限 | `contents: read`。公開・書き込みが必要なjobにだけ追加する |
| checkout | `persist-credentials: false`。通常のCIはPRのmerge結果を検証 |
| 実行環境 | runnerのOS版を指定し、Node・pnpm・Go・検査ツールの版を揃える |
| CIの処理 | ローカルと同じcheck、CSS lint、test、build、Go検査 |
| 待ち時間 | jobのtimeout、同じPRの古い実行のキャンセル |
| キャッシュ | 最初は使わない。時間が必要になったらlockfileに紐づけて導入 |
| workflow検査 | actionlintで構文・式、zizmorで権限・注入等を確認 |
| Action依存 | 対応環境では `actions.lock`、未対応環境では40桁SHA固定 |
| 更新 | Dependabotの週次PR＋公開から7日のcooldown。設定とlockfileを同じ変更で揃える |

通常のPRコードの検査には `pull_request_target` を使わない。
デプロイ時の資格情報は専用job・environmentへ分け、対応するサービスならOIDCを使う。
PRタイトル等をshellの式へ直接埋め込まず、必要な場合はenv経由で扱う。

## gh actions-lock

GitHub公式のCLI拡張。workflowで指定したActionの参照を解決し、
`.github/workflows/actions.lock` にcommitとリポジトリの識別情報を記録する。
2026-10-12時点ではプレビュー。GHESは対応対象外で、schemaとCLIの互換性も確認が必要。
GitHub Enterprise Cloudの管理ポリシーは別機能なので、全プランで強制可能とは扱わない。

対応しているリポジトリでworkflowを登録すると、lockされたcommitが実行対象になる。
再利用workflowの内部は定義元リポジトリのlockで管理される。
lockはActionが実行中に取得する任意のパッケージまで固定するものではない。

```sh
# 初回導入（gh CLIとGitHubへの認証が必要）
gh extension install github/gh-actions-lock --pin v0.1.6

# コピー先のリポジトリのルートで生成する
gh actions-lock

# GitHub上の参照・identityも含めて確認（CIで使う）
gh actions-lock --verify

# ローカルのcoverageのみ確認（offline、上流の正当性は検査しない）
gh actions-lock --verify-local
```

workflowと生成したlockfileを同じコミットに含める。lockfileは手で編集しない。
この部品にはコピー用のlockを置かず、コピー先の全workflowを対象に生成する。
Actionまたはworkflowの追加・削除でも再生成する。

通常の生成は、記録済みの可変参照を最新へ進めない。
更新する場合は `gh actions-lock --relock` を実行し、差分をレビューする。
検証が失敗したときは移動・削除・改名等の理由を確認する。
`--accept-moved` を自動で実行して検証失敗を通さない。

この例のzizmor 1.30.0はlockを認識せず、タグ参照を未固定と判定する。
そのため `uses` 行だけに理由付きの `unpinned-uses` 除外を置き、
別の必須チェックで `gh actions-lock --verify` を実行する。その他の監査は有効。
lock未対応の環境へ持ち込む場合は、タグを40桁SHA＋版コメントに変え、除外を削除する。
`gh actions-lock` はSHAからタグへの変換も行うため、SHA方式と混ぜて無条件に生成しない。

## 導入と更新

1. `ci.yml` をコピーし、作業ディレクトリ・package.jsonの位置・Node・Go版を合わせる。
2. 上記のCLIでlockを生成する。新しいworkflowの追加時もこの工程が必要。
3. `actionlint`、`zizmor --offline .github/workflows/ci.yml`、lockの検証を実行する。
4. GitHub上でCI成功を確認してから、web・api・workflowsを必須チェックとして設定する。
5. Dependabotに `github-actions` とnpm（pnpm）の対象ディレクトリを指定する。

Dependabotは既にlockへ登録したActionの更新とlock再生成を扱う。
新規workflowの登録は人が生成する。
Dependabotが走査するのはルートのworkflowで、コピー用の `parts/github-actions/ci.yml` は対象外。
CIの `scripts/check_action_versions.py`（Python 3.9以降＋Ruby標準YAML）が、
stepのActionとjobのreusable workflowを含めて両者の参照の一致を確認するため、
更新PRではコピー用の参照も同じ版へ更新する。
Chrome拡張・Homebrewのコピー用workflowも、実行用CIと共通するActionはlockのSHAと比較する。
その構成だけで使うActionはSHA固定し、利用先の用途に応じて更新する。
Vite+本体の更新はcoreとVitestのoverrideも合わせる。
ブランチ保護・environment・管理ポリシーの設定は利用先リポジトリで行う。

チェーンPRは親をbaseにするため、マージは親から順に行う。
親をsquash mergeすると子に親のコミットが残る。子のbaseをmainへ変えた後の差分を確認し、
履歴を整理する場合は別途その操作を明示して実施する。

## 検証記録と参考資料

2026-10-12: gh-actions-lock 0.1.6で実際のCIのlockを生成し、6依存（推移依存含む）を記録。
actionlint 1.7.12、zizmor 1.30.0、lockのoffline・上流検証を実行する。
GitHub上のCI結果はPRのchecksに残す。

- [gh-actions-lock](https://github.com/github/gh-actions-lock)
- [GitHubのworkflow dependency lockfiles](https://docs.github.com/en/enterprise-cloud%40latest/actions/concepts/security/workflow-dependency-lockfiles)
- [lockの強制とDependabot更新](https://docs.github.com/en/actions/how-tos/administer/enforce-workflow-lockfiles)
- [actionlint](https://github.com/rhysd/actionlint)
- [zizmor](https://docs.zizmor.sh/)
