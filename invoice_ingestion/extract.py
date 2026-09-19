from __future__ import annotations

import hashlib
import json
from pathlib import Path

INGESTION_DIR = Path(__file__).resolve().parent.parent / "data" / "ingestion"


class DocumentExtractionError(Exception):
    """Unreadable document or unsupported file type."""


class UnsupportedFileType(DocumentExtractionError):
    pass


class UnreadableDocument(DocumentExtractionError):
    pass


def resolve_ingestion_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return INGESTION_DIR / candidate


def document_hash(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.strip().splitlines())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def page_refs_from_text(text: str) -> list[str]:
    refs: list[str] = []
    for line in text.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("--- page ") and stripped.endswith("---"):
            refs.append(stripped.strip("- ").strip())
    if not refs:
        refs.append("page 1")
    return refs


def extract_text(path: str | Path) -> str:
    """Replaceable document-text layer. PDFs/images use a sidecar .txt for the demo."""
    target = resolve_ingestion_path(path)
    suffix = target.suffix.lower()
    supported_text = {".txt", ".md", ".csv", ".json", ".xml", ".edi"}
    sidecar_types = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

    if suffix in sidecar_types:
        sidecar = target.with_suffix(".txt")
        if sidecar.exists():
            return sidecar.read_text()
        raise UnreadableDocument(
            f"No text extraction sidecar for {target.name}. "
            "Replace extract_text() with a real OCR/PDF adapter."
        )
    if suffix not in supported_text and suffix:
        raise UnsupportedFileType(f"Unsupported file type: {target.name}")
    if not target.exists():
        raise UnreadableDocument(f"Document not found: {target}")
    try:
        return target.read_text()
    except OSError as exc:
        raise UnreadableDocument(f"Could not read {target.name}: {exc}") from exc


def extract_json(path: str | Path):
    raw = extract_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UnreadableDocument(f"Invalid JSON in {path}: {exc.msg}") from exc
