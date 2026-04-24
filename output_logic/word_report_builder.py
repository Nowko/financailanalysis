from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from output_logic.source_report_builder import build_source_report_text
from output_logic.sentence_builder import build_summary_text
from output_logic.table_builder import build_analysis_tables


WORD_MAIN_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_CORE_REL_TYPE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
APP_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties"
DOCUMENT_REL_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
CORE_PROP_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
DCMI_TYPE_NS = "http://purl.org/dc/dcmitype/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

HEADER_FILL = "EEF2F6"
GOOD_FILL = "E8F5E9"
BAD_FILL = "FDEBEC"
NOTE_COLOR = "666666"
TITLE_COLOR = "1F2937"


def build_word_report_bytes(profile, analysis, generated_at=None) -> bytes:
    generated_at = generated_at or datetime.now()
    title_name = getattr(profile, "name", "").strip() or "분석대상"
    document_title = f"{title_name} 재무분석 보고서"
    summary_text = build_summary_text(profile, analysis)
    source_report_text = build_source_report_text(profile, analysis)
    tables = build_analysis_tables(profile, analysis)

    document_xml = _build_document_xml(document_title, generated_at, summary_text, tables, source_report_text)
    core_xml = _build_core_properties_xml(document_title, generated_at)
    app_xml = _build_app_properties_xml()

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _build_content_types_xml())
        archive.writestr("_rels/.rels", _build_root_relationships_xml())
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/_rels/document.xml.rels", _build_document_relationships_xml())
    return buffer.getvalue()


def write_word_report(path, profile, analysis, generated_at=None):
    target = Path(path)
    target.write_bytes(build_word_report_bytes(profile, analysis, generated_at=generated_at))


def _build_content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )


def _build_root_relationships_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PACKAGE_REL_NS}">'
        f'<Relationship Id="rId1" Type="{DOCUMENT_REL_TYPE}" Target="word/document.xml"/>'
        f'<Relationship Id="rId2" Type="{PACKAGE_CORE_REL_TYPE}" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{APP_REL_TYPE}" Target="docProps/app.xml"/>'
        "</Relationships>"
    )


def _build_document_relationships_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PACKAGE_REL_NS}"></Relationships>'
    )


def _build_core_properties_xml(title: str, generated_at: datetime) -> str:
    timestamp = generated_at.replace(microsecond=0).isoformat() + "Z"
    escaped_title = escape(title)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<cp:coreProperties xmlns:cp="{CORE_PROP_NS}" xmlns:dc="{DC_NS}" '
        f'xmlns:dcterms="{DCTERMS_NS}" xmlns:dcmitype="{DCMI_TYPE_NS}" xmlns:xsi="{XSI_NS}">'
        f"<dc:title>{escaped_title}</dc:title>"
        "<dc:creator>Codex</dc:creator>"
        "<cp:lastModifiedBy>Codex</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>'
        "</cp:coreProperties>"
    )


def _build_app_properties_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>Microsoft Office Word</Application>"
        "</Properties>"
    )


def _build_document_xml(title: str, generated_at: datetime, summary_text: str, tables: list, source_report_text: str) -> str:
    body_parts = [
        _paragraph(title, bold=True, size=30, color=TITLE_COLOR, align="center", after=220),
        _paragraph(
            f"생성일: {generated_at.strftime('%Y-%m-%d %H:%M')}",
            size=20,
            color=NOTE_COLOR,
            align="center",
            after=280,
        ),
        _heading("분석 요약", level=1),
    ]
    body_parts.extend(_paragraphs_from_text(summary_text))

    if tables:
        body_parts.append(_heading("비교표", level=1))
        for table in tables:
            body_parts.append(_heading(table.get("title", ""), level=2))
            description = (table.get("description") or "").strip()
            if description:
                body_parts.extend(_paragraphs_from_text(description, note=True))
            body_parts.append(_table_xml(table))
            body_parts.append(_blank_paragraph())

    if source_report_text.strip():
        body_parts.append(_heading("자료 근거", level=1))
        body_parts.extend(_paragraphs_from_text(source_report_text, note=True))

    body_parts.append(_section_properties())
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{WORD_MAIN_NS}"><w:body>'
        + "".join(body_parts)
        + "</w:body></w:document>"
    )


def _paragraphs_from_text(text: str, note: bool = False) -> list:
    paragraphs = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            paragraphs.append(_blank_paragraph())
            continue
        is_header = line.startswith("[") and line.endswith("]")
        paragraphs.append(
            _paragraph(
                line,
                bold=is_header,
                size=24 if is_header else 21,
                color=NOTE_COLOR if note and not is_header else None,
                after=90 if note else 120,
            )
        )
    return paragraphs


