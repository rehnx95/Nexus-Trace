from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePath


@dataclass(frozen=True)
class SourceUnit:
    text: str
    source: dict
    offset_start: int
    offset_end: int


@dataclass(frozen=True)
class ParsedDocument:
    filename: str
    file_type: str
    text: str
    units: list[SourceUnit] = field(default_factory=list)
    rejected_reason: str | None = None


def _append_text(parts: list[str], units: list[SourceUnit], text: str, source: dict) -> None:
    if not text:
        return
    offset_start = sum(len(part) + 1 for part in parts)
    parts.append(text.strip())
    units.append(SourceUnit(
        text=text.strip(),
        source=source,
        offset_start=offset_start,
        offset_end=offset_start + len(text.strip()),
    ))


def _parse_text(content: bytes, filename: str, file_type: str) -> ParsedDocument:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text="",
            rejected_reason="File is not valid UTF-8 text.",
        )
    if not text.strip():
        return ParsedDocument(
            filename=filename,
            file_type=file_type,
            text="",
            rejected_reason="File is empty.",
        )
    parts = text.splitlines()
    units = []
    offset = 0
    for line_number, line in enumerate(parts, start=1):
        if line.strip():
            units.append(SourceUnit(
                text=line,
                source={"line": line_number},
                offset_start=offset,
                offset_end=offset + len(line),
            ))
        offset += len(line) + 1
    return ParsedDocument(filename, file_type, text, units)


def _parse_csv(content: bytes, filename: str, delimiter: str) -> ParsedDocument:
    decoded = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(decoded), delimiter=delimiter)
    parts = []
    units = []
    for row_number, row in enumerate(reader, start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        text = " | ".join(f"{value.strip()}" for value in row if value.strip())
        _append_text(
            parts,
            units,
            text,
            {"row": row_number, "columns": row},
        )
    return ParsedDocument(filename, "csv" if delimiter == "," else "tsv", "\n".join(parts), units)


def _parse_excel(content: bytes, filename: str) -> ParsedDocument:
    try:
        import openpyxl
        from openpyxl.utils.exceptions import InvalidFileException
    except ImportError:
        return ParsedDocument(filename, "xlsx", "", "Excel support dependency is unavailable.")

    if filename.lower().endswith(".xls"):
        return ParsedDocument(
            filename,
            "xls",
            "",
            "Legacy .xls files are unsupported. Upload an .xlsx or CSV version.",
        )
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except (InvalidFileException, zipfile.BadZipFile):
        return ParsedDocument(filename, "xlsx", "", "File is not a valid .xlsx workbook.")
    parts = []
    units = []
    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            values = [("" if value is None else str(value).strip()) for value in row]
            if not any(values):
                continue
            text = ", ".join(value.replace(",", " ") for value in values if value)
            _append_text(
                parts,
                units,
                text,
                {"sheet": sheet_name, "row": row_number, "cells": values},
            )
    workbook.close()
    if not parts:
        return ParsedDocument(filename, "xlsx", "", "Workbook contains no non-empty cells.")
    return ParsedDocument(filename, "xlsx", "\n".join(parts), units)


def _parse_pdf(content: bytes, filename: str) -> ParsedDocument:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ParsedDocument(filename, "pdf", "", "PDF support dependency is unavailable.")

    reader = PdfReader(io.BytesIO(content))
    parts = []
    units = []
    scanned_pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            _append_text(parts, units, text, {"page": page_number})
        else:
            scanned_pages.append(page_number)
    if not parts:
        return ParsedDocument(
            filename,
            "pdf",
            "",
            units,
            (
                "PDF contains no extractable text. OCR is not enabled; "
                f"scanned pages: {', '.join(map(str, scanned_pages))}."
            ),
        )
    return ParsedDocument(filename, "pdf", "\n".join(parts), units)


def _parse_docx(content: bytes, filename: str) -> ParsedDocument:
    try:
        from docx import Document
    except ImportError:
        return ParsedDocument(filename, "docx", "", "DOCX support dependency is unavailable.")

    document = Document(io.BytesIO(content))
    parts = []
    units = []
    for paragraph_number, paragraph in enumerate(document.paragraphs, start=1):
        _append_text(
            parts,
            units,
            paragraph.text,
            {"paragraph": paragraph_number},
        )
    for table_number, table in enumerate(document.tables, start=1):
        for row_number, row in enumerate(table.rows, start=1):
            text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            _append_text(
                parts,
                units,
                text,
                {"table": table_number, "row": row_number},
            )
    if not parts:
        return ParsedDocument(filename, "docx", "", "DOCX contains no readable text.")
    return ParsedDocument(filename, "docx", "\n".join(parts), units)


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    suffix = PurePath(filename).suffix.lower().lstrip(".")
    if suffix in {"txt", "text"}:
        return _parse_text(content, filename, "txt")
    if suffix == "csv":
        return _parse_csv(content, filename, ",")
    if suffix == "tsv":
        return _parse_csv(content, filename, "\t")
    if suffix in {"xlsx", "xls"}:
        return _parse_excel(content, filename)
    if suffix == "pdf":
        return _parse_pdf(content, filename)
    if suffix == "docx":
        return _parse_docx(content, filename)
    return ParsedDocument(filename, suffix, "", "Unsupported file format.")
