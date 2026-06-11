"""Render PDF pages to PNG for frontend overlay display."""

from pathlib import Path


def render_pdf_pages(pdf_path: str, output_dir: str) -> list[str]:
    """Render each PDF page to PNG. Returns list of absolute file paths."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        paths: list[str] = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x for readability
            png_path = out / f"{i + 1}.png"
            pix.save(str(png_path))
            paths.append(str(png_path))
        doc.close()
        return paths
    except ImportError:
        # Fallback: no page images without PyMuPDF
        return []