def _heading(text: str, level: int = 1) -> str:
    sizes = {1: 26, 2: 23, 3: 21}
    return _paragraph(text, bold=True, size=sizes.get(level, 21), color=TITLE_COLOR, after=120)


def _blank_paragraph() -> str:
    return "<w:p/>"


def _paragraph(text: str, bold: bool = False, size: int = 21, color: str = None, align: str = "left", after: int = 120) -> str:
    escaped_text = escape(text)
    run_props = []
    if bold:
        run_props.append("<w:b/><w:bCs/>")
    if size:
        run_props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if color:
        run_props.append(f'<w:color w:val="{color}"/>')
    paragraph_props = [f'<w:spacing w:after="{after}"/>']
    align_value = {"center": "center", "right": "right"}.get(align, "left")
    if align_value != "left":
        paragraph_props.append(f'<w:jc w:val="{align_value}"/>')
    run_props_xml = f"<w:rPr>{''.join(run_props)}</w:rPr>" if run_props else ""
    paragraph_props_xml = f"<w:pPr>{''.join(paragraph_props)}</w:pPr>" if paragraph_props else ""
    return (
        "<w:p>"
        f"{paragraph_props_xml}"
        "<w:r>"
        f"{run_props_xml}"
        f'<w:t xml:space="preserve">{escaped_text}</w:t>'
        "</w:r>"
        "</w:p>"
    )


def _table_xml(table: dict) -> str:
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    if not columns or not rows:
        return ""

    total_weight = sum(max(int(column.get("weight", 1)), 1) for column in columns)
    widths = [max(900, int(9000 * max(int(column.get("weight", 1)), 1) / total_weight)) for column in columns]
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)

    header_row = _table_row(
        widths,
        [column.get("title", "") for column in columns],
        header=True,
        fill=HEADER_FILL,
        aligns=[column.get("anchor", "w") for column in columns],
    )
    data_rows = []
    for row in rows:
        tone_fill = _tone_fill(row.get("tone"))
        cell_values = [str(row.get("values", {}).get(column.get("id"), "")) for column in columns]
        data_rows.append(
            _table_row(
                widths,
                cell_values,
                header=False,
                fill=tone_fill,
                aligns=[column.get("anchor", "w") for column in columns],
            )
        )

    return (
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblW w:w="0" w:type="auto"/>'
        '<w:tblLayout w:type="fixed"/>'
        "<w:tblBorders>"
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        '<w:left w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        '<w:right w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        '<w:insideH w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        '<w:insideV w:val="single" w:sz="8" w:space="0" w:color="D0D7DE"/>'
        "</w:tblBorders>"
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{header_row}"
        + "".join(data_rows)
        + "</w:tbl>"
    )


def _table_row(widths: Iterable[int], values: Iterable[str], header: bool, fill: str, aligns: Iterable[str]) -> str:
    cells = []
    for width, value, anchor in zip(widths, values, aligns):
        cells.append(_table_cell(width, value, header=header, fill=fill, anchor=anchor))
    return f"<w:tr>{''.join(cells)}</w:tr>"


def _table_cell(width: int, text: str, header: bool, fill: str, anchor: str = "w") -> str:
    paragraph_align = {"e": "right", "center": "center"}.get(anchor, "left")
    escaped_text = escape(str(text))
    run_props = ['<w:sz w:val="20"/><w:szCs w:val="20"/>']
    if header:
        run_props.insert(0, "<w:b/><w:bCs/>")
    paragraph_props = ['<w:spacing w:after="60"/>']
    if paragraph_align != "left":
        paragraph_props.append(f'<w:jc w:val="{paragraph_align}"/>')
    return (
        "<w:tc>"
        "<w:tcPr>"
        f'<w:tcW w:w="{width}" w:type="dxa"/>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
        "</w:tcPr>"
        "<w:p>"
        f"<w:pPr>{''.join(paragraph_props)}</w:pPr>"
        "<w:r>"
        f"<w:rPr>{''.join(run_props)}</w:rPr>"
        f'<w:t xml:space="preserve">{escaped_text}</w:t>'
        "</w:r>"
        "</w:p>"
        "</w:tc>"
    )


def _tone_fill(tone: str) -> str:
    if tone == "good":
        return GOOD_FILL
    if tone == "bad":
        return BAD_FILL
    return "FFFFFF"


def _section_properties() -> str:
    return (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
