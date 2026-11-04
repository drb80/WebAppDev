"""Build 'Selenium and Capybara.pptx' from the markdown outline, using the
layouts, master, and footer of an existing deck (RSpec and OpenAPI.pptx).

Every slide's text goes in the layout's own white panel (the body
placeholder): bullets in the theme font, code in Menlo. Font sizes are
set explicitly so the text fits, because PowerPoint does not re-run
shrink-to-fit when it opens a generated file."""
import copy
import re
import sys

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Inches, Pt
from pptx.oxml.ns import qn

SOURCE_MD, TEMPLATE, OUTPUT = sys.argv[1], sys.argv[2], sys.argv[3]

# The body placeholder in "Title and Content" / "Title and Code" (inches).
PANEL_LEFT, PANEL_TOP, PANEL_WIDTH, PANEL_HEIGHT = 0.667, 1.75, 12.0, 4.95
INSET_X = 0.1
# The panel is a rounded rectangle; PowerPoint insets its text area by the
# corner radius, so the usable width is about 10.5", not 11.8".
TEXT_AREA_WIDTH = 10.5
INSET_TOP, INSET_BOTTOM = 0.1, 0.1
CODE_FONT = "Menlo"
CODE_CHAR_EM = 0.602      # Menlo advance width, in ems
TEXT_CHAR_EM = 0.50       # Calibri average width, slightly generous
TEXT_LINE_EM = 1.22       # Calibri line height
CODE_LINE_EM = 1.18       # Menlo line height
SAFETY = 0.92             # leave room for estimate error
MAX_TEXT, MIN_TEXT = 28, 14
MAX_CODE, MIN_CODE = 24, 11

NOTES = {
    "The Name": "Huggins' email: 'selenium cures mercury poisoning.' Mercury Interactive made QuickTest Pro.",
    "Two Processes, Three Threads": "Ask: what could go wrong when two threads share one database connection?",
    "Red": "Open tmp/screenshots/ and show the screenshot. The page looks like nothing happened.",
    "Break It": "Do this live: delete the meta line, rerun, then put it back.",
    "Does That Test Work?": "Live: remove hx-boost, rerun only this file, watch exactly one test fail.",
    "hx-boost and Turbo Drive": "Show log/test.log with two GETs per click. Then add data-turbo=\"false\" and show one.",
    "The Biggest Idea Today": "Two processes, and our test is racing the browser. Everything in this part follows from that.",
}


# ---------- markdown parsing ----------

def parse_slides(text):
    """Return slide dicts: {kind, title, blocks}. Blocks are
    ('bullets', [(level, text)]), ('code', [lines]), ('table', [[cells]])."""
    slides = []
    current = None
    in_code = False
    for raw in text.splitlines():
        if in_code:
            if raw.startswith("```"):
                in_code = False
            else:
                current["blocks"][-1][1].append(raw)
            continue
        if raw.startswith("# Part "):
            slides.append({"kind": "section", "title": raw.split(":", 1)[1].strip(), "blocks": []})
            current = None
            continue
        match = re.match(r"^## \d+\. (.*)$", raw)
        if match:
            current = {"kind": "content", "title": match.group(1).strip(), "blocks": []}
            slides.append(current)
            continue
        if current is None:
            continue
        if raw.startswith("```"):
            in_code = True
            current["blocks"].append(("code", []))
        elif raw.startswith("|"):
            cells = [c.strip() for c in raw.strip().strip("|").split("|")]
            if all(re.fullmatch(r"-+", c) for c in cells):
                continue
            if not current["blocks"] or current["blocks"][-1][0] != "table":
                current["blocks"].append(("table", []))
            current["blocks"][-1][1].append(cells)
        elif re.match(r"^\s*- ", raw):
            level = (len(raw) - len(raw.lstrip(" "))) // 2
            if not current["blocks"] or current["blocks"][-1][0] != "bullets":
                current["blocks"].append(("bullets", []))
            current["blocks"][-1][1].append((level, raw.strip()[2:]))
        elif raw.strip() and raw.strip() != "---":
            if not current["blocks"] or current["blocks"][-1][0] != "bullets":
                current["blocks"].append(("bullets", []))
            current["blocks"][-1][1].append((-1, raw.strip()))
    # The first content slide is the deck's title slide; it goes first,
    # ahead of the Part 1 divider.
    first = next(s for s in slides if s["kind"] == "content")
    slides.remove(first)
    first["kind"] = "title"
    return [first] + slides


INLINE = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")


def runs_of(text):
    """Split inline markdown into (text, style) runs."""
    parts = []
    for piece in INLINE.split(text):
        if not piece:
            continue
        if piece.startswith("`"):
            parts.append((piece[1:-1], "code"))
        elif piece.startswith("**"):
            parts.append((piece[2:-2], "bold"))
        elif piece.startswith("*") and piece.endswith("*") and len(piece) > 2:
            parts.append((piece[1:-1], "italic"))
        else:
            parts.append((piece, "plain"))
    return parts


