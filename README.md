# dev-verify-report

Markdown形式の報告書を、スクリーンショット画像と共にPDFに変換するツールです。
開発修正や機能実装後の動作確認レポート作成を効率化するために設計されています。

## 特徴

- **Markdown対応**: 見出し、リスト、テーブル、画像埋め込みなどのMarkdown記法をサポート。
- **画像自動埋め込み**: スクリーンショットディレクトリを指定することで、レポート内の画像参照を解決。
- **日本語フォント対応**: OS標準の日本語フォント（ヒラギノ、NotoSansなど）を自動検出して使用。
- **絵文字対応**: PDFで文字化けしやすい絵文字をテキスト（`[OK]`, `[NG]`など）に自動置換。

## 必要要件

- Python 3.x
- [fpdf2](https://pypi.org/project/fpdf2/)

## インストール

必要なライブラリをインストールしてください。

```bash
pip install fpdf2
```

## 使い方

`scripts/generate_pdf.py` を使用して変換を行います。

```bash
python scripts/generate_pdf.py \
  --report /path/to/report.md \
  --images /path/to/screenshots/ \
  --output /path/to/report.pdf \
  --font auto
```

### 引数オプション

| 引数 | 必須 | 説明 | デフォルト |
|---|---|---|---|
| `--report` | 必須 | 変換元のMarkdownファイルのパス | - |
| `--output` | 必須 | 出力するPDFファイルのパス | - |
| `--images` | 任意 | スクリーンショット画像が格納されているディレクトリのパス | `""` |
| `--font` | 任意 | フォントファイルのパス。`auto`で自動検索。 | `auto` |

## ワークフロー

このツールは、動作確認ワークフローの一部として使用することを想定しています。
詳細は [SKILL.md](./SKILL.md) を参照してください。

1. ブラウザで動作確認 & スクショ撮影
2. Markdownでレポート作成 (`report.md`)
3. このツールでPDF化
4. 報告
