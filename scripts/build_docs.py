#!/usr/bin/env python3
"""Build readable bilingual PDFs from Markdown. Does not access the server."""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]

try:
    import reportlab
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:  # pragma: no cover - optional PDF dependency
    reportlab = None
    colors = None
    ParagraphStyle = None
    pdfmetrics = None
    TTFont = None
    PageBreak = Paragraph = Preformatted = SimpleDocTemplate = Spacer = (
        Table
    ) = TableStyle = None


def main():
    """Build bilingual PDF exports for the project's documentation pages."""
    if reportlab is None:
        raise RuntimeError(
            "Optional PDF tool missing. See docs/en/printing.md or docs/fr/printing.md."
        )
    fontdir = Path(reportlab.__file__).resolve().parent / "fonts"
    pdfmetrics.registerFont(TTFont("Family", str(fontdir / "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("FamilyBold", str(fontdir / "VeraBd.ttf")))
    styles = {
        "body": ParagraphStyle(
            "body", fontName="Family", fontSize=10, leading=14, spaceAfter=8
        ),
        "title": ParagraphStyle(
            "title",
            fontName="FamilyBold",
            fontSize=20,
            leading=25,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "heading",
            fontName="FamilyBold",
            fontSize=12,
            leading=16,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "code": ParagraphStyle(
            "code",
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            backColor=colors.HexColor("#F1F5F2"),
            borderPadding=6,
            spaceBefore=3,
            spaceAfter=10,
        ),
        "cell": ParagraphStyle(
            "cell", fontName="Family", fontSize=9, leading=12
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Family",
            fontSize=10,
            leading=14,
            leftIndent=10,
            spaceAfter=6,
        ),
    }

    def plain(value):
        value = re.sub(
            r"\[([^]]+)\]\(([^)]+)\)",
            lambda m: (
                m.group(1)
                + (" (" + m.group(2) + ")" if "://" in m.group(2) else "")
            ),
            value,
        )
        return value.replace("`", "").replace("**", "").replace("→", ">")

    def para(value, kind="body"):
        return Paragraph(escape(plain(value)), styles[kind])

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#53615B"))
        canvas.drawString(38, 22, "Minecraft Bedrock Family")
        canvas.drawRightString(557, 22, str(doc.page))

    def is_special(line):
        return line.startswith(("#", "|", "```", "<!--")) or bool(
            re.match(r"^\s*(?:[-*]|\d+\.)\s+", line)
        )

    for language in ("en", "fr"):
        for name in ("installation", "guide", "cheat-sheet"):
            source = ROOT / "docs" / language / (name + ".md")
            lines = source.read_text(encoding="utf-8").splitlines()
            story = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if not line.strip():
                    i += 1
                elif line.strip() == "<!-- pagebreak -->":
                    story.append(PageBreak())
                    i += 1
                elif line.startswith("<!--"):
                    i += 1
                elif line.startswith("```"):
                    block = []
                    i += 1
                    while i < len(lines) and not lines[i].startswith("```"):
                        block.append(lines[i])
                        i += 1
                    story.append(Preformatted("\n".join(block), styles["code"]))
                    i += 1
                elif line.startswith("#"):
                    kind = "title" if line.startswith("# ") else "heading"
                    story.append(para(line.lstrip("# ").strip(), kind))
                    i += 1
                elif line.lstrip().startswith("|"):
                    rows = []
                    while i < len(lines) and lines[i].lstrip().startswith("|"):
                        row = [
                            x.strip()
                            for x in lines[i].strip().strip("|").split("|")
                        ]
                        if not all(re.fullmatch(r"[:\- ]+", x) for x in row):
                            rows.append([para(x, "cell") for x in row])
                        i += 1
                    columns = max(len(row) for row in rows)
                    for row in rows:
                        row.extend([para("", "cell")] * (columns - len(row)))
                    table = Table(
                        rows,
                        colWidths=[519 / columns] * columns,
                        repeatRows=1,
                        hAlign="LEFT",
                    )
                    table.setStyle(
                        TableStyle(
                            [
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                (
                                    "ROWBACKGROUNDS",
                                    (0, 0),
                                    (-1, -1),
                                    [colors.HexColor("#EFF4F0"), colors.white],
                                ),
                                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                ("TOPPADDING", (0, 0), (-1, -1), 6),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ]
                        )
                    )
                    story.extend([table, Spacer(1, 8)])
                elif re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
                    story.append(para(line, "bullet"))
                    i += 1
                else:
                    block = [line]
                    i += 1
                    while (
                        i < len(lines)
                        and lines[i].strip()
                        and not is_special(lines[i])
                    ):
                        block.append(lines[i])
                        i += 1
                    story.append(para(" ".join(block)))
            output = ROOT / "docs" / "print" / language / (name + ".pdf")
            output.parent.mkdir(parents=True, exist_ok=True)
            SimpleDocTemplate(
                str(output),
                pagesize=(595.28, 841.89),
                leftMargin=38,
                rightMargin=38,
                topMargin=32,
                bottomMargin=37,
                title="Minecraft Bedrock Family - " + name,
                author="Minecraft Bedrock Family contributors",
            ).build(story, onFirstPage=footer, onLaterPages=footer)
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError("Empty PDF: " + str(output))
            print(output.relative_to(ROOT))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)
