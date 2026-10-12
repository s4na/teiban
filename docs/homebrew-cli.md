# 自作CLIをHomebrewで配布するときの定番

## 用途と参考にするもの

利用者が `brew install` でCLIを導入・更新・固定できるようにするためのノウハウ。
開発環境用のBrewfileとは分けて、配布する側のtap・Formula・release運用を考える。

参考は [ipv4-runのrelease workflow](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/.github/workflows/release.yml)。
確認時点のcommitは `fb41539767b9da8d30a884f6efde8a75646df4dd`。
参照元はPython CLIだが、版の管理、通常版・固定版・HEAD、再実行の設計は他のCLIにも使える。

## tapと配布方式を決める

通常は `homebrew-<tap>` というリポジトリを用意し、Formulaを管理する。
CLI本体のリポジトリにFormulaを同居させる場合は、tapのURLを明示する。
どちらでも、利用者向けREADMEにtap・install・upgrade・uninstallを載せる。

| 配布方式 | 選ぶ目安・確認する点 |
| --- | --- |
| ソースbuildのFormula | 利用者の環境でbuildする。言語・build依存、取得元、checksumを定義 |
| build済みバイナリ | OS・CPUごとの成果物とchecksumを管理。署名・notarization等も検討 |
| Python等のCLI | runtime依存、専用環境、libexecとlauncherの配置を設計 |

GoReleaserを使う場合は、現在の推奨が `homebrew_casks` である点を確認する。
古い `brews` の例をそのまま採用せず、配布するOS・CPUと方式に合う設定を選ぶ。

長期的にchecksumを固定する配布物は、版付きの名前でRelease asset等へ公開し、
公開後に同じassetを差し替えない方式を初期値にする。ソースbuildでも自分で作ったarchiveを配布できる。
GitHubの自動生成タグarchiveは、同じcommitでも圧縮等の再生成によりbytesが変わる場合があり、
抽出後の内容が同じこととSHA-256が同じことは別になる。
参照元のタグarchive方式を採る場合も、この違いを理解し、固定版のURL・checksumを
長期保持したいなら、自分で公開したarchiveへ寄せる。

## 通常版・固定版・HEADを分ける

| 種類 | 管理の仕方 | 利用者に伝えること |
| --- | --- | --- |
| 通常版 | `<name>.rb` を最新の安定版へ更新 | brew upgradeで更新される |
| 固定版 | `<name>@X.Y.Z.rb` を保持 | 明示した版を選ぶ。keg-onlyなら実行方法も案内 |
| HEAD | 通常版に開発branchを指定 | 安定版の代わりではなく開発版として使う |

固定版のFormulaを、同じ名前のまま別のソースへ付け替えない。
公開済みタグ・URL・checksumを保持し、再実行で内容が変わったら止める。
固定する対象がCLIのソースなのか、runtime・依存も含むのかを区別して説明する。

版付きFormula名と実行ファイル名は別にする。
Goの `std_go_args` はFormula名を出力名に使うため、固定版でも同じCLI名にしたい場合は
`output: bin/"<CLI名>"` を明示する。
`keg_only :versioned_formula` を使う固定版では、brew --prefixで得たbinのパスから実行できるよう案内する。

## Formulaで押さえる点

- ソースのURLとSHA-256、homepage、description、実際のlicenseを記載する。
- build依存とruntime依存を分ける。binとlibexecの役割も分ける。
- install時に利用者の既存環境へ依存を混ぜない。
- `test do` で導入したCLIを呼び出し、可能なら実際の機能を確認する。
- 通常版と固定版の両方を、cleanな環境でinstall・testする。

Go modules等をbuild時に取得する方式は、Homebrewのネットワーク制限に注意する。
Homebrew 7以降のfetchに対応した構成なら、fetchで依存を取得し、installではofflineでbuildする。
Goなら `go mod download` と `GOPROXY=off` を組み合わせ、go.mod・go.sumと必要なGo版を揃える。
別方式や古い環境を対象にするなら、vendoringや成果物の配布も含めて設計を確認する。

## release workflowで考えること

