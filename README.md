# 定番（teiban）

新しいリポジトリを作るときに迷うことを、Markdownで残していくノウハウ集。
「この用途なら何を選び、どう設定し、どう運用するか」を自分の定番としてまとめる。

## 残したいもの

JavaScript / TypeScript、CSS、Go、lint・整形・テスト、GitHub Actions、配布などの
選び方と設定の考え方。特定のアプリに依存しない形で、次のプロジェクトでも参照できるようにする。

- まず採用する構成と、その理由。
- 用途によって変える項目と、判断の目安。
- 導入する順序、設定で押さえる点、確認すること。
- 運用・更新で詰まりやすいところ。
- 根拠となる公式資料と、参考にしたリポジトリ。

説明に必要な短いコマンド・設定の例は本文に載せる。
このリポジトリの成果物はMarkdownの知識と、それを参照するスキル。
アプリの実装や実行用テンプレートは置かない。

## 最初にまとめるテーマ

1. [VoidZeroのツール群＋GoでWebアプリを作るときの定番](docs/web-voidzero-go.md)。
2. [GitHub ActionsのCI、Actionのlock、更新・検証の定番](docs/github-actions.md)。
3. [自作CLIをHomebrewで導入・更新・固定できるようにする定番](docs/homebrew-cli.md)。
4. [小さなChrome拡張を作るときの開発・テスト・配布の定番](docs/chrome-extension.md)。
5. [Dependabot・7日待機・pinactの依存管理ポリシーテンプレート](docs/dependency-updates.md)。

## 読み方・育て方

記事の「用途」と「まず採用するもの」を起点に、自分のプロジェクトに必要な判断を拾う。
バージョン番号そのものより、固定する場所・更新する方法・確認する範囲を残す。
流行やツールの仕様が変わったら、確認日と根拠を添えて更新する。

記事の書き方は [ノウハウのまとめ方](docs/writing-notes.md) を参照。

## Codexのスキルとして使う

[SKILL.md](SKILL.md)を入口に、依頼に関係する記事を読んで定番を適用する。
記事が選び方・理由・注意点を担当し、スキルが対象の確認・記事の選択・成果物の作成を担当する。
想定モデルはOpenAIのGPT-6 Sol（`gpt-6-sol`）。目的・参照先・成果物・確認を短い手順で明示する。
モデルはCodex側で選び、スキルからは変更しない。

このリポジトリ全体が一つのスキルフォルダなので、`SKILL.md`だけをコピーせず`docs/`も一緒に使う。
PRがmainへマージされた後、ghqのcheckoutを更新し、ユーザー用スキルへリンクする例:

```sh
mkdir -p "$HOME/.agents/skills"
# 同名のファイル・ディレクトリ・symlinkがある場合は作成せず、その設定を確認する
test ! -e "$HOME/.agents/skills/teiban" && \
  test ! -L "$HOME/.agents/skills/teiban" && \
  ln -s "$(ghq root)/github.com/s4na/teiban" "$HOME/.agents/skills/teiban"
codex --model gpt-6-sol
```

リンク先の記事の更新もそのまま反映される。新しいチャットで`$teiban`を指定するか、
descriptionに合う依頼で自動選択させる。用途を明記した呼び出し例:

- `$teiban VoidZero＋GoでWebアプリを作る構成と、選ぶ理由をまとめて`
- `$teiban このリポジトリのCIを定番に寄せて。既存の言語・ツールは維持して`
- `$teiban このGo CLIをbrewで配る方法をMarkdownにまとめて`
- `$teiban このChrome拡張の権限とSPAへの対応をレビューして`

スキルの呼び出し自体は、実装・移行・公開の依頼を追加しない。
構成相談なら提案、文書化ならMarkdown、設定変更の依頼なら変更と確認を成果物にする。

確認日: 2026-10-13。形式・読み込み先・symlinkの対応は[OpenAIのスキル公式資料](https://learn.chatgpt.com/docs/build-skills)、
モデル名は[GPT-6 Solの案内](https://learn.chatgpt.com/docs/changelog#codex-2026-09-22-gpt-6-sol-luna)を参照。
