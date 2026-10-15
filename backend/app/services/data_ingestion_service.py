import os
import io
import csv
import json
import re
import zipfile
import zlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Tuple, Optional, Any, List
import pandas as pd
import openpyxl
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import DataValidationException


class _TableHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables: List[List[List[str]]] = []
        self.current_table: List[List[str]] = []
        self.current_row: List[str] = []
        self.current_cell: List[str] = []
        self.in_cell: bool = False

    def handle_starttag(self, tag: str, attrs: Any):
        tag_lower = tag.lower()
        if tag_lower in ["td", "th"]:
            self.in_cell = True
            self.current_cell = []
        elif tag_lower == "tr":
            self.current_row = []
        elif tag_lower == "table":
            self.current_table = []

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in ["td", "th"]:
            self.in_cell = False
            self.current_row.append("".join(self.current_cell).strip())
        elif tag_lower == "tr":
            if self.current_row:
                self.current_table.append(self.current_row)
        elif tag_lower == "table":
            if self.current_table:
                self.tables.append(self.current_table)

    def handle_data(self, data: str):
        if self.in_cell:
            self.current_cell.append(data)


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user-provided filenames to prevent path traversal attacks,
    unsafe absolute paths, hidden files, and shell injection characters.
    """
    if not filename:
        return "uploaded_dataset.csv"
    
    # 1. Strip directory components (handles both / and \)
    base = os.path.basename(filename.replace("\\", "/"))
    base = base.replace("\x00", "").strip()
    
    # 2. Prevent directory traversal sequences
    while ".." in base:
        base = base.replace("..", "")
    
    # 3. Strip leading dots (hidden files) or invalid starting characters
    base = re.sub(r"^[.\s]+", "", base)
    
    # 4. Whitelist safe filename characters
    name_parts = os.path.splitext(base)
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name_parts[0])
    ext = re.sub(r"[^a-zA-Z0-9.]", "", name_parts[1])
    
    if not name:
        name = "dataset"
    if not ext:
        ext = ".csv"
        
    sanitized = f"{name}{ext}"
    return sanitized[:200]


class DataIngestionService:
    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id

    async def read_uploaded_file(self, file: UploadFile) -> Tuple[pd.DataFrame, str]:
        """
        Reads CSV, TSV, Excel (.xlsx, .xls, .xlsm, .xlsb), Word (.docx), PDF (.pdf),
        JSON, Parquet, or delimited uploaded files into a pandas DataFrame with magic bytes
        detection, multi-engine parsing, HTML/XML fallback, charset autodetection, and robust error recovery.
        """
        filename = sanitize_filename(file.filename or "uploaded_dataset.csv")

        # Check supported extension
        allowed_extensions = (
            ".csv", ".tsv", ".psv", ".txt", ".tab",
            ".xlsx", ".xls", ".xlsm", ".xlsb", ".xltx",
            ".docx", ".docm", ".dotx",
            ".json", ".jsonl", ".parquet", ".pq",
            ".pdf"
        )
        if not filename.lower().endswith(allowed_extensions):
            raise DataValidationException(
                f"Unsupported file format '{filename}'. Supported formats: CSV, Excel (.xlsx, .xls, .xlsb), "
                "Word (.docx), PDF, JSON, TSV, Parquet."
            )

        try:
            await file.seek(0)
        except Exception:
            pass
        content = await file.read()
        
        if not content or len(content) == 0:
            raise DataValidationException("Uploaded file is empty (0 bytes). Please select a valid data file.")

        # Check maximum file size limit
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise DataValidationException(
                f"Uploaded file size ({len(content) / (1024 * 1024):.1f}MB) exceeds the maximum allowed limit of {max_mb}MB."
            )

        df = self.parse_raw_content(content, filename)
        return df, filename

    def parse_raw_content(self, content: bytes, filename: str = "upload.csv") -> pd.DataFrame:
        """
        Universal content parser supporting:
        - Modern Word Documents (.docx, .docm, .dotx) with table and key-value extraction
        - Excel (.xlsx, .xlsm, .xltx) with openpyxl (data_only=True) and multi-sheet discovery
        - Legacy Excel (.xls / BIFF8) with xlrd
        - PDF documents (.pdf) with stream text & table extraction
        - Disguised HTML/XML tables saved with .xls extension (common in SAP, QuickBooks, Salesforce exports)
        - Delimited text (CSV, TSV, semicolon, pipe) with comment skipping & charset autodetection
        - JSON arrays, object records, JSON Lines, and normalized nested tables
        - Apache Parquet (.parquet) via pyarrow
        """
        df = None
        lower_name = filename.lower()
        errors_encountered: List[str] = []
        
        # Check magic bytes & signatures
        is_zip_container = content.startswith(b"PK\x03\x04")
        is_ole_container = content.startswith(b"\xd0\xcf\x11\xe0")
        is_parquet = content.startswith(b"PAR1") or lower_name.endswith((".parquet", ".pq"))
        is_pdf = content.startswith(b"%PDF") or lower_name.endswith(".pdf")
        
        # Check if Word .docx inside ZIP container
        is_docx = False
        if is_zip_container:
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    if "word/document.xml" in zf.namelist():
                        is_docx = True
            except Exception:
                pass
        
        if lower_name.endswith((".docx", ".docm", ".dotx")):
            is_docx = True

        trimmed_content = content.lstrip()
        is_html_disguised = (
            trimmed_content.lower().startswith((b"<html", b"<!doctype html", b"<table", b"<body"))
            or (b"<table" in trimmed_content[:2048].lower() and b"<tr" in trimmed_content[:2048].lower())
        )
        is_xml_disguised = (
            trimmed_content.startswith(b"<?xml")
            or b"<workbook" in trimmed_content[:1024].lower()
            or b"<ss:workbook" in trimmed_content[:1024].lower()
        )

        # 1. Apache Parquet Files
        if is_parquet:
            try:
                df = pd.read_parquet(io.BytesIO(content))
            except Exception as e:
                errors_encountered.append(f"Parquet: {str(e)}")

        # 2. Word Documents (.docx) — Parsed before Excel to avoid openpyxl ZIP collisions
        if df is None and is_docx:
            try:
                df = self._parse_docx_file(content)
            except Exception as e:
                errors_encountered.append(f"Word (.docx) parser: {str(e)}")

        # 3. PDF Documents (.pdf)
        if df is None and is_pdf:
            try:
                df = self._parse_pdf_file(content)
            except Exception as e:
                errors_encountered.append(f"PDF parser: {str(e)}")

        # 4. HTML / XML tables disguised as .xls or .html files
        if df is None and (is_html_disguised or lower_name.endswith((".html", ".htm")) or (lower_name.endswith(".xls") and is_html_disguised)):
            try:
                df = self._parse_html_table(content)
            except Exception as e:
                errors_encountered.append(f"HTML Table parser: {str(e)}")

        # 5. XML Spreadsheet 2003 disguised as .xls
        if df is None and (is_xml_disguised or (lower_name.endswith(".xls") and is_xml_disguised)):
            try:
                df = self._parse_xml_spreadsheet(content)
            except Exception as e:
                errors_encountered.append(f"XML Spreadsheet: {str(e)}")

        # 6. Modern Excel (.xlsx, .xlsm, .xltx, .xltm)
        if df is None and (is_zip_container or lower_name.endswith((".xlsx", ".xlsm", ".xltx", ".xltm"))):
            # Try openpyxl directly with data_only=True to get computed formula values
            try:
                df = self._parse_openpyxl_workbook(content)
            except Exception as e:
                errors_encountered.append(f"openpyxl data_only: {str(e)}")

            if df is None:
                for engine in ["openpyxl", None]:
                    try:
                        kwargs = {"engine": engine} if engine else {}
                        excel_file = pd.ExcelFile(io.BytesIO(content), **kwargs)
                        
                        best_sheet = None
                        max_cells = 0
                        for sheet_name in excel_file.sheet_names:
                            try:
                                temp_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                                if temp_df is not None and not temp_df.empty:
                                    cell_count = len(temp_df) * len(temp_df.columns)
                                    if cell_count > max_cells:
                                        max_cells = cell_count
                                        best_sheet = temp_df
                            except Exception:
                                continue
                        
                        if best_sheet is not None and not best_sheet.empty:
                            df = self._clean_headers(best_sheet)
                            break
                    except Exception as e:
                        errors_encountered.append(f"Excel (openpyxl): {str(e)}")

        # 7. Legacy Excel (.xls / BIFF8) or OLE container
        if df is None and (is_ole_container or lower_name.endswith(".xls")):
            for engine in ["xlrd", None]:
                try:
                    kwargs = {"engine": engine} if engine else {}
                    excel_file = pd.ExcelFile(io.BytesIO(content), **kwargs)
                    best_sheet = None
                    max_cells = 0
                    for sheet_name in excel_file.sheet_names:
                        try:
                            temp_df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                            if temp_df is not None and not temp_df.empty:
                                cell_count = len(temp_df) * len(temp_df.columns)
                                if cell_count > max_cells:
                                    max_cells = cell_count
                                    best_sheet = temp_df
                        except Exception:
                            continue
                    if best_sheet is not None and not best_sheet.empty:
                        df = self._clean_headers(best_sheet)
                        break
                except Exception as e:
                    errors_encountered.append(f"Excel (xlrd): {str(e)}")

        # 8. Binary Excel (.xlsb)
        if df is None and lower_name.endswith(".xlsb"):
            for engine in ["pyxlsb", "openpyxl", None]:
                try:
                    kwargs = {"engine": engine} if engine else {}
                    df = pd.read_excel(io.BytesIO(content), header=None, **kwargs)
                    if df is not None and not df.empty:
                        df = self._clean_headers(df)
                        break
                except Exception:
                    pass

        # 9. JSON Formats (.json, .jsonl, .ndjson, or content starting with { / [)
        if df is None and (
            lower_name.endswith((".json", ".jsonl", ".ndjson"))
            or trimmed_content.startswith((b"{", b"["))
        ):
            try:
                text_content = content.decode("utf-8-sig").strip()
                def reject_nonfinite(value):
                    raise ValueError(f"Non-finite JSON value '{value}' is not supported. Use null for missing values.")
                try:
                    parsed_json = json.loads(text_content, parse_constant=reject_nonfinite)
                except json.JSONDecodeError:
                    # A JSONL import is atomic: a malformed line must not vanish.
                    lines = [(i, line) for i, line in enumerate(text_content.splitlines(), 1) if line.strip()]
                    parsed_json = []
                    for line_number, line in lines:
                        try:
                            record = json.loads(line, parse_constant=reject_nonfinite)
                        except json.JSONDecodeError as error:
                            raise ValueError(f"Invalid JSON on line {line_number}.") from error
                        if not isinstance(record, dict):
                            raise ValueError(f"JSON line {line_number} must contain an object.")
                        parsed_json.append(record)
                if isinstance(parsed_json, dict):
                    for wrapper_key in ["data", "items", "records", "rows", "results", "table", "transactions", "values", "dataset", "content"]:
                        if isinstance(parsed_json.get(wrapper_key), list):
                            parsed_json = parsed_json[wrapper_key]
                            break
                    else:
                        parsed_json = [parsed_json]
                if not isinstance(parsed_json, list) or not all(isinstance(row, dict) for row in parsed_json):
                    raise ValueError("JSON data must be an object or an array of record objects.")
                df = pd.json_normalize(parsed_json)
                df.attrs['explicit_headers'] = True
            except (ValueError, UnicodeDecodeError) as error:
                raise DataValidationException(f"JSON import failed: {error}") from error

        # Delimited imports validate every record before building a table.
        if df is None and not (is_zip_container or is_ole_container or is_pdf or is_parquet):
            delimiter = "\t" if lower_name.endswith((".tsv", ".tab")) else "|" if lower_name.endswith(".psv") else None
            df = self._parse_delimited_text(content, delimiter=delimiter)

        # 12. Fallback: try Excel parser once more if CSV failed
        if df is None or df.empty:
            for engine in ["openpyxl", "xlrd", None]:
                try:
                    kwargs = {"engine": engine} if engine else {}
                    temp_excel = pd.read_excel(io.BytesIO(content), header=None, **kwargs)
                    if temp_excel is not None and not temp_excel.empty:
                        df = self._clean_headers(temp_excel)
                        break
                except Exception:
                    pass

        # 13. Fallback: HTML table search if content is HTML-like
        if df is None or df.empty:
            try:
                df = self._parse_html_table(content)
            except Exception:
                pass

        if df is None or df.empty:
            err_details = "; ".join(errors_encountered) if errors_encountered else "File format unsupported or content unparseable"
            raise DataValidationException(f"Failed to parse file '{filename}': {err_details}")

        # Preserve blank fields, all-missing columns and explicit source records.

        # Header Auto-Discovery: Elevate genuine header row if top rows are metadata/title banners
        df = self._clean_headers(df)

        return df

    def _parse_docx_file(self, content: bytes) -> Optional[pd.DataFrame]:
        """
        Parses Microsoft Word (.docx) documents, extracting structured tables (<w:tbl>)
        or key-value / delimited lines from paragraphs (<w:p>).
        """
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                if "word/document.xml" not in zf.namelist():
                    return None
                doc_xml = zf.read("word/document.xml")
        except Exception:
            return None

        root = ET.fromstring(doc_xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        # 1. Look for structured tables (<w:tbl>)
        tables = root.findall(".//w:tbl", ns) or root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl")
        best_table_df = None
        max_cells = 0

        for tbl in tables:
            rows_data = []
            rows = tbl.findall(".//w:tr", ns) or tbl.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr")
            for tr in rows:
                cells = tr.findall(".//w:tc", ns) or tr.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc")
                row_vals = []
                for tc in cells:
                    texts = tc.findall(".//w:t", ns) or tc.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                    cell_text = "".join([t.text for t in texts if t.text]).strip()
                    row_vals.append(cell_text)
                if any(v != "" for v in row_vals):
                    rows_data.append(row_vals)

            if rows_data:
                max_cols = max(len(r) for r in rows_data)
                if max_cols > 1 and len(rows_data) >= 2:
                    padded = [r + [""] * (max_cols - len(r)) for r in rows_data]
                    raw_df = pd.DataFrame(padded)
                    cleaned = self._clean_headers(raw_df)
                    score = len(cleaned) * len(cleaned.columns)
                    if score > max_cells:
                        max_cells = score
                        best_table_df = cleaned

        if best_table_df is not None and not best_table_df.empty:
            return best_table_df

        # 2. Fallback: Parse paragraphs (<w:p>) for key-value pairs or structured lines
        paragraphs = root.findall(".//w:p", ns) or root.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")
        lines = []
        for p in paragraphs:
            texts = p.findall(".//w:t", ns) or p.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
            line = "".join([t.text for t in texts if t.text]).strip()
            if line:
                lines.append(line)

        if lines:
            raw_text = "\n".join(lines)
            df_text = self._parse_delimited_text(raw_text.encode("utf-8"))
            if df_text is not None and not df_text.empty and len(df_text.columns) > 1:
                return df_text

            # Check for key: value pairs
            kv_pairs = {}
            for line in lines:
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip()
                    if k and v and len(k) < 40:
                        kv_pairs[k] = v
            if len(kv_pairs) >= 2:
                return pd.DataFrame([kv_pairs])

        return None

    def _parse_pdf_file(self, content: bytes) -> Optional[pd.DataFrame]:
        """
        Parses text streams from PDF files and extracts tabular or delimited records.
        """
        try:
            # Simple stream text extraction
            text_chunks = []
            # Extract plain text strings in parentheses (Tj / TJ / stream)
            matches = re.findall(rb"\((.*?)\)\s*Tj", content)
            for m in matches:
                try:
                    text_chunks.append(m.decode("latin1", errors="ignore"))
                except Exception:
                    pass

            if not text_chunks:
                # Search for uncompressed text blocks
                matches2 = re.findall(rb"\[(.*?)\]\s*TJ", content)
                for m in matches2:
                    sub_matches = re.findall(rb"\((.*?)\)", m)
                    for sm in sub_matches:
                        text_chunks.append(sm.decode("latin1", errors="ignore"))

            if text_chunks:
                joined = "\n".join(text_chunks)
                df = self._parse_delimited_text(joined.encode("utf-8"))
                if df is not None and not df.empty:
                    return df
        except Exception:
            pass
        return None

    def _parse_openpyxl_workbook(self, content: bytes) -> Optional[pd.DataFrame]:
        """
        Parses modern Excel workbook (.xlsx, .xlsm) using openpyxl with data_only=True,
        extracting computed values for formulas, examining all sheets, and choosing the richest table.
        """
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        best_df = None
        max_score = -1

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows_data = []
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None and str(cell).strip() != "" for cell in row):
                    rows_data.append(list(row))

            if not rows_data or len(rows_data) < 1:
                continue

            max_cols = max(len(r) for r in rows_data)
            padded = [r + [None] * (max_cols - len(r)) for r in rows_data]
            raw_df = pd.DataFrame(padded)
            cleaned_df = self._clean_headers(raw_df)

            score = len(cleaned_df) * len(cleaned_df.columns)
            if score > max_score:
                max_score = score
                best_df = cleaned_df

        wb.close()
        return best_df

    def _parse_delimited_text(self, content: bytes, delimiter: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Read text without silently skipping bad rows, coercing identifiers or NA labels."""
        encodings = ["utf-16"] if content.startswith((b"\xff\xfe", b"\xfe\xff")) else ["utf-8-sig", "cp1252", "latin1"]
        decoded = None
        for encoding in encodings:
            try:
                decoded = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if decoded is None or "\x00" in decoded:
            raise DataValidationException("Unable to decode text. Save the file as UTF-8 or UTF-16 with a byte-order mark.")
        lines = decoded.splitlines(keepends=True)
        # Only leading comment metadata is ignored. Inline # signs and later
        # records beginning with comment-like text are part of the dataset.
        while lines and (not lines[0].strip() or lines[0].lstrip().startswith(("#", "//", "--"))):
            lines.pop(0)
        if not lines:
            return None
        text_content = "".join(lines)
        if delimiter is None:
            candidates = []
            for separator in [",", ";", "\t", "|", ":"]:
                try:
                    first = next(csv.reader(io.StringIO(text_content), delimiter=separator, strict=True))
                    candidates.append((len(first), separator))
                except (csv.Error, StopIteration):
                    continue
            if not candidates:
                raise DataValidationException("Malformed delimited file header.")
            delimiter = max(candidates, key=lambda item: item[0])[1]
        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter, strict=True)
        try:
            header = next(reader)
            rows = []
            for row in reader:
                if not row:  # Physical blank line, rather than an explicit empty record.
                    continue
                if len(row) != len(header):
                    raise DataValidationException(
                        f"Delimited record ending at line {reader.line_num} has {len(row)} fields; expected {len(header)}. "
                        "Correct the delimiters or quoting and upload again. No rows were imported."
                    )
                rows.append([value if value != "" else None for value in row])
        except csv.Error as error:
            raise DataValidationException(f"Malformed quoting near line {reader.line_num}. No rows were imported.") from error
        if not rows:
            return None
        frame = pd.DataFrame(rows, columns=header)
        # A parsed header is authoritative even if one of its labels is numeric.
        frame.attrs['explicit_headers'] = True
        return self._clean_headers(frame)

    def _parse_html_table(self, content: bytes) -> pd.DataFrame:
        """Parses HTML tables using built-in HTMLParser with fallback to pd.read_html."""
        try:
            text = content.decode("utf-8", errors="ignore")
            parser = _TableHTMLParser()
            parser.feed(text)
            if parser.tables:
                best_table = max(parser.tables, key=lambda t: len(t) * max(len(r) for r in t) if t else 0)
                if len(best_table) >= 2:
                    max_cols = max(len(r) for r in best_table)
                    padded = [r + [""] * (max_cols - len(r)) for r in best_table]
                    raw_df = pd.DataFrame(padded)
                    return self._clean_headers(raw_df)
        except Exception:
            pass

        tables = pd.read_html(io.BytesIO(content))
        if tables and len(tables) > 0:
            best_t = max(tables, key=lambda t: len(t) * len(t.columns) if not t.empty else 0)
            return self._clean_headers(best_t)

        raise ValueError("No table found in HTML content.")

    def _parse_xml_spreadsheet(self, content: bytes) -> pd.DataFrame:
        """Parses Microsoft XML Spreadsheet 2003 format."""
        root = ET.fromstring(content)
        ns = {"ss": "urn:schemas-microsoft-com:office:spreadsheet"}
        
        rows_data = []
        for row in root.findall(".//ss:Row", ns) or root.findall(".//{urn:schemas-microsoft-com:office:spreadsheet}Row"):
            row_cells = []
            for cell in row.findall("ss:Cell", ns) or row.findall("{urn:schemas-microsoft-com:office:spreadsheet}Cell"):
                data = cell.find("ss:Data", ns) or cell.find("{urn:schemas-microsoft-com:office:spreadsheet}Data")
                val = data.text if data is not None else None
                row_cells.append(val)
            if row_cells and any(c is not None for c in row_cells):
                rows_data.append(row_cells)
        
        if not rows_data:
            raise ValueError("No table rows found in XML spreadsheet.")

        max_cols = max(len(r) for r in rows_data)
        padded_rows = [r + [None] * (max_cols - len(r)) for r in rows_data]
        raw_df = pd.DataFrame(padded_rows)
        return self._clean_headers(raw_df)

    def _clean_headers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Intelligent Header Auto-Discovery:
        Detects if top rows are metadata/title banners or note blocks and elevates the genuine
        column header row. Deduplicates and sanitizes column names without deleting summary records.
        """
        if df.empty:
            return df

        df = df.copy().reset_index(drop=True)
        if df.empty:
            return df

        business_keywords = {
            "date", "time", "timestamp", "dt", "day", "month", "year", "period",
            "id", "order", "invoice", "transaction", "sku", "code", "ticket",
            "revenue", "sales", "amount", "price", "cost", "mrr", "income", "profit", "margin", "total", "subtotal", "spend", "budget", "val",
            "units", "quantity", "qty", "volume", "count", "stock", "level", "inventory", "reorder",
            "region", "channel", "category", "product", "item", "department", "city", "country", "state", "branch", "store",
            "customer", "user", "client", "member", "account", "doctor", "patient", "operator", "employee",
            "status", "tier", "plan", "type", "rate", "percent", "pct", "churn", "conversion", "visitors", "traffic", "kwh", "power"
        }

        best_header_idx = -1
        best_header_score = -1

        current_cols = [str(c).strip() for c in df.columns]
        unnamed_col_count = sum(1 for c in current_cols if not c or "unnamed" in c.lower() or c.isdigit())
        col_kw_hits = sum(1 for c in current_cols if any(k in c.lower() for k in business_keywords))
        
        if unnamed_col_count < len(current_cols) * 0.4 and col_kw_hits >= 1:
            best_header_idx = -1
            best_header_score = col_kw_hits * 10 + (len(current_cols) - unnamed_col_count) * 2

        # Explicit, nonempty column names already supplied by CSV/JSON or an
        # earlier parser must not be replaced by a data row. Header discovery
        # is reserved for raw positional columns or banner/unnamed layouts.
        explicit_headers = bool(df.attrs.get('explicit_headers')) or (unnamed_col_count == 0 and len(set(current_cols)) == len(current_cols))
        scan_limit = 0 if explicit_headers else min(15, len(df))
        for r_idx in range(scan_limit):
            row_vals = df.iloc[r_idx]
            non_null_vals = [str(v).strip() for v in row_vals if pd.notna(v) and str(v).strip() != ""]
            
            if not non_null_vals:
                continue

            if any(not isinstance(v, str) and pd.notna(v) for v in row_vals):
                continue
            if any(re.fullmatch(r"[+\-]?[\d,.%$€£₹()\s]+", v) or re.match(r"^\d{4}[-/]\d", v) for v in non_null_vals):
                continue
            short_str_count = sum(1 for v in non_null_vals if len(v) < 45 and not v.startswith("{") and not v.startswith("["))
            kw_matches = sum(1 for v in non_null_vals if any(k in v.lower() for k in business_keywords))
            cell_coverage = len(non_null_vals) / max(1, len(df.columns))
            
            data_bonus = 0
            if r_idx + 1 < len(df):
                next_row = df.iloc[r_idx + 1]
                for cell in next_row:
                    if pd.notna(cell):
                        cell_str = str(cell).strip()
                        if re.search(r"\d", cell_str):
                            data_bonus += 2

            score = (short_str_count * 3) + (kw_matches * 6) + (cell_coverage * 10) + data_bonus
            
            if len(df.columns) >= 3 and len(non_null_vals) <= 2 and kw_matches == 0:
                score -= 15

            if score > best_header_score and cell_coverage >= 0.6:
                best_header_score = score
                best_header_idx = r_idx

        if best_header_idx >= 0:
            header_row = df.iloc[best_header_idx]
            new_cols = []
            for i, val in enumerate(header_row):
                if pd.notna(val) and str(val).strip() != "":
                    new_cols.append(str(val).strip())
                else:
                    new_cols.append(f"col_{i+1}")
            df.columns = new_cols
            df = df.iloc[best_header_idx + 1:].reset_index(drop=True)

        clean_cols = []
        seen_cols = set()
        for i, col in enumerate(df.columns):
            col_str = str(col).strip()
            if not col_str or col_str.lower().startswith("unnamed:") or (col_str.isdigit() and not explicit_headers and best_header_idx < 0):
                col_name = f"col_{i+1}"
            else:
                col_name = re.sub(r"[\r\n\t]+", " ", col_str).strip()

            base_name = col_name
            suffix = 2
            while col_name in seen_cols:
                col_name = f"{base_name}_{suffix}"
                suffix += 1
            seen_cols.add(col_name)

            clean_cols.append(col_name)

        df.columns = clean_cols

        df.attrs['explicit_headers'] = True

        return df.reset_index(drop=True)
