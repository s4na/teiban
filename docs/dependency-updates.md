# 依存管理ポリシーのMarkdownテンプレート

対象プロジェクトの文書へ転記して使う。設定例は実際の構成に合わせ、GitHub Actionsを使わない場合はその節を省く。

## 共通方針

- パッケージ管理にはDependabotを設定する。実際のecosystem・manifestの場所を登録し、未対応の依存は手動で同じ方針を確認する。
- 新規追加・更新は公開から7日以上経過した版に限る。手動更新、security update、lockfile再解決で変わる推移依存も対象とする。
- major更新は他と分け、関連依存のgroup化は互換性とレビューのしやすさに合わせて選ぶ。
- 各 `updates` に `cooldown.default-days: 7` を指定する。SemVer別の日数を省略するか7日以上にし、`include`・`exclude` で待機対象を狭めない。
- 取り込み前に公開日時・変更履歴・manifestとlockfileの差分を確認し、check・test・buildを通す。PR作成日やcommit日時を公開日時の代用にせず、7日未満または公開日時が不明の版は取り込まない。

cooldownは通常のversion updateの候補・PR作成に適用され、security updateやマージ時の検査には適用されない。
設定だけで全更新の7日待機を保証せず、対象バージョンの公開日時を別途確認する。7日待機自体も安全性の保証にはしない。

## Dependabotの設定例

対象の `.github/dependabot.yml` 用。`web/` にnpm系のmanifestがある場合の例で、各ecosystem・ディレクトリに同じcooldownを設定する。

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/web"
    schedule:
      interval: "weekly"
    cooldown:
      default-days: 7
```

`weekly` は調査頻度であり、7日待機の代わりにはならない。
GitHub Actionsは `package-ecosystem: "github-actions"`・`directory: "/"` とし、SemVer別ではなく `default-days` を使う。

## GitHub Actionsを使う場合

- SHA固定を採る場合は、公開後7日以上の具体的なリリース版を選び、`pinact run` で外部Actionと再利用workflowを40桁commit SHAへ固定する。版コメントも残す。
- `pinact run --check` でファイルを変更せず固定漏れを検査し、CIにも組み込む。この確認だけで公開後7日の待機や安全性を検証できたと扱わない。
- `actions.lock` がrunnerで適用される環境では、[GitHub Actionsの定番](https://github.com/s4na/teiban/blob/main/docs/github-actions.md)に従って `gh actions-lock` で生成・検証する。その参照にpinactのSHA固定を一律に重ねず、pinactをlockの生成・検証に使わない。

## 参考資料

確認日: 2026-10-13。利用先での設定・実稼働の検証は別途行う。

- [Dependabotの設定・cooldown](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown)、[対応ecosystem](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
- [pinactの使い方](https://github.com/suzuki-shunsuke/pinact/blob/33cd8b1b95fa2268b348d55145690a050d120012/README.md)、[固定の検査](https://github.com/suzuki-shunsuke/pinact/blob/33cd8b1b95fa2268b348d55145690a050d120012/docs/check.md)
