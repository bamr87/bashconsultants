"""Media — reusing the image a page already has, or asking for one.

zer0-image-generator already solves social imagery for these sites: a three-stage
pipeline (Claude writes an art brief, an image model renders it, Claude reviews
the render) that writes a preview image per page and wires it into frontmatter.
A LinkedIn share wants exactly that image, so distribution should not generate
anything — it should find what the site already produced and reuse it.

This module therefore does the small, boring part: resolve the preview image for
a piece of content, and when there is none, emit the request the generator takes
as input. Rendering stays in the generator, where the provider matrix, the review
stage, and the credential chain already live. Duplicating any of that here would
mean two definitions of what a preview image is.

Resolution order, most explicit first:

1. `preview:` in the page's own frontmatter — the generator writes this, so it is
   the authoritative answer whenever the pipeline has run.
2. The conventional path, `assets/images/previews/<slug>.png`.
3. Nothing, plus a brief the generator can act on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from contract import ContentRecord

PREVIEW_DIR = Path("assets/images/previews")
PREVIEW_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")

# LinkedIn renders a link card at roughly 1.91:1. The generator's default output
# already matches; this is here so a mismatch is reported rather than discovered
# after publishing.
CARD_RATIO = 1.91
RATIO_TOLERANCE = 0.25


@dataclass
class Media:
    path: Path | None = None
    source: str = "none"      # frontmatter | convention | none
    bytes: int = 0
    brief: str = ""           # populated only when there is no image

    @property
    def found(self) -> bool:
        return self.path is not None

    def describe(self) -> str:
        if not self.found:
            return f"no preview image — {self.brief}"
        return f"{self.path} ({self.bytes:,} bytes, via {self.source})"


def _frontmatter_preview(root: Path, content_path: str) -> Path | None:
    """Read `preview:` out of the page's frontmatter without a YAML parser —
    it is a single scalar, and this module should not add a dependency for it."""
    page = root / content_path
    if not page.exists():
        return None
    try:
        text = page.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    match = re.search(r"^preview:\s*(.+)$", parts[1], re.M)
    if not match:
        return None
    value = match.group(1).strip().strip("\"'")
    if not value:
        return None
    candidate = root / value.lstrip("/")
    return candidate if candidate.exists() else None


def _conventional(root: Path, slug: str) -> Path | None:
    for ext in PREVIEW_EXTS:
        candidate = root / PREVIEW_DIR / f"{slug}{ext}"
        if candidate.exists():
            return candidate
    return None


def brief_for(record: ContentRecord) -> str:
    """The request zer0-image-generator's analyze stage takes.

    Its own Claude stage writes the actual art direction from the article; this
    only has to say which article and what shape. Inventing visual direction
    here would compete with the stage that does it properly.
    """
    return (
        f"generate a preview image for {record.path} "
        f"(title: {record.title or record.slug}); "
        f"run: jekyll preview-images --only {record.slug}"
    )


def resolve(root: Path, record: ContentRecord) -> Media:
    """Find the image this content should share with, or describe how to get it."""
    found = _frontmatter_preview(root, record.path)
    source = "frontmatter"
    if found is None:
        found = _conventional(root, record.slug)
        source = "convention"
    if found is None:
        return Media(brief=brief_for(record))
    try:
        size = found.stat().st_size
    except OSError:
        size = 0
    try:
        shown = found.relative_to(root)
    except ValueError:
        shown = found
    return Media(path=shown, source=source, bytes=size)
