# 定番（teiban）

新しいリポジトリで使う構成・設定・運用の定番集。
Markdown内のコード・設定例を起点に、選ぶ理由と適用条件を短く残す。

## 使い方

1. 用途に合う記事を選び、対象ファイルと前提を確認する。
2. 必要なコード・設定例を転記し、名前・パス・版を対象プロジェクトに合わせる。
3. 記載した確認コマンドを利用先で実行する。説明用の例を、実行検証済みの完成品として扱わない。

成果物はMarkdownと、それを参照するスキル。アプリの実装や、実行用の設定ファイル一式は置かない。

## テーマと使える例

| テーマ | 記事内の例 |
| --- | --- |
| [VoidZero＋GoのWebアプリ](docs/web-voidzero-go.md) | Preact、Valibot、Vite+設定、Goの検査 |
| [GitHub Actions](docs/github-actions.md) | 最小CI、SHA固定・lock、lint、入力の扱い |
| [HomebrewでCLIを配布](docs/homebrew-cli.md) | Formula、導入・固定・更新、配布前の検証 |
| [Chrome拡張](docs/chrome-extension.md) | manifest、lint、実Chromeのテスト、配布物 |
| [依存管理の共通テンプレート](docs/dependency-updates.md) | Dependabot、7日待機、pinact |

## 読み方・育て方

採用理由・変える条件・落とし穴は例の近くに残す。共通方針はリンクして重複を避ける。
版や仕様が変わったら、例・確認日・公式資料を一緒に更新する。

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
