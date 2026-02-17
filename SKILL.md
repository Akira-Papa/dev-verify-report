---
name: dev-verify-report
description: |
  開発修正・機能実装後の動作確認→スクショ撮影→テストチェックリスト→修正報告書（md+PDF）作成の一連のワークフロー。
  Use when: 「動作確認して」「スクショ撮って」「テスト結果まとめて」「修正報告書作って」「確認してPDFで送って」等の依頼。
  開発作業後のブラウザ確認、スクリーンショット収集、テスト結果の文書化、PDF報告書生成に使用。
  Don't use when: コードの実装のみ（動作確認・報告書が不要な場合）。デザインレビュー（実装の動作確認ではない場合）。
---

# dev-verify-report スキル

修正・実装後の品質確認ワークフロー。ブラウザで実際に動作確認し、エビデンス（スクショ）付きの報告書を作成してPDF化する。

## ワークフロー

### Step 1: 準備

- 対象プロジェクトのディレクトリ確認
- 出力フォルダ作成: `docs/tasks/YYYY-MM-DD/verification-test/`
- 対象ブランチ・デプロイ状況確認（`git log --oneline -5`, 本番URL等）

### Step 2: ブラウザ動作確認 & スクショ撮影

```
browser open   → profile=openclaw, targetUrl=対象URL
browser screenshot → 保存先: 出力フォルダ/01_xxx.jpg
```

**撮影ルール:**
- 連番ファイル名: `01_toppage.jpg`, `02_feature_name.jpg` ...
- ダイアログ/モーダル: `snapshot` → 内容確認 → `click` → `screenshot`
- スクロール必要時: `evaluate` で `document.documentElement.scrollTop = N` → screenshot
- レスポンシブ確認が必要なら viewport 変更後に撮影

**ブラウザ操作例:**
```javascript
// ページを開く
browser({ action: "open", profile: "openclaw", targetUrl: "https://example.com" })

// スクショ撮影
browser({ action: "screenshot", profile: "openclaw", fullPage: true,
          path: "/path/to/01_toppage.jpg" })

// スナップショットで要素確認→クリック
browser({ action: "snapshot", profile: "openclaw" })
browser({ action: "act", profile: "openclaw",
          request: { kind: "click", ref: "ボタンのref" } })

// スクロール
browser({ action: "act", profile: "openclaw",
          request: { kind: "evaluate",
                     fn: "() => { document.documentElement.scrollTop = 500; }" } })
```

### Step 3: テストチェックリスト作成

`test-checklist.md` を出力フォルダに作成:

```markdown
# テストチェックリスト

## テスト情報
- テスト日時: YYYY年MM月DD日 HH:MM
- テスト対象: [URL]
- テスト対象ブランチ: [branch]
- テスト実施者: テスト特化AIエージェント

## チェック項目

| # | 項目 | 期待結果 | 実際の結果 | 判定 | スクショ |
|---|------|---------|-----------|------|---------|
| 1 | トップページ表示 | 正常表示 | 正常表示確認 | ✅ | 01_toppage.jpg |
| 2 | xxx機能 | xxxが動作 | 動作確認 | ✅ | 02_xxx.jpg |

## 総合判定
- ✅ 全項目合格 / ⚠️ 一部注意あり / ❌ 不合格あり
```

### Step 4: 修正報告書（md）作成

`report.md` を出力フォルダに作成:

```markdown
# 修正確認報告書

## 基本情報
- 報告日: YYYY年MM月DD日
- 報告者: テスト特化AIエージェント
- 対象プロジェクト: [プロジェクト名]
- 対象URL: [URL]
- 対象ブランチ: [branch]

## 実施概要
[何をしたかの概要]

## 修正項目の確認結果

### 1. [修正項目名]
- **修正内容**: [何を変更したか]
- **確認結果**: ✅ 正常動作
- **スクリーンショット**: 01_xxx.jpg

![01_xxx](./01_xxx.jpg)

### 2. [修正項目名]
...

## 未対応・残課題
- なし / [課題があれば記載]

## 推奨アクション
- [次のステップ]

## スクリーンショット一覧
| # | ファイル名 | 説明 |
|---|-----------|------|
| 1 | 01_xxx.jpg | xxx |
```

### Step 5: PDF化

スキルディレクトリの `scripts/generate_pdf.py` を使用:

```bash
# fpdf2が必要（初回のみ）
pip install fpdf2

# PDF生成
python /path/to/skills/dev-verify-report/scripts/generate_pdf.py \
  --report /path/to/report.md \
  --images /path/to/verification-test/ \
  --output /path/to/report.pdf \
  --font auto
```

**引数:**
- `--report`: report.md のパス
- `--images`: スクショが入っているディレクトリ
- `--output`: 出力PDFパス
- `--font`: `auto`（自動検索）またはフォントファイルのパス

**フォント自動検索順:**
1. プロジェクト内の `NotoSansJP-Regular.ttf`
2. macOS `/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc`
3. macOS `/Library/Fonts/ヒラギノ角ゴ ProN W3.otf`

**絵文字の置換（フォント非対応時）:**
- ✅ → [OK]
- ⚠️ → [WARN]
- ❌ → [NG]

### Step 6: Discord送信

```javascript
// ワークスペースにコピー（パス制限対応）
exec("cp /path/to/report.pdf /workspace/report.pdf")

// Discord送信
message({ action: "send", target: "チャンネル",
          message: "修正確認報告書です",
          filePath: "/workspace/report.pdf" })
```

## 注意事項

- **ログイン必要時**: 担当者に依頼（自動ログイン不可）
- **未デプロイ項目**: 「PR待ち」「マージ後確認予定」として記録
- **スクショ形式**: jpg（browser screenshotデフォルト）
- **PDF設定**: A4サイズ、マージン15mm
- **画像埋め込み**: ページ幅（180mm）に収まるようリサイズ
- **ファイル配置**: すべて `docs/tasks/YYYY-MM-DD/verification-test/` に集約
