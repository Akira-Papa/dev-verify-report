#!/usr/bin/env python3
"""
generate_pdf.py - Markdown報告書をPDF化するスクリプト
スクリーンショット画像を埋め込み、日本語フォント対応。

Usage:
    python generate_pdf.py --report report.md --images ./screenshots/ --output report.pdf --font auto
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Optional, List, Dict

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2が必要です: pip install fpdf2", file=sys.stderr)
    sys.exit(1)


# 絵文字→テキスト置換マップ
EMOJI_MAP = {
    "✅": "[OK]",
    "⚠️": "[WARN]",
    "❌": "[NG]",
    "⭕": "[O]",
    "🔴": "[!]",
    "📝": "[NOTE]",
    "📌": "[PIN]",
    "🚀": "[GO]",
    "💡": "[TIP]",
    "⚒️": "[WIP]",
    "🎯": "[TARGET]",
}

# 追加: よくある絵文字パターンを除去
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"
    "\U0000fe0f"             # variation selector
    "]+",
    flags=re.UNICODE,
)


def find_font(font_arg: str, images_dir: str = "") -> Optional[str]:
    """日本語フォントを検索"""
    if font_arg != "auto" and os.path.exists(font_arg):
        return font_arg

    candidates = []

    # プロジェクト内のNotoSansJPを探す
    if images_dir:
        project_root = Path(images_dir)
        for _ in range(5):
            noto = project_root / "public" / "fonts" / "NotoSansJP-Regular.ttf"
            if noto.exists():
                candidates.append(str(noto))
                break
            project_root = project_root.parent

    candidates.extend([
        # macOS
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/Library/Fonts/ヒラギノ角ゴ ProN W3.otf",
        "/System/Library/Fonts/Hiragino Sans GB W3.otf",
        # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
    ])

    for f in candidates:
        if os.path.exists(f):
            # 簡易バリデーション: ファイルサイズが小さすぎるorテキストファイルはスキップ
            try:
                size = os.path.getsize(f)
                if size < 10000:
                    continue
                with open(f, "rb") as fh:
                    header = fh.read(4)
                # TrueType/OpenType/TTC の先頭バイトチェック
                valid_headers = [b"\x00\x01\x00\x00", b"OTTO", b"ttcf", b"true", b"wOFF"]
                if not any(header.startswith(h) for h in valid_headers):
                    continue
            except Exception:
                continue
            return f
    return None


def replace_emoji(text: str) -> str:
    """絵文字をテキスト表記に置換"""
    for emoji, replacement in EMOJI_MAP.items():
        text = text.replace(emoji, replacement)
    # 残りの絵文字を除去
    text = EMOJI_PATTERN.sub("", text)
    return text


def parse_markdown(md_text: str) -> List[Dict]:
    """Markdownをパースしてセクションのリストに変換"""
    lines = md_text.split("\n")
    sections = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.append({"type": "blank"})
        elif stripped.startswith("# "):
            sections.append({"type": "h1", "text": stripped[2:]})
        elif stripped.startswith("## "):
            sections.append({"type": "h2", "text": stripped[3:]})
        elif stripped.startswith("### "):
            sections.append({"type": "h3", "text": stripped[4:]})
        elif stripped.startswith("!["):
            # 画像参照: ![alt](path)
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
            if m:
                sections.append({"type": "image", "alt": m.group(1), "path": m.group(2)})
            else:
                sections.append({"type": "text", "text": stripped})
        elif stripped.startswith("|") and "|" in stripped[1:]:
            sections.append({"type": "table_row", "text": stripped})
        elif stripped.startswith("- "):
            sections.append({"type": "bullet", "text": stripped[2:]})
        elif stripped.startswith("---"):
            sections.append({"type": "hr"})
        else:
            sections.append({"type": "text", "text": stripped})

    return sections


def collect_images(images_dir: str) -> List[str]:
    """ディレクトリ内の画像ファイルを収集（ソート済み）"""
    if not images_dir or not os.path.isdir(images_dir):
        return []
    exts = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    files = [
        f for f in sorted(os.listdir(images_dir))
        if Path(f).suffix.lower() in exts
    ]
    return files


class ReportPDF(FPDF):
    """報告書PDF"""

    def __init__(self, font_path: Optional[str] = None):
        super().__init__()
        self.font_path = font_path
        self._setup_font()

    def _setup_font(self):
        if self.font_path:
            self.add_font("JP", "", self.font_path)
            self._jp = True
        else:
            self._jp = False
            print("WARNING: 日本語フォントが見つかりません。ASCII のみ出力します。", file=sys.stderr)

    def _set_font(self, style: str = "", size: int = 10):
        if self._jp:
            # .ttc では Bold スタイルが使えないため常に Regular
            self.set_font("JP", "", size)
        else:
            self.set_font("Helvetica", style, size)

    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self._set_font("", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")
        self.set_text_color(0, 0, 0)

    def add_h1(self, text: str):
        self._set_font("B", 18)
        self.set_text_color(30, 30, 30)
        self.cell(0, 14, replace_emoji(text), new_x="LMARGIN", new_y="NEXT")
        # 下線
        self.set_draw_color(50, 50, 50)
        self.set_line_width(0.5)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(6)
        self.set_text_color(0, 0, 0)

    def add_h2(self, text: str):
        self.ln(3)
        self._set_font("B", 14)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, replace_emoji(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def add_h3(self, text: str):
        self.ln(2)
        self._set_font("B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, replace_emoji(text), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def add_text(self, text: str):
        self._set_font("", 10)
        self.multi_cell(0, 6, replace_emoji(text), new_x="LMARGIN", new_y="NEXT")

    def add_bullet(self, text: str):
        self._set_font("", 10)
        self.cell(6, 6, "・")
        self.multi_cell(0, 6, replace_emoji(text), new_x="LMARGIN", new_y="NEXT")

    def add_table_row(self, text: str, is_header: bool = False):
        """簡易テーブル行の描画"""
        cells = [c.strip() for c in text.strip("|").split("|")]
        # セパレータ行はスキップ
        if all(re.match(r"^[-:]+$", c) for c in cells):
            return

        self._set_font("B" if is_header else "", 9)
        col_w = (self.w - self.l_margin - self.r_margin) / max(len(cells), 1)
        for cell in cells:
            self.cell(col_w, 6, replace_emoji(cell)[:40], border=1)
        self.ln()

    def add_image_embed(self, img_path: str, alt: str = ""):
        """画像をPDFに埋め込み（ページ幅に合わせる）"""
        if not os.path.exists(img_path):
            self.add_text(f"[画像なし: {alt or img_path}]")
            return

        avail_w = self.w - self.l_margin - self.r_margin  # ~180mm
        # ページ残り高さチェック
        if self.get_y() > self.h - 80:
            self.add_page()

        try:
            self.image(img_path, x=self.l_margin, w=avail_w)
            self.ln(4)
        except Exception as e:
            self.add_text(f"[画像読込エラー: {e}]")

    def add_hr(self):
        self.ln(3)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        y = self.get_y()
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(3)


def generate_pdf(report_path: str, images_dir: str, output_path: str, font_arg: str):
    """メイン: report.mdを読み込みPDFを生成"""

    # フォント検索
    font_path = find_font(font_arg, images_dir)
    if font_path:
        print(f"フォント: {font_path}")
    else:
        print("WARNING: 日本語フォント未検出", file=sys.stderr)

    # Markdown読み込み
    with open(report_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    sections = parse_markdown(md_text)

    # PDF作成
    pdf = ReportPDF(font_path)
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    table_started = False
    table_row_idx = 0

    for sec in sections:
        t = sec["type"]

        if t != "table_row":
            table_started = False
            table_row_idx = 0

        if t == "h1":
            pdf.add_h1(sec["text"])
        elif t == "h2":
            pdf.add_h2(sec["text"])
        elif t == "h3":
            pdf.add_h3(sec["text"])
        elif t == "text":
            pdf.add_text(sec["text"])
        elif t == "bullet":
            pdf.add_bullet(sec["text"])
        elif t == "table_row":
            is_header = not table_started
            table_started = True
            table_row_idx += 1
            pdf.add_table_row(sec["text"], is_header=is_header)
        elif t == "image":
            # 画像パス解決
            img_path = sec["path"]
            if not os.path.isabs(img_path):
                # report.md からの相対パス
                img_path = os.path.join(os.path.dirname(report_path), img_path)
            if not os.path.exists(img_path) and images_dir:
                # images_dir内を探す
                basename = os.path.basename(sec["path"])
                alt_path = os.path.join(images_dir, basename)
                if os.path.exists(alt_path):
                    img_path = alt_path
            pdf.add_image_embed(img_path, sec.get("alt", ""))
        elif t == "hr":
            pdf.add_hr()
        elif t == "blank":
            pdf.ln(2)

    # images_dirに画像があり、mdに画像参照がない場合、末尾に全スクショを追加
    md_has_images = any(s["type"] == "image" for s in sections)
    if not md_has_images and images_dir:
        imgs = collect_images(images_dir)
        if imgs:
            pdf.add_page()
            pdf.add_h2("スクリーンショット一覧")
            for img_file in imgs:
                img_full = os.path.join(images_dir, img_file)
                pdf.add_text(img_file)
                pdf.add_image_embed(img_full, img_file)
                pdf.ln(2)

    pdf.output(output_path)
    print(f"PDF生成完了: {output_path}")
    print(f"  ページ数: {pdf.page_no()}")


def main():
    parser = argparse.ArgumentParser(description="Markdown報告書→PDF変換")
    parser.add_argument("--report", required=True, help="report.md のパス")
    parser.add_argument("--images", default="", help="スクショディレクトリ")
    parser.add_argument("--output", required=True, help="出力PDFパス")
    parser.add_argument("--font", default="auto", help="フォントパス or 'auto'")
    args = parser.parse_args()

    if not os.path.exists(args.report):
        print(f"ERROR: {args.report} が見つかりません", file=sys.stderr)
        sys.exit(1)

    generate_pdf(args.report, args.images, args.output, args.font)


if __name__ == "__main__":
    main()
