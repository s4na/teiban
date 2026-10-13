# パッケージ管理・依存更新の定番

## まず採用する方針

パッケージ管理をするプロジェクトではDependabotを設定する。
新規追加・更新とも、取り込むパッケージのバージョンは公開から7日以上経過したものを選ぶ。
公開直後の不具合や不正な更新に気づくための待機期間であり、安全性の確認やテストの代わりにはしない。

Webアプリ、CLI、Chrome拡張などで共通の方針とする。
GitHub Actionsの外部依存にも適用し、固定方法は[GitHub Actionsの定番](github-actions.md)を参照する。

## Dependabotで設定すること

対象プロジェクトの `.github/dependabot.yml` に、実際に使うecosystemとmanifestの場所を登録する。
npm・pnpm・Yarnは `npm`、Go modulesは `gomod`、GitHub Actionsは `github-actions` など、
採用したpackage manager・版・lockfile形式への対応を公式資料で確認して選ぶ。
Dependabot未対応の依存は対象外であることを明示し、手動更新でも7日の待機方針を守る。

各 `updates` エントリーに `cooldown.default-days: 7` を明示する。
SemVer別の日数を省略すれば `default-days` が使われる。
`semver-major-days`・`semver-minor-days`・`semver-patch-days` を追加する場合も7日未満にせず、
`include` で対象を狭めたり `exclude` で待機を外したりしない。
GitHub Actionsは `default-days` に対応するが、SemVer別の日数設定には対応しない。

次は `web/` にJSのmanifestがあるプロジェクトの説明用の例。
Goなどを併用する場合は、そのecosystem・ディレクトリのエントリーにも同じcooldownを設定する。

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

`schedule.interval` は更新を調べる頻度、`cooldown` は公開後の待機期間を決める。
週次の調査だけでは、調査直前に公開された版を候補にできるため、7日の待機を保証できない。
`github-actions` の `directory` は `/` を指定し、ルートのworkflow等を対象にする。
major更新を他と分け、関連依存のgroup化は互換性とレビューのしやすさに合わせて選ぶ。

## 取り込み前に確認すること

cooldownが制御するのは通常のversion updateの候補選定・PR作成であり、マージ時の検査ではない。
security updateには適用されないため、Dependabotの設定だけで全更新の7日待機を保証したと扱わない。
security updateのPRでも、取り込み前に対象バージョンの公開から7日経過したことを別途確認する。

手動更新、新規追加、lockfileの再解決で変わる推移依存にも同じ方針を適用する。
PRの作成日やcommitの日付ではなく、registry等で対象バージョンの公開日時を確認する。
7日未満、または公開日時を確認できない版は取り込まない。

manifestとlockfileの差分、変更履歴、互換性を確認し、対象のcheck・test・buildを通して取り込む。
本文の設定例は方針を説明するものであり、利用先での設定・検証は別途行う。

## 参考資料

確認日: 2026-10-13。対応ecosystemとcooldownの範囲は導入時に再確認する。

- [Dependabotの設定項目・cooldown](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#cooldown)
- [Dependabotの対象ディレクトリ](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference#directories-or-directory)
- [Dependabotが対応するecosystem](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories)
