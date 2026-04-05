import io
import logging
from docx import Document
from docx.oxml.ns import qn
from copy import deepcopy

logger = logging.getLogger(__name__)


class SkillsSectionNotFoundError(Exception):
    pass


# All heading variants we search for (lowercase)
SKILLS_HEADINGS = {"skills", "technical skills", "core skills", "key skills"}


def add_skills_to_resume(file_bytes: bytes, skills: list[str]) -> bytes:
    doc = Document(io.BytesIO(file_bytes))

    # Find the index of the Skills heading paragraph
    skills_idx = None
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip().lower() in SKILLS_HEADINGS:
            skills_idx = i
            logger.info(f"Skills section found at paragraph index {i}: '{para.text.strip()}'")
            break

    if skills_idx is None:
        searched = ", ".join(f'"{h}"' for h in SKILLS_HEADINGS)
        raise SkillsSectionNotFoundError(
            f"No Skills section heading found. Searched for: {searched}"
        )

    # Detect bullet style from the paragraph immediately after the heading
    bullet_style = _detect_bullet_style(doc, skills_idx)
    logger.info(f"Using bullet style: '{bullet_style}'")

    # Insert bullets in reverse order right after the heading so they appear in order
    for skill in reversed(skills):
        _insert_paragraph_after(doc, skills_idx, skill, bullet_style)
        logger.info(f"Inserted bullet: '{skill}'")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


def _detect_bullet_style(doc: Document, heading_idx: int) -> str | None:
    """Return the style name of the first bullet paragraph after the heading, or None."""
    for para in doc.paragraphs[heading_idx + 1 :]:
        # Stop if we hit another heading-level paragraph
        if para.style.name.lower().startswith("heading"):
            break
        style_name = para.style.name
        if "bullet" in style_name.lower() or "list" in style_name.lower():
            return style_name
    return None


def _insert_paragraph_after(
    doc: Document, after_idx: int, text: str, bullet_style: str | None
):
    """Insert a new paragraph directly after the paragraph at after_idx."""
    ref_para = doc.paragraphs[after_idx]

    # Create a new paragraph element by copying the reference paragraph's XML
    new_para = deepcopy(ref_para._element)
    # Clear all runs from the copy so we start with clean text
    for child in list(new_para):
        if child.tag == qn("w:r") or child.tag == qn("w:hyperlink"):
            new_para.remove(child)

    # Insert into the document XML right after the reference paragraph
    ref_para._element.addnext(new_para)

    # Now work with the python-docx Paragraph wrapper for the newly inserted element
    # Find it in the refreshed paragraph list
    new_paragraph = None
    for p in doc.paragraphs:
        if p._element is new_para:
            new_paragraph = p
            break

    if new_paragraph is None:  # fallback — should not happen
        return

    # Apply style
    if bullet_style:
        try:
            new_paragraph.style = doc.styles[bullet_style]
        except KeyError:
            _apply_list_bullet_or_plain(doc, new_paragraph, text)
            return
    else:
        _apply_list_bullet_or_plain(doc, new_paragraph, text)
        return

    new_paragraph.text = text


def _apply_list_bullet_or_plain(doc: Document, paragraph, text: str):
    """Try 'List Bullet' style; fall back to plain paragraph with '• ' prefix."""
    try:
        paragraph.style = doc.styles["List Bullet"]
        paragraph.text = text
    except KeyError:
        paragraph.style = doc.styles["Normal"]
        paragraph.text = f"• {text}"
