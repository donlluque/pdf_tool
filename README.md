# PDF Batch Tools

[Español (README.es.md)](README.es.md)

Extract text from PDFs and batch rename files using regex patterns. Useful for organizing invoice batches, standardizing document archives, and extracting data from scanned documents.

**Key features:**

- Text extraction from specific pages
- Batch rename based on document content
- Regex pattern matching with capture groups
- Dry-run mode to preview changes before applying
- Support for both positional and named regex groups

## Install

```bash
python -m venv .venv && source .venv/bin/activate
# On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick demo

### Extract text from PDF

```bash
python pdf_tools.py extract --pdf samples/invoice_001.pdf
```

**Expected output:**

- Extracted text printed to console with separators
- Log showing number of pages processed

### Batch rename (dry-run preview)

```bash
python pdf_tools.py rename \
  --folder samples \
  --pattern "Invoice Number: #(\d+)" \
  --template "INV_{1}.pdf"
```

**Expected output:**

- Preview of all rename operations
- Warning for files that don't match pattern
- Summary statistics (e.g., "2/3 files would be renamed")
- No actual file changes (dry-run mode)

### Apply rename

```bash
python pdf_tools.py rename \
  --folder samples \
  --pattern "Invoice Number: #(\d+)" \
  --template "INV_{1}.pdf" \
  --apply
```

## Usage

```bash
python pdf_tools.py --help
```

### Extract subcommand

```bash
python pdf_tools.py extract --pdf FILE [--pages N]
```

**Parameters:**

- `--pdf`: PDF file path (required)
- `--pages`: Number of pages to extract (default: 1)

### Rename subcommand

```bash
python pdf_tools.py rename --folder DIR --pattern REGEX --template TEMPLATE [--pages N] [--apply]
```

**Parameters:**

- `--folder`: Directory containing PDFs (required)
- `--pattern`: Regex pattern to search in text (required)
- `--template`: New filename template (required)
- `--pages`: Pages to scan per PDF (default: 1)
- `--apply`: Execute changes (without this flag, runs in dry-run mode)

## Common examples

### Extract from multiple pages

```bash
python pdf_tools.py extract --pdf contract.pdf --pages 3
```

### Rename invoices with date

```bash
# Pattern with multiple capture groups
python pdf_tools.py rename \
  --folder ./invoices \
  --pattern "Invoice: (\d+).*Date: (\d{4}-\d{2}-\d{2})" \
  --template "{2}_INV_{1}.pdf" \
  --pages 2 \
  --apply
```

**Input:** `invoice_old.pdf` with text "Invoice: 12345 ... Date: 2025-01-15"  
**Output:** `2025-01-15_INV_12345.pdf`

### Named regex groups

```bash
python pdf_tools.py rename \
  --folder ./docs \
  --pattern "Order ID: (?P<order>\w+).*Customer: (?P<client>\w+)" \
  --template "{client}_{order}.pdf" \
  --apply
```

**Input:** `document.pdf` with text "Order ID: A7B3 ... Customer: ACME"  
**Output:** `ACME_A7B3.pdf`

### Extract specific text pattern

```bash
# Find all PDFs containing a specific pattern
python pdf_tools.py rename \
  --folder ./archive \
  --pattern "URGENT|PRIORITY" \
  --template "PRIORITY_{1}.pdf"
# Review dry-run output to see which files matched
```

## Screenshots

### Text extraction output

![Text Extraction](images/terminal_extract.png)

### Before rename (original filenames)

![Before Rename](images/before_rename.png)

### After rename (standardized names)

![After Rename](images/after_rename.png)

## How it works

1. **Text extraction**: Uses `pdfplumber` to extract text from specified pages
2. **Pattern matching**: Applies regex to extracted text
3. **Capture groups**: Extracts values using `()` or `(?P<name>)` syntax
4. **Template rendering**: Replaces `{1}`, `{2}` (positional) or `{name}` (named) with captured values
5. **Collision detection**: Skips rename if target filename already exists
6. **Dry-run mode**: Default behavior shows preview without modifying files

## Regex pattern examples

| Use case | Pattern | Template | Example |
| --- | --- | --- | --- |
| Invoice number | `Invoice #(\d+)` | `INV_{1}.pdf` | INV_12345.pdf |
| Date extraction | `Date: (\d{4}-\d{2}-\d{2})` | `{1}_doc.pdf` | 2025-01-15_doc.pdf |
| Order + Customer | `Order: (?P<o>\w+).*Client: (?P<c>\w+)` | `{c}_{o}.pdf` | ACME_A7B3.pdf |
| Case insensitive | `contract` (default flag) | `CONTRACT_{1}.pdf` | Matches "Contract" or "CONTRACT" |

**Regex flags applied:** `re.IGNORECASE | re.MULTILINE`

## Tech Stack

- **Python 3.9+**
- **pdfplumber** - PDF text extraction with layout preservation
- **regex** - Pattern matching with capture groups

## Common troubleshooting

**Issue:** "No text extracted"  
**Solution:** PDF may be scanned image. Use OCR preprocessing (pytesseract) or increase `--pages` if text is on later pages.

**Issue:** "Template error - Replacement index X out of range"  
**Solution:** Template uses `{2}` but regex only captures 1 group. Verify regex at [regex101.com](https://regex101.com)

**Issue:** "Target filename already exists"  
**Solution:** Multiple PDFs match to same output name. Refine template to include unique identifiers (dates, additional groups).

## Next steps

After organizing documents:

- Build searchable database (SQLite with FTS)
- Extract tables using `pdfplumber.extract_tables()`
- Add OCR layer for scanned documents
- Integrate with document management systems
