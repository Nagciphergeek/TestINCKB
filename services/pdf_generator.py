"""
services/pdf_generator.py
Generates a professional PDF from a Markdown KB article using ReportLab.
Pattern from FriAI pdf_generator.py — upgraded for KB article structure.
"""
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER


def _escape(text: str) -> str:
    """Escape XML special characters for ReportLab Paragraph."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def create_kb_pdf(markdown_text: str, title: str = "KB Article", review_status: str = "New") -> bytes:
    """
    Convert a Markdown KB article into a styled PDF.
    Returns PDF bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "KBTitle", parent=styles["Title"],
        fontSize=20, spaceAfter=4, textColor=colors.HexColor("#1a237e")
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#555555"), spaceAfter=2
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=16, spaceBefore=10, spaceAfter=4,
        textColor=colors.HexColor("#1a237e")
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, spaceBefore=8, spaceAfter=3,
        textColor=colors.HexColor("#283593")
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, spaceAfter=3, leading=14
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=styles["Normal"],
        fontSize=10, spaceAfter=2, leftIndent=12, bulletIndent=0, leading=13
    )
    code_style = ParagraphStyle(
        "Code", parent=styles["Code"],
        fontSize=8, backColor=colors.HexColor("#f5f5f5"),
        leftIndent=10, spaceAfter=4, leading=11,
        fontName="Courier"
    )

    story = []

    # Header block
    story.append(Paragraph(_escape(title), title_style))
    story.append(Paragraph(f"Review Status: <b>{_escape(review_status)}</b>", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e"), spaceAfter=8))

    lines = markdown_text.splitlines()
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Code block fence
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lines = []
            else:
                # End of code block — render collected lines
                in_code_block = False
                code_text = "\n".join(code_lines)
                story.append(Preformatted(code_text, code_style))
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # H1
        if line.startswith("# "):
            story.append(Paragraph(_escape(line[2:].strip()), h1_style))

        # H2
        elif line.startswith("## "):
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#90caf9"), spaceAfter=2))
            story.append(Paragraph(_escape(line[3:].strip()), h2_style))

        # Bold metadata lines (**Category:** etc.)
        elif line.strip().startswith("**") and ":**" in line:
            clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _escape(line.strip()))
            story.append(Paragraph(clean, body_style))

        # Numbered list
        elif re.match(r"^\d+\.\s", line.strip()):
            text = re.sub(r"^\d+\.\s", "", line.strip())
            text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", _escape(text))
            story.append(Paragraph(f"• {text}", bullet_style))

        # Bullet list
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            text = line.strip()[2:]
            text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", _escape(text))
            story.append(Paragraph(f"• {text}", bullet_style))

        # Empty line
        elif line.strip() == "":
            story.append(Spacer(1, 4))

        # Normal paragraph
        else:
            clean = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _escape(line))
            clean = re.sub(r"\*(.+?)\*", r"<i>\1</i>", clean)
            clean = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", clean)
            story.append(Paragraph(clean, body_style))

        i += 1

    doc.build(story)
    return buffer.getvalue()
