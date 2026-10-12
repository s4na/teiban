# 定番（teiban）

新しいリポジトリを作るときに使う、自分の定番設定集。
毎回調べ直しているツールの選び方、設定、導入手順、確認方法をここに残す。

## 作りたいもの

「この用途で始めるなら、何を選び、どう揃えるか」を、理由と一緒にコピーできる形にする。
JavaScript / TypeScript、CSS、Goの開発環境から、lint・整形・テスト、GitHub Actions、配布まで扱う。
アプリ固有の機能よりも、リポジトリを始めるときの判断と設定を中心にする。

- **構成例（presets）**: Webアプリ、CLI、Chrome拡張など、用途ごとの組み合わせ。
- **部品（parts）**: 構成例を増やす中で繰り返し使うと分かった設定。
- **理由と手順**: 採用理由、適用条件、コピー先、確認コマンド、更新時の注意点。

最初は用途ごとの構成例を完成させ、共通部分が見えてから部品に分ける。
「どのプロジェクトにも全部入れる」より、必要な構成を選んで持ち込めることを優先する。

## 追加していく構成

1. [VoidZeroのツール群＋Goで作るWebアプリ](presets/web-voidzero-go/README.md)。
2. [GitHub ActionsのCI、依存Actionのlock、更新と検証](parts/github-actions/README.md)。
3. [brew installで導入できるCLIの配布](presets/homebrew-cli/README.md)。
4. 小さなChrome拡張の開発・テスト・配布。

## 使い方

各構成例のREADMEで用途と前提を確認し、指定されたファイルを新しいリポジトリへコピーする。
プロジェクト名、module名、対象URLなどを置き換え、記載した確認コマンドを実行する。
バージョンとlockfileは構成例の検証時点を記録するためのもの。更新するときは両方を揃えて再確認する。

設定の追加方法は [追加・更新の方針](docs/adding-presets.md)、記述のひな形は
[構成例のREADMEテンプレート](templates/preset-readme.md) を参照する。