公開と検証を分け、[GitHub Actions](github-actions.md)の最小権限・lock方針を適用する。
まずは明示したversionを対象に、成果物とFormulaを確認してから公開する運用にする。

1. versionと、そのversionが指すソースcommitを確定する。
2. FormulaのURLを取得可能にして、配布物のchecksumを計算する。
3. 公開済みFormulaと照合し、通常版・固定版の更新候補を作る。
4. brew install・brew testを実施する。
5. 検証済みのFormulaを公開し、必要なRelease情報・告知を整える。

タグのarchiveを使うなら、brew installの前に対象commitのタグを公開する。
Release assetを使うなら、そのassetを取得できるReleaseも先に公開する。
配布物の公開とFormulaの公開を同じ段階にせず、Formulaの更新は検証成功後に行う。
配布物を先に公開できない運用では、検証用URLやinstaller cacheを使う方式を別途設計する。

既存固定版との照合は、空の生成ディレクトリだけではできない。
同じリポジトリでも別tapでも、公開済みFormulaを取得してから比較する。
生成物をartifactへ分ける場合は、その比較に成功してからstagingする。
通常版を古いversionへ戻す操作も、意図したものか確認する。

タグ・Formula・Releaseを一度に更新する処理は、途中まで成功することを前提にする。
各段階が既に完了している場合は同じ内容であることを確認し、未完了の段階から再開できるようにする。
同じversionに別のchecksumを付けて、再実行を成功扱いにしない。
公開処理はconcurrencyで直列化し、途中でキャンセルするかどうかも決める。

## PRマージごとの自動patch releaseを採用するなら

ipv4-runはmainへのマージごとにpatchを上げ、処理済みPRをstateへ記録する。
履歴順に未処理PRを回収し、同じタグが別commitを指す場合は拒否する設計になっている。
この運用を採るなら、次の判断もセットにする。

- docsだけのPRもリリースするか。major / minorはどう指定するか。
- 初期baselineと、既存リリース・未処理PRの境界をどう決めるか。
- botのdefault branchへの直接pushを許可するか、Formula更新をPRへ分けるか。
- state・タグ・Formula・Releaseのどこまで進んだかをどう保存・復旧するか。
- GITHUB_TOKENで作ったイベントが後続workflowを起動しない場合をどう扱うか。

`pull_request_target: closed` は未マージのcloseでも起動するため、マージ時だけの処理には
`if: github.event.pull_request.merged == true` を条件にする。
write権限でPR headを実行せず、マージ後のdefault branchを扱う。
処理済みstateを残すだけでなく、タグや公開物との整合性も確認する。
参照元の自動化をそのまま移す前に、自分のrelease方針に必要な部分を選ぶ。

## 利用者向けの案内

READMEには、tapの追加、通常版・固定版・HEADの導入、更新、削除をまとめる。
版付きFormulaを共存させる場合は、どのCLIが実行されるかも説明する。

```sh
# プロジェクト本体をtapとして使う場合の例
brew tap OWNER/REPO https://github.com/OWNER/REPO.git
brew install OWNER/REPO/my-cli
brew upgrade OWNER/REPO/my-cli

# 開発branchのHEAD版を導入する例
brew install --HEAD OWNER/REPO/my-cli

# 固定版はkeg-onlyの配置から実行する例
brew install OWNER/REPO/my-cli@0.1.0
"$(brew --prefix OWNER/REPO/my-cli@0.1.0)/bin/my-cli" --help

# 不要になった版を削除し、tapも使わなくなったら解除する例
brew uninstall OWNER/REPO/my-cli
brew uninstall OWNER/REPO/my-cli@0.1.0
brew untap OWNER/REPO
```

## 参考資料

確認日: 2026-10-12。参照元の運用と、一般化できる判断を分けて記載した。

- [ipv4-runのFormula](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/Formula/ipv4-run.rb)
- [ipv4-runのrelease処理](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/scripts/release.py)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew taps](https://docs.brew.sh/Taps)
- [GitHubソースarchiveの安定性](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#stability-of-source-code-archives)
- [GoReleaserのHomebrew設定](https://goreleaser.com/customization/publish/homebrew_casks/)