def plain_length(text):
    return sum(len(t) for t, _ in runs_of(text))


# ---------- sizing ----------

def wrapped_lines(chars, width_in, size_pt, em):
    per_line = max(1, int(width_in * 72 / (size_pt * em)))
    return max(1, -(-chars // per_line))


def level_size(size, level):
    return size * 0.86 if level >= 1 else size


def text_width(level):
    indent = {-1: 0.0, 0: 0.5, 1: 1.08}.get(level, 1.08)
    return TEXT_AREA_WIDTH - indent


def blocks_height(blocks, text_size, code_size):
    height = 0.0
    for index, (kind, content) in enumerate(blocks):
        gap_pt = 0 if index == 0 else 0.5 * text_size
        height += gap_pt / 72
        if kind == "bullets":
            for level, text in content:
                pt = level_size(text_size, level)
                lines = wrapped_lines(plain_length(text) + 1, text_width(level), pt, TEXT_CHAR_EM)
                height += lines * pt * TEXT_LINE_EM / 72 + 0.2 * pt / 72
        elif kind == "code":
            height += len(content) * code_size * CODE_LINE_EM / 72
    return height


def longest_code_line(blocks):
    return max((len(line) for kind, c in blocks if kind == "code" for line in c), default=0)


def fit(blocks):
    """Largest sizes where the blocks fit in the panel."""
    available = (PANEL_HEIGHT - INSET_TOP - INSET_BOTTOM) * SAFETY
    longest = longest_code_line(blocks)
    width_cap = MAX_CODE
    if longest:
        width_cap = TEXT_AREA_WIDTH * 0.97 * 72 / (longest * CODE_CHAR_EM)
    for text_size in range(MAX_TEXT, MIN_TEXT - 1, -1):
        code_size = max(MIN_CODE, min(width_cap, text_size * 0.85, MAX_CODE))
        if blocks_height(blocks, text_size, code_size) <= available:
            return text_size, code_size
    return MIN_TEXT, max(MIN_CODE, min(width_cap, MIN_TEXT * 0.85))


# ---------- XML helpers ----------

def add_run(paragraph, text, style, size, code_size=None):
    run = paragraph.add_run()
    run.text = text
    if style == "code":
        run.font.size = Pt(code_size or size)
        run.font.name = CODE_FONT
    else:
        run.font.size = Pt(size)
        run.font.bold = True if style == "bold" else None
        run.font.italic = True if style == "italic" else None


def paragraph_format(paragraph, level, space_before_pt):
    """Match the master's bullets: '•' level 1, '–' level 2; none for code."""
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        pPr.remove(child)
    if level in (0, 1):
        mar, ind, char = (457166, -457166, "•") if level == 0 else (990526, -380973, "–")
    else:
        mar, ind, char = 0, 0, None
    pPr.set("marL", str(mar))
    pPr.set("indent", str(ind))
    spc = etree.SubElement(pPr, qn("a:spcBef"))
    etree.SubElement(spc, qn("a:spcPts")).set("val", str(int(space_before_pt * 100)))
    if char:
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
        etree.SubElement(pPr, qn("a:buChar")).set("char", char)
    else:
        etree.SubElement(pPr, qn("a:buNone"))


def no_autofit(text_frame):
    bodyPr = text_frame._txBody.find(qn("a:bodyPr"))
    for child in list(bodyPr):
        if child.tag in (qn("a:normAutofit"), qn("a:spAutoFit"), qn("a:noAutofit")):
            bodyPr.remove(child)
    etree.SubElement(bodyPr, qn("a:noAutofit"))


def fill_panel(text_frame, blocks, text_size, code_size):
    text_frame.word_wrap = True
    text_frame.margin_top = Inches(INSET_TOP)
    text_frame.margin_bottom = Inches(INSET_BOTTOM)
    first = True
    for index, (kind, content) in enumerate(blocks):
        block_gap = 0 if index == 0 else 0.5 * text_size
        if kind == "code":
            for line_number, line in enumerate(content or [""]):
                paragraph = text_frame.paragraphs[0] if first else text_frame.add_paragraph()
                first = False
                paragraph_format(paragraph, -1, block_gap if line_number == 0 else 0)
                add_run(paragraph, line if line else " ", "code", code_size, code_size)
        else:
            for item_number, (level, text) in enumerate(content):
                paragraph = text_frame.paragraphs[0] if first else text_frame.add_paragraph()
                first = False
                pt = level_size(text_size, level)
                space = 0.2 * pt + (block_gap if item_number == 0 else 0)
                paragraph_format(paragraph, level, space)
                for piece, style in runs_of(text):
                    add_run(paragraph, piece, style, pt, pt * 0.92)
    no_autofit(text_frame)


def add_footer(slide, layout):
    """Copy the layout's date, footer, and slide number onto the slide."""
    tree = slide.shapes._spTree
    next_id = max(int(e.get("id")) for e in tree.iter(qn("p:cNvPr"))) + 1
    for ph in layout.placeholders:
        if ph.placeholder_format.type in (PP_PLACEHOLDER.DATE, PP_PLACEHOLDER.FOOTER,
                                          PP_PLACEHOLDER.SLIDE_NUMBER):
            element = copy.deepcopy(ph._element)
            element.find(".//" + qn("p:cNvPr")).set("id", str(next_id))
            next_id += 1
            tree.append(element)


def set_title(slide, title, base=48):
    shape = slide.shapes.title
    size = min(base, (PANEL_WIDTH - 0.4) * 72 / (max(plain_length(title), 1) * 0.52))
    shape.text_frame.text = ""
    paragraph = shape.text_frame.paragraphs[0]
    for piece, style in runs_of(title):
        add_run(paragraph, piece, style, size, size * 0.9)
    no_autofit(shape.text_frame)


# ---------- building ----------

def remove_all_slides(prs):
    ids = prs.slides._sldIdLst
    for sld_id in list(ids):
        prs.part.drop_rel(sld_id.get(qn("r:id")))
        ids.remove(sld_id)


def layout_named(prs, name):
    return next(l for l in prs.slide_layouts if l.name == name)


def body_of(slide):
    return next(s for s in slide.placeholders if s.placeholder_format.idx == 1)


def build_table_slide(prs, spec):
    layout = layout_named(prs, "Title Only")
    slide = prs.slides.add_slide(layout)
    set_title(slide, spec["title"])
    rows = spec["blocks"][0][1]
    widths = [3.6, 2.2, 1.8, 4.4]
    size = 20
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Inches(PANEL_LEFT), Inches(PANEL_TOP),
                                   Inches(PANEL_WIDTH), Inches(0.6 * len(rows)))
    table = shape.table
    for c, w in enumerate(widths):
        table.columns[c].width = Inches(w)
    for r, row in enumerate(rows):
        for c, cell_text in enumerate(row):
            cell = table.cell(r, c)
            cell.text_frame.text = ""
            paragraph = cell.text_frame.paragraphs[0]
            for piece, style in runs_of(cell_text):
                add_run(paragraph, piece, "bold" if r == 0 and style == "plain" else style,
                        size, size * 0.9)
    return slide, layout


def build_content(prs, spec):
    blocks = spec["blocks"]
    if any(kind == "table" for kind, _ in blocks):
        slide, layout = build_table_slide(prs, spec)
    else:
        code_only = all(kind == "code" for kind, _ in blocks)
        layout = layout_named(prs, "Title and Code" if code_only else "Title and Content")
        slide = prs.slides.add_slide(layout)
        set_title(slide, spec["title"])
        body = body_of(slide)
        # Code layout's box is a little higher and taller; use one panel
        # size everywhere so slides don't jump.
        body.left, body.top = Inches(PANEL_LEFT), Inches(PANEL_TOP)
        body.width, body.height = Inches(PANEL_WIDTH), Inches(PANEL_HEIGHT)
        text_size, code_size = fit(blocks)
        fill_panel(body.text_frame, blocks, text_size, code_size)
    add_footer(slide, layout)
    if spec["title"] in NOTES:
        slide.notes_slide.notes_text_frame.text = NOTES[spec["title"]]


def build_title(prs, spec):
    layout = layout_named(prs, "Title Slide")
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text_frame.text = spec["title"]
    subtitle = next(s for s in slide.placeholders if s.placeholder_format.idx == 10)
    subtitle.text_frame.text = ""
    add_run(subtitle.text_frame.paragraphs[0], spec["blocks"][0][1][0][1], "plain", 28)
    add_footer(slide, layout)


def build_section(prs, spec):
    layout = layout_named(prs, "Section")
    slide = prs.slides.add_slide(layout)
    set_title(slide, spec["title"], base=54)
    add_footer(slide, layout)


def set_slide_total(prs, total):
    """The master shows the deck's total as typed text next to the slide
    number (it said 49, the RSpec deck's count)."""
    for shape in prs.slide_master.shapes:
        if shape.has_text_frame and shape.text_frame.text.strip().isdigit():
            shape.text_frame.paragraphs[0].runs[0].text = str(total)


def main():
    slides = parse_slides(open(SOURCE_MD, encoding="utf-8").read())
    prs = Presentation(TEMPLATE)
    remove_all_slides(prs)
    builders = {"title": build_title, "section": build_section, "content": build_content}
    for spec in slides:
        builders[spec["kind"]](prs, spec)
    set_slide_total(prs, len(slides))
    prs.core_properties.title = "Selenium and Capybara"
    prs.save(OUTPUT)
    print(len(slides), "slides written to", OUTPUT)


main()
