#!/usr/bin/env python3
"""
PDF Batch Tools
Extract text from PDFs and batch rename using regex patterns.
"""
import argparse
import logging
import re
from pathlib import Path
import pdfplumber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def extract_text(pdf_path: Path, max_pages: int = 1) -> str:
    """
    Extracts text from first N pages of a PDF.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Number of pages to process
        
    Returns:
        Concatenated text from all pages
        
    Raises:
        Exception: On PDF read errors (logged but not re-raised)
    """
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = min(len(pdf.pages), max_pages)
            for i in range(total):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text_parts.append(page_text)
            logger.info(f"✓ Extracted {total} page(s) from {pdf_path.name}")
    except Exception as e:
        logger.error(f"Failed to extract from {pdf_path.name}: {e}")
        return ""
    
    return "\n".join(text_parts)


def rename_from_text(
    folder: Path,
    pattern: str,
    template: str,
    max_pages: int = 1,
    dry_run: bool = True
) -> int:
    """
    Renames PDFs based on extracted text using regex pattern.
    
    Args:
        folder: Directory containing PDF files
        pattern: Regex pattern to search in text (can have capture groups)
        template: New filename template using {1}, {2} for groups or {name} for named groups
        max_pages: Pages to scan per PDF
        dry_run: If True, only preview changes without applying
        
    Returns:
        Number of files successfully renamed
    """
    # Validate regex pattern
    try:
        rx = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
    except re.error as e:
        logger.error(f"Invalid regex pattern: {e}")
        return 0
    
    pdfs = list(folder.glob("*.pdf"))
    if not pdfs:
        logger.warning(f"No PDF files found in {folder}")
        return 0
    
    logger.info(f"Processing {len(pdfs)} PDF(s) in {folder}")
    logger.info(f"Pattern: {pattern}")
    logger.info(f"Template: {template}")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}")
    print("-" * 60)
    
    matched = 0
    for pdf in pdfs:
        txt = extract_text(pdf, max_pages=max_pages)
        if not txt:
            logger.warning(f"⚠ {pdf.name}: No text extracted")
            continue
        
        m = rx.search(txt)
        if not m:
            logger.warning(f"⚠ {pdf.name}: Pattern not found")
            continue
        
        try:
            # Add dummy element at index 0 to make groups 1-indexed
            groups_1indexed = (None,) + m.groups()
            new_name = template.format(*groups_1indexed, **m.groupdict())
            if not new_name.endswith(".pdf"):
                new_name += ".pdf"
            
            new_path = pdf.with_name(new_name)
            
            # Prevent overwriting existing files
            if new_path.exists() and new_path != pdf:
                logger.error(f"✗ {pdf.name}: Target '{new_name}' already exists, skipping")
                continue
            
            logger.info(f"{'[DRY]' if dry_run else '✓'} {pdf.name} → {new_name}")
            
            if not dry_run:
                pdf.rename(new_path)
            
            matched += 1
            
        except (IndexError, KeyError) as e:
            logger.error(f"✗ {pdf.name}: Template error - {e}")
            logger.info(f"    Regex captured: {m.groups()} / {m.groupdict()}")
            continue
    
    print("-" * 60)
    logger.info(f"Summary: {matched}/{len(pdfs)} files {'would be' if dry_run else ''} renamed")
    if dry_run:
        logger.info("Run with --apply to execute changes")
    
    return matched


def main() -> int:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="PDF text extraction and batch renaming tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from first page
  python pdf_tools.py extract --pdf invoice.pdf

  # Extract from first 3 pages
  python pdf_tools.py extract --pdf report.pdf --pages 3

  # Dry-run rename (preview changes)
  python pdf_tools.py rename \\
    --folder ./invoices \\
    --pattern "Invoice #(\\d+)" \\
    --template "INV_{1}.pdf"

  # Apply rename with named groups
  python pdf_tools.py rename \\
    --folder ./docs \\
    --pattern "Order ID: (?P<order>\\w+)" \\
    --template "ORDER_{order}.pdf" \\
    --apply

  # Extract invoice number and date
  python pdf_tools.py rename \\
    --folder ./bills \\
    --pattern "Invoice: (?P<num>\\d+).*Date: (?P<date>\\d{4}-\\d{2}-\\d{2})" \\
    --template "{date}_INV_{num}.pdf" \\
    --pages 2 \\
    --apply
        """
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Subcommand: extract
    p_extract = sub.add_parser(
        "extract",
        help="Extract text from PDF"
    )
    p_extract.add_argument(
        "--pdf",
        required=True,
        type=Path,
        help="PDF file path"
    )
    p_extract.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to extract (default: 1)"
    )

    # Subcommand: rename
    p_rename = sub.add_parser(
        "rename",
        help="Batch rename PDFs using text patterns"
    )
    p_rename.add_argument(
        "--folder",
        required=True,
        type=Path,
        help="Folder containing PDFs"
    )
    p_rename.add_argument(
        "--pattern",
        required=True,
        help=r"Regex pattern (e.g., 'Invoice #(\d+)' or 'ID: (?P<id>\w+)')"
    )
    p_rename.add_argument(
        "--template",
        required=True,
        help="New filename template (e.g., 'INVOICE_{1}.pdf' or 'DOC_{id}.pdf')"
    )
    p_rename.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Pages to scan per PDF (default: 1)"
    )
    p_rename.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (without this flag, runs in dry-run mode)"
    )

    args = parser.parse_args()

    try:
        if args.cmd == "extract":
            if not args.pdf.exists():
                logger.error(f"File not found: {args.pdf}")
                return 2
            
            txt = extract_text(args.pdf, max_pages=args.pages)
            if txt:
                print("\n" + "=" * 60)
                print(txt)
                print("=" * 60)
                return 0
            else:
                logger.warning("No text extracted")
                return 1
                
        elif args.cmd == "rename":
            if not args.folder.exists():
                logger.error(f"Folder not found: {args.folder}")
                return 2
            
            matched = rename_from_text(
                args.folder,
                args.pattern,
                args.template,
                max_pages=args.pages,
                dry_run=(not args.apply)
            )
            
            return 0 if matched > 0 else 1

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 2
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())