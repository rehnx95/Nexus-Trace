from app.ingestion.formats import parse_document


def test_txt_parser_preserves_line_provenance():
    parsed = parse_document("report.txt", b"Line one\nRajesh Kumar owns 9876543210")

    assert parsed.rejected_reason is None
    assert parsed.file_type == "txt"
    assert parsed.units[0].source == {"line": 1}
    assert parsed.units[1].source == {"line": 2}
    assert "9876543210" in parsed.units[1].text


def test_csv_parser_preserves_row_provenance():
    parsed = parse_document(
        "cdr.csv",
        b"caller,callee,duration\n9876543210,9123456789,120\n",
    )

    assert parsed.rejected_reason is None
    assert parsed.file_type == "csv"
    assert parsed.units[0].source["row"] == 1
    assert parsed.units[1].source["row"] == 2


def test_xlsx_parser_produces_cell_provenance(tmp_path):
    openpyxl = __import__("openpyxl")
    path = tmp_path / "cdr.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["caller", "callee", "duration"])
    sheet.append(["9876543210", "9123456789", 120])
    workbook.save(path)

    parsed = parse_document(path.name, path.read_bytes())

    assert parsed.rejected_reason is None
    assert parsed.file_type == "xlsx"
    assert parsed.units[0].source["sheet"] == sheet.title
    assert parsed.units[0].source["row"] == 1
    assert len(parsed.units) == 2


def test_scanned_pdf_reports_ocr_limitation():
    from pypdf import PdfWriter
    from io import BytesIO

    pdf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(pdf)
    parsed = parse_document("scan.pdf", pdf.getvalue())

    assert parsed.text == ""
    assert parsed.rejected_reason
    assert "OCR is not enabled" in parsed.rejected_reason


def test_docx_parser_preserves_paragraph_and_table_provenance(tmp_path):
    docx = __import__("docx")
    path = tmp_path / "report.docx"
    document = docx.Document()
    document.add_paragraph("Rajesh Kumar transferred funds.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Vehicle"
    table.rows[0].cells[1].text = "DL01AB1234"
    document.save(path)

    parsed = parse_document(path.name, path.read_bytes())

    assert parsed.rejected_reason is None
    assert parsed.file_type == "docx"
    assert parsed.units[0].source == {"paragraph": 1}
    assert parsed.units[1].source == {"table": 1, "row": 1}
