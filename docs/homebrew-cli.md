# 自作CLIをHomebrewで配布するときの定番

## 用途と前提

自作CLIを `brew install` で導入・更新し、特定の版も選べるようにする。
開発環境用のBrewfileとは分けて、配布用のtap・Formula・releaseを扱う。

以下は自分のtapでGo CLIをソースbuildする例。
`OWNER`、`REPO`、`TAP`、`my-cli`、`0.1.0`、build対象のパスは実際の構成へ置き換える。
checksumとlicenseも配布物から確認する。

## 配布方式を選ぶ

- **ソースbuild**: 言語・build依存、取得元、checksumをFormulaに定義する。以下はこの方式。
- **build済みバイナリ**: OS・CPUごとの成果物、checksum、署名・notarizationを管理する。
- **Python等**: runtime依存と専用環境を定義する。内部ファイルは `libexec`、launcherは `bin` に置き、利用者の既存環境へ依存を混ぜない。

GoReleaserでバイナリを配る場合は `homebrew_casks` を確認する。旧 `brews` は非推奨。
Formula例と混ぜず、対象OS・CPUと固定版の要件に合う設定を選び、`goreleaser check` で確認する。

## 通常版のFormula

`OWNER/homebrew-TAP` に置く例。Homebrew 7以降のfetch方式を使う。
archiveのルートに `go.mod`・`go.sum`、実行対象に `cmd/my-cli` があり、
CLIが `--help` を受け付ける前提。

```ruby
# Formula/my-cli.rb
class MyCli < Formula
  desc "Example command-line tool"
  homepage "https://github.com/OWNER/REPO"
  url "https://github.com/OWNER/REPO/releases/download/v0.1.0/my-cli-0.1.0.tar.gz"
  sha256 "REPLACE_WITH_64_HEX_SHA256"
  license "MIT" # 例。実際のlicenseに置き換える
  head "https://github.com/OWNER/REPO.git", branch: "main"

  depends_on "go" => :build

  def fetch
    system "go", "mod", "download"
  end

  def install
    ENV["GOPROXY"] = "off"
    system "go", "build", *std_go_args(output: bin/"my-cli"), "./cmd/my-cli"
  end

  test do
    system bin/"my-cli", "--help"
  end
end
```

`fetch` で依存を取得し、`install` で追加取得せずbuildする。
必要なGo版を `go.mod` とbuild依存で揃える。
古いHomebrewも対象なら、vendoringやバイナリ配布を検討する。

`--help` は最小確認。実際のFormulaでは入力の処理結果などを検証するテストに置き換える。
認証や対話操作に頼らず、新しい一時ディレクトリで動くものにする。

## 固定版とHEAD

| 種類 | Formula | 管理 |
| --- | --- | --- |
| 通常版 | `my-cli.rb` | 最新安定版のURL・checksumへ更新 |
| 固定版 | `my-cli@0.1.0.rb` | 同じ版のソース・URL・checksumを保持 |
| HEAD | 通常版の `head` | 開発branchの先端。安定版とは別用途 |

通常版が `0.1.0` を指す時点の内容を `Formula/my-cli@0.1.0.rb` へコピーし、次を変える。

```diff
-class MyCli < Formula
+class MyCliAT010 < Formula
-  head "https://github.com/OWNER/REPO.git", branch: "main"
+  keg_only :versioned_formula
```

`output: bin/"my-cli"` は残す。`std_go_args` の既定の出力名はFormula名なので、
省略すると固定版の実行ファイル名も変わる。keg-only版は末尾の例のように配置先を指定して実行する。

固定版を同じ名前のまま別ソースへ付け替えない。
この例が固定するのはCLIのソースとmodule定義であり、compilerやHomebrew側の依存まで同じ版に保つものではない。
古い版には修正が自動で入らないため、更新方針も案内する。
patch版まで残すのは自分のtapの方針で、homebrew/coreの採用条件とは分ける。

## checksumと公開前の検証

版付きのRelease assetを公開し、公開後に同じassetを差し替えない。
ソースbuildでも自分で作ったarchiveを配布できる。
GitHubの自動生成タグarchiveは、同じcommitでも圧縮方法の変更でbytesが変わり得る。
展開後の内容が同じこととSHA-256が同じことは別なので、長期保持する固定版には自分で公開したarchiveを使う。

公開済みassetを取得して確認する例:

```sh
set -eu
archive="$(mktemp)"
curl --fail --location --retry 3 --output "$archive" \
  "https://github.com/OWNER/REPO/releases/download/v0.1.0/my-cli-0.1.0.tar.gz"
shasum -a 256 "$archive"
```

公開前の成果物と一致することを確認し、そのSHA-256をFormulaへ記載する。
既存固定版とchecksumが違う場合は止める。値を書き換えて再実行を成功扱いにしない。

候補のFormulaを置いたディレクトリで、cleanな検証環境から実行する例。
`OWNER/check` は新しいローカルtapで、配布用tapへはpushしない。

```sh
set -eu
brew tap-new OWNER/check
tap_dir="$(brew --repository OWNER/check)"
cp Formula/my-cli.rb Formula/my-cli@0.1.0.rb "$tap_dir/Formula/"
mkdir -p "$tap_dir/Aliases"
ln -s ../Formula/my-cli.rb "$tap_dir/Aliases/my-cli@0.1"

for formula in my-cli my-cli@0.1.0; do
  brew audit --strict "OWNER/check/$formula"
  brew install --build-from-source "OWNER/check/$formula"
  brew test "OWNER/check/$formula"
done
"$(brew --prefix OWNER/check/my-cli@0.1.0)/bin/my-cli" --help
```

