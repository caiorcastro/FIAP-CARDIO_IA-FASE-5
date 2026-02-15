from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def md_to_simple_paragraphs(md: str) -> list[str]:
    # Markdown minimalista: remove headers e transforma em linhas.
    lines = []
    for raw in md.splitlines():
        s = raw.rstrip()
        if not s:
            lines.append("")
            continue
        # strip markdown headers/bullets
        s = s.lstrip("#").strip()
        s = s.lstrip("-").strip()
        lines.append(s)
    return lines


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=md_path.stem,
    )

    story = []
    lines = md_to_simple_paragraphs(md_path.read_text(encoding="utf-8"))
    for line in lines:
        if not line:
            story.append(Spacer(1, 8))
            continue
        story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), body))
    doc.build(story)


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "document" / "fase5"
    pairs = [
        ("relatorio_conversacional.md", "relatorio_conversacional.pdf"),
        ("ir-alem-1_extracao_clinica.md", "ir-alem-1_extracao_clinica.pdf"),
        ("ir-alem-2_rpa_dados_hibridos.md", "ir-alem-2_rpa_dados_hibridos.pdf"),
    ]

    for md_name, pdf_name in pairs:
        md_path = base / md_name
        pdf_path = base / pdf_name
        build_pdf(md_path, pdf_path)
        print(f"wrote {pdf_path}")


if __name__ == "__main__":
    main()

