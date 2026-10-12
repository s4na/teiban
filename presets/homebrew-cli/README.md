# CLIをbrew installで配布する定番

## 用途と前提

自分のCLIをHomebrew tap経由で配布したいときの設定。
環境用のBrewfileを作る話ではなく、利用者が `brew install` でCLIを導入・更新・固定できるようにする。

参照は [ipv4-runのrelease workflow](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/.github/workflows/release.yml)。
2026-10-12にmainの `fb41539767b9da8d30a884f6efde8a75646df4dd` と、そのFormula・release.py・テストを確認した。
参照元はPythonのCLI。この構成例のFormulaはGoのソースbuildを想定し、言語固有のinstall処理は利用先で変える。

## 定番にする部分

| 項目 | 方針 |
| --- | --- |
| 配布物 | `vX.Y.Z` タグのソースarchive。URLとSHA-256をFormulaへ記録 |
| 通常版 | `Formula/<name>.rb` を最新の安定版へ更新 |
| 固定版 | `Formula/<name>@X.Y.Z.rb` を保持。`keg_only :versioned_formula` で共存 |
| HEAD版 | 通常版だけに `head` を用意。安定版とは区別する |
| インストール | 実行ファイルはbin、内部スクリプト・資源は必要に応じlibexec |
| 確認 | ソースからの `brew install` と `brew test` を通常版・固定版で実行 |
| 自動化 | リリース処理を直列化し、再実行で同じ版を別の内容にしない |
| 権限 | 検証はreadのみ。タグ・Formula・Releaseを公開するjobだけwrite |

固定版が固定するのはCLIのソース。GoやPython等の依存まで完全固定するものではない。
`brew upgrade` で上がる通常版と、明示的に選ぶ固定版をREADMEでも分ける。

## 配置と導入

```text
Formula/teiban-cli.rb.in                 Go CLI用のFormulaテンプレート
scripts/render_formula.py               URL・checksum・通常版・固定版を生成
.github/workflows/prepare-homebrew.yml   既存タグから生成・brew検証するworkflow
```

これは利用先CLIへ組み込むテンプレート。teiban自身をbrew配布するものではない。
実行できるCLIの `go.mod` と `cmd/<name>`、`--help` の仕様を利用先で用意する。
そのうえでこのディレクトリのREADME以外を利用先のルートへコピーする。
Formulaの `fetch` に対応するHomebrew 7以降を前提にする。
Go modulesはネットワークを使える `fetch` で先に取得し、`install` では
`GOPROXY=off` でbuildする。`go.mod`・`go.sum` と必要なGo版もソースへ含める。

- `desc`、main以外のデフォルトブランチ、`install` と `test do` をCLIに合わせる。
- Go以外ならGoのbuild依存を変える。Pythonならruntime依存とlibexecのlauncherを設計する。
- `--help` の期待値 `Usage` もCLIの実際の出力へ合わせる。
- workflowのAction依存は [GHA部品](../../parts/github-actions/README.md) に従ってlockを生成する。

```sh
# 利用先で v0.1.0 タグを公開した後。archiveを取得してchecksumを計算する
python3 scripts/render_formula.py \
  --repository OWNER/REPO --name my-cli --version 0.1.0

ruby -c Formula/my-cli.rb
ruby -c Formula/my-cli@0.1.0.rb
```

generatorは既存の固定版と異なる内容で上書きしようとすると停止する。
生成した通常版を公開する前に、その版が最新の安定版かも確認する。
checksumは取得したarchiveと一致することを示す。リリース内容自体の信頼性はタグとソースのレビューで確認する。

`prepare-homebrew.yml` はデフォルトブランチから手動実行し、公開済みversionとCLI名を入力する。
checkoutした `Formula/` の既存固定版と照合しながら生成してから、対象の2ファイルを
artifact用ディレクトリへコピーする。brewの実インストール・テストを行い、artifactへ保存する。
公開済みFormulaはこのリポジトリのデフォルトブランチの `Formula/` に保持する。
別tapで管理する場合はその公開済み固定版も取得し、生成先へ配置してから実行する。
生成物を確認し、利用先のFormula更新PRへ含める。タグ作成・mainへのpush・Release公開は行わない。

## 利用者向けREADMEの定番

通常の `homebrew-<tap>` 名にするか、プロジェクト自身を明示URLでtapにできる。
参照元のように通常の命名ではないリポジトリをtapにする場合は、URLも案内する。

```sh
brew tap OWNER/REPO https://github.com/OWNER/REPO.git
brew install OWNER/REPO/my-cli

# tapに用意された固定版を選ぶ
brew install OWNER/REPO/my-cli@0.1.0
"$(brew --prefix OWNER/REPO/my-cli@0.1.0)/bin/my-cli" --help

# 開発版
brew install --HEAD OWNER/REPO/my-cli

# 更新・削除
brew update
brew upgrade OWNER/REPO/my-cli
brew uninstall OWNER/REPO/my-cli
brew uninstall OWNER/REPO/my-cli@0.1.0
brew untap OWNER/REPO
```

## PRマージごとの自動パッチリリースを採用するなら

ipv4-runはmainへのマージごとにpatchを上げ、処理済みPRを `.release-state.json` に記録する。
`pull_request_target: closed` で起動しても、write tokenでPR headをcheckoutせず、マージ後のmainだけを扱う。
同時実行を直列化し、未処理PRを履歴順に回収し、同じタグが別のcommitを指す場合は拒否する。

この運用にする場合は、次の判断と検証もセットで必要。

- docsだけのPRもリリース対象にするか、major/minorをどう上げるか。
- stateの初期baseline、既存リリースと未処理PRの境界。
- botのmainへの直接pushを許可するか、Formula更新をPRへ分けるか。
- GitHub tokenで作ったイベントが後続workflowを自動起動しないことへの対応。
- 失敗段階（タグ済み、Formula未公開、Release未公開）ごとの再実行。
- 既存タグの付け替え、固定Formulaの変更、force pushを避けること。

利用先固有のstate更新・README更新・公開処理は参照元のrelease.pyを読む。
全CLIで同じscriptをそのまま使う前提にはせず、ここでは生成・検証までを共通の初期値にする。

## Goのbuild済みバイナリを配る場合

この例はソースbuildのFormula。GoReleaserで事前buildしたバイナリを配る場合は別構成になる。
現在のGoReleaserは旧 `brews` より `homebrew_casks` を案内しているため、古いFormula設定を流用しない。
macOSの署名・notarizationやLinuxへの対応も、選んだ配布方式で確認する。

## 検証記録と参考資料

2026-10-12: generatorの入力検証、通常版・固定版の生成、再実行、固定版の変更拒否とRuby構文を確認。
`python3 -m unittest discover -s tests -v` が成功（3テスト）。
生成Formulaのfetch/installメソッドを一時的なGo CLIで実行し、空のmodule cacheから
外部moduleを取得してGOPROXY=offでbuildできることも確認した（Homebrew sandbox外での確認）。
workflowのactionlint・zizmorも成功。
利用先CLIの公開タグ・brew実インストール・Release公開は未実施。workflowのbrew検証は利用先で行う。

- [ipv4-runのFormula](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/Formula/ipv4-run.rb)
- [ipv4-runのrelease.py](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/scripts/release.py)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew taps](https://docs.brew.sh/Taps)
- [GoReleaserのHomebrew設定](https://goreleaser.com/customization/publish/homebrew_casks/)
