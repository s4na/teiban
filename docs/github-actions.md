# GitHub Actionsの定番

## まず決める方針

CIは、ローカルで行うcheck・test・buildを再現する場所にする。
workflow固有の複雑な処理を増やす前に、プロジェクト側のコマンドを揃える。
[VoidZero＋Go](web-voidzero-go.md)なら、フロント・Go・workflow自体の検査を分けると見通しがよい。

| 項目 | 初期値・考え方 |
| --- | --- |
| 起動 | 通常の検証はpull_requestとdefault branchへのpush |
| 権限 | contents: readを基本にし、writeは必要なjobだけへ渡す |
| checkout | 通常の検査はPRのmerge結果。persist-credentials: falseを採用 |
| 環境 | runnerのOS系統、言語・package manager・検査ツールの版を明示 |
| 再現性 | lockfileを変更しない依存導入。Actionの依存も固定 |
| 待ち時間 | jobのtimeoutと、同じPRの古い検証をキャンセルするconcurrency |
| 検査 | 整形・lint・型検査・test・build。workflowにはactionlintとzizmor |
| 更新 | Dependabot等で更新PRを作り、設定とlockの差分を一緒にレビュー |

必須チェックをpath filterで起動しなくすると、マージに必要な結果が返らない場合がある。
monorepoでは、変更のない領域も含めて最終結果を返す方法を設計してから絞り込む。
job名はbranch protection等から参照されるため、変更時はそちらも確認する。

## Actionの固定: actions.lockを使えるか確認する

`gh actions-lock` はGitHub公式のCLI拡張。
Actionの参照を解決し、`.github/workflows/actions.lock` にcommitとidentityを記録する。
対応環境では、workflowの読みやすい参照と、実際に実行するcommitを分けて管理できる。

2026-10-12時点ではプレビューで、GHESは対象外。
採用するリポジトリ・runner・schema / CLIの対応を確認する。
lockの利用と、管理ポリシーでlockを強制することは別の条件として確認する。
未対応なら、`uses` を40桁commit SHAで固定し、コメントにリリース版を残す。

```sh
# 確認時点の導入例。採用するCLI版の互換性を確認してpinする
gh extension install github/gh-actions-lock --pin v0.1.6

# リポジトリのルートで生成し、workflowと一緒にコミットする
gh actions-lock

# GitHub上の参照・identityを含めて検証する
gh actions-lock --verify
```

通常の生成と、更新のための `--relock` は目的が異なる。
`--verify-local` はofflineでのcoverage確認で、上流の正当性を検査する代わりにはならない。
Actionやworkflowの追加・削除もlockの更新対象にする。lockfileは生成ツールで更新する。

移動・改名等で検証が失敗した場合は、変更理由を確認する。
`--accept-moved` の自動実行で検証を通す運用にしない。
再利用workflowの内部は定義元のlockで管理する。
Actionが実行時に取得する任意のパッケージまで、このlockが固定するわけではない。

## workflow自体のlint

actionlintは構文・式等、zizmorは権限・未固定参照・入力の扱い等を検査する。
`.yml` と `.yaml` の両方を対象にする。actionlintは引数なしでリポジトリ内のworkflowを発見できる。
reusable workflowも依存として扱い、stepのusesだけを確認して終わらない。

lockとlintの対応範囲は、採用する版で確認する。
例えば確認時点のzizmor 1.30.0はnative lockを認識せず、タグ参照を未固定と判定する。
この場合はSHA固定を使うか、lock検証を必須にした上で該当行だけに理由付きの除外を置く。
監査全体を無効にしない。lock未対応環境へ移すときは除外も見直す。

## PRコード・secret・デプロイの扱い

通常のPRの検査には `pull_request_target` を使わない。
管理用イベントでwrite権限を使う場合は、PR headのコードを実行しない設計を確認する。
PRタイトル等の入力をshellへ直接埋め込まず、env経由で渡して引用する。

デプロイは検査jobと権限を分け、environmentや保護条件を設ける。
対応サービスならOIDCで短期間の資格情報を使う。
forkのPRにsecretが渡らない前提で、検査と公開の入口を決める。

## 更新とキャッシュ

Dependabot等にActionと言語の依存を登録し、major更新を他と分けて確認する。
週次更新、関連依存のgroup化、version updateのcooldownは運用に合わせて選ぶ。
例えば公開から7日待つ方針にしても、security updateまで同じ待機条件にしない。
各ecosystem・lock形式への対応と、更新対象のディレクトリを確認する。

Dependabotのgithub-actionsの対象はルートのworkflow等で、別ディレクトリの説明用ファイルが
自動更新されるとは限らない。記事や別管理の設定にも同じActionを記載した場合は追随を確認する。

キャッシュは、CIが動いてから遅い部分へ導入する。
lockfile・OS・toolchain等をキーへ含め、依存更新時に古い結果を使わないようにする。
キャッシュを使わない実行でも成功することを確認し、キャッシュへsecretを入れない。

## 導入時に確認すること

1. ローカルの確認コマンドと、CIの実行ディレクトリを揃える。
2. PR・default branch・公開イベントの起動条件と権限を分ける。
3. 対応環境ならlockを生成し、それ以外はSHA固定にする。
4. workflowのlint・lock検証を含め、実際にGitHub上で結果を確認する。
5. 必須チェック、依存更新、キャッシュ、デプロイ条件を設定する。

## 参考資料

確認日: 2026-10-12。プレビューの利用条件とツールの対応は導入時に再確認する。

- [gh-actions-lock](https://github.com/github/gh-actions-lock)
- [GitHubのworkflow dependency lockfiles](https://docs.github.com/en/enterprise-cloud%40latest/actions/concepts/security/workflow-dependency-lockfiles)
- [lockの強制とDependabot更新](https://docs.github.com/en/actions/how-tos/administer/enforce-workflow-lockfiles)
- [Dependabotの設定項目](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)
- [actionlint](https://github.com/rhysd/actionlint)
- [zizmor](https://docs.zizmor.sh/)