Homebrew 7のauditに合わせ、配布tapにも通常版へのmajor/minor aliasを置く。
例の `my-cli@0.1` は通常版を指す可変aliasで、ソースを固定する `my-cli@0.1.0` とは別。通常版の版に合わせてalias名も見直す。
[auditの条件](https://github.com/Homebrew/brew/blob/7.0.0/Library/Homebrew/formula_auditor.rb#L109-L156)を参照。

対応するOS・CPUで通常版と固定版を確認し、既存のmodule cacheへの依存も調べる。
HEADを提供するなら、別のcleanな環境で `brew install --HEAD` と `brew test` を行う。
これらは採用先で実行する手順であり、この記事の例を実環境で検証済みとは扱わない。

## 公開順序と再実行

最初はversionを明示して公開する運用にする。
最小権限・並行実行は [GitHub Actions](github-actions.md)、
Action固定・更新は [依存管理](dependency-updates.md)に合わせる。

| 順序 | 確認すること |
| --- | --- |
| 1. versionとcommitを確定 | 既存の同名タグが別commitを指していたら停止 |
| 2. タグ・配布物を公開 | FormulaのURLから取得でき、checksumが成果物と一致 |
| 3. Formula候補を作成 | 公開済みtapの固定版と照合。通常版の意図しない巻き戻しを拒否 |
| 4. 候補を検証 | 通常版・固定版のinstall・testが成功 |
| 5. Formulaを公開 | 検証した内容をtapへ反映し、Release情報・告知を整備 |

タグarchiveなら検証前にタグ、Release assetなら取得可能なReleaseが必要。
配布物を先に公開できない運用では、検証用URLやinstaller cacheを使う方式を別途設計する。

タグ・Release・Formulaは一括で確定しない。途中成功からの再実行は、既存内容との一致を確認して未完了の段階から再開する。
公開済みasset・固定版が候補と違ったら上書きせず停止する。
比較対象を空の生成ディレクトリで代用せず、artifactへのstagingも比較成功後に行う。
公開処理はconcurrencyで直列化し、途中キャンセルの扱いを決める。

### PRマージごとの自動patch releaseを採る場合

参照元のipv4-runは、処理済みPRをstateへ記録し、未処理PRを履歴順に回収する。
採用するなら、docs-only PRの扱い、major / minorの指定、初期baseline、
botの直接pushかFormula更新PRかを決める。

`pull_request_target: closed` は未マージのcloseでも起動する。
公開jobに `if: github.event.pull_request.merged == true` を付け、write権限でPR headを実行しない。
マージ後のdefault branchを使い、stateとタグ・公開物を照合して重複や途中成功を扱う。
`GITHUB_TOKEN` によるタグpushが後続workflowを起動しない場合も、公開処理が完了する構成にする。

## 利用者向けREADMEの例

`OWNER/homebrew-TAP` から配る場合。通常版とHEADは同じFormulaなので、導入方法はどちらかを選ぶ。

```sh
# 通常版
brew tap OWNER/TAP
brew install OWNER/TAP/my-cli
brew upgrade OWNER/TAP/my-cli

# 固定版。実行ファイルの配置先を明示する
brew install OWNER/TAP/my-cli@0.1.0
"$(brew --prefix OWNER/TAP/my-cli@0.1.0)/bin/my-cli" --help

# 開発版を使う場合
brew install --HEAD OWNER/TAP/my-cli

# 不要になった版を削除し、tapも使わなくなったら解除する
brew uninstall OWNER/TAP/my-cli
brew uninstall OWNER/TAP/my-cli@0.1.0
brew untap OWNER/TAP
```

CLI本体のリポジトリをtapにする場合は、
`brew tap OWNER/REPO https://github.com/OWNER/REPO.git` とURLを明示し、
以降のFormula名も `OWNER/REPO/my-cli` に合わせる。

## 参考資料

確認日: 2026-10-13。参照元はPython CLIで、版管理と再実行の判断を参考にした。

- [ipv4-runのrelease workflow](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/.github/workflows/release.yml)・[release処理](https://github.com/s4na/ipv4-run/blob/fb41539767b9da8d30a884f6efde8a75646df4dd/scripts/release.py)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)・[std_go_args](https://docs.brew.sh/rubydoc/Formula.html#std_go_args-instance_method)・[Homebrew 7.0.0](https://brew.sh/2026/09/13/homebrew-7.0.0/)
- [tapの作成・管理](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)・[tapの指定方法](https://docs.brew.sh/Taps)・[versioned Formula](https://docs.brew.sh/Versions)
- [Go modulesの環境変数](https://go.dev/ref/mod#environment-variables)
- [GitHubソースarchiveの安定性](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives#stability-of-source-code-archives)
- [GoReleaserのHomebrew設定](https://goreleaser.com/customization/publish/homebrew_casks/)・[非推奨設定](https://goreleaser.com/resources/deprecations/#brews)
- [GitHub Actionsのイベント](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)・[workflowからの起動制限](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow#triggering-a-workflow-from-a-workflow)
