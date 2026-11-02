"""PDF de leitura de manuscrito agregado; executar com Python que tenha ReportLab."""

import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def render(source, output):
    document = json.loads(source.read_text(encoding="utf-8"))
    fonts = Path("C:/Windows/Fonts")
    for name, file in [
        ("TCCSerif", "times.ttf"),
        ("TCCSerifBold", "timesbd.ttf"),
        ("TCCSerifItalic", "timesi.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily(
        "TCCSerif",
        normal="TCCSerif",
        bold="TCCSerifBold",
        italic="TCCSerifItalic",
        boldItalic="TCCSerifBold",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "TCCBody",
            fontName="TCCSerif",
            fontSize=12,
            leading=17.5,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
            firstLineIndent=18,
        )
    )
    styles.add(
        ParagraphStyle(
            "TCCHeading", fontName="TCCSerifBold", fontSize=17, leading=21, spaceAfter=15
        )
    )
    styles.add(
        ParagraphStyle("TCCTitle", fontName="TCCSerifBold", fontSize=20, leading=24, spaceAfter=12)
    )
    styles.add(
        ParagraphStyle("TCCSmall", fontName="TCCSerif", fontSize=9.5, leading=12, spaceAfter=7)
    )
    styles.add(
        ParagraphStyle(
            "TCCCell", fontName="TCCSerif", fontSize=9.5, leading=11.5, alignment=TA_LEFT
        )
    )
    styles.add(
        ParagraphStyle(
            "TCCReference",
            fontName="TCCSerif",
            fontSize=10,
            leading=13,
            spaceAfter=12,
            wordWrap="CJK",
        )
    )
    styles.add(ParagraphStyle("TCCNumber", parent=styles["TCCCell"], alignment=TA_RIGHT))
    story = []
    width = A4[0] - 5 * cm
    for index, section in enumerate(document["sections"]):
        if index:
            story.append(PageBreak())
        else:
            story += [
                Paragraph(escape(document["title"]), styles["TCCTitle"]),
                Paragraph(
                    escape(document["author"] + " | Estatística - UnB | " + document["date"]),
                    styles["TCCSmall"],
                ),
                Paragraph(
                    "Trecho parcial de métodos, resultados e discussão. PDF de leitura; não é template institucional oficial.",
                    styles["TCCSmall"],
                ),
                Spacer(1, 7),
            ]
        story.append(Paragraph(f"{index + 1}. " + escape(section["title"]), styles["TCCHeading"]))
        story += [Paragraph(escape(p), styles["TCCBody"]) for p in section["paragraphs"]]
        for name in section["tables"]:
            table = document["tables"][name]
            n = len(table["headers"])
            first = 0.32 if n >= 5 else 0.43
            widths = [width * first] + [width * (1 - first) / (n - 1)] * (n - 1)
            rows = [
                [
                    Paragraph(
                        "<b>" + escape(str(c)) + "</b>",
                        styles["TCCCell"] if j == 0 else styles["TCCNumber"],
                    )
                    for j, c in enumerate(table["headers"])
                ]
            ]
            rows += [
                [
                    Paragraph(escape(str(c)), styles["TCCCell"] if j == 0 else styles["TCCNumber"])
                    for j, c in enumerate(row)
                ]
                for row in table["rows"]
            ]
            rendered = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
            rendered.setStyle(
                TableStyle(
                    [
                        ("LINEABOVE", (0, 0), (-1, 0), 0.7, colors.HexColor("#34495A")),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#34495A")),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.7, colors.HexColor("#34495A")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story += [
                KeepTogether(
                    [
                        Spacer(1, 3),
                        Paragraph("<b>" + escape(table["caption"]) + "</b>", styles["TCCSmall"]),
                        rendered,
                        Paragraph("Nota: " + escape(table["note"]), styles["TCCSmall"]),
                    ]
                ),
                Spacer(1, 3),
            ]
        for name, caption in section["figures"]:
            from PIL import Image as PILImage

            path = source.parent / "images" / f"{name}.png"
            with PILImage.open(path) as image:
                w, h = image.size
            story.append(
                KeepTogether(
                    [
                        Image(str(path), width=width, height=width * h / w),
                        Paragraph(escape(caption), styles["TCCSmall"]),
                    ]
                )
            )
        story += [Paragraph(escape(p), styles["TCCBody"]) for p in section["after"]]
    story += [PageBreak(), Paragraph("Referências", styles["TCCHeading"])]
    story += [Paragraph(escape(p), styles["TCCReference"]) for p in document["references"]]

    def page(canvas, doc):
        canvas.saveState()
        canvas.setFont("TCCSerif", 9)
        canvas.setFillColor(colors.HexColor("#536271"))
        canvas.drawString(3 * cm, A4[1] - 1.7 * cm, "TCC - Domínio observado com letras aceitas")
        canvas.drawRightString(A4[0] - 2 * cm, 1.25 * cm, str(doc.page))
        canvas.restoreState()

    pdf = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title=document["title"],
        author=document["author"],
    )
    pdf.build(story, onFirstPage=page, onLaterPages=page)


if __name__ == "__main__":
    render(Path(sys.argv[1]), Path(sys.argv[2]))
