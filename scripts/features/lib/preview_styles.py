#!/usr/bin/env python3
"""Per-collection and per-section preview style overrides.

The banner prompt is assembled from a global ``style`` and ``style_modifiers``
in the ``preview_images:`` block of ``_config.yml``. One site, though, is
rarely one register: this site's four post sections carry four editorial
voices, and a banner that ignores that makes every section look alike.

This module resolves the override blocks that let a collection or a section
carry its own look, most specific winning:

    global  →  collection_styles[<collection>]  →  section_styles[<section>]

A file's **collection** is the nearest ``_<name>`` ancestor directory
(``pages/_posts/erp/x.md`` → ``posts``) and its **section** is the directory
immediately inside that collection (→ ``erp``), matching Jekyll's own layout
and the resolution zer0-image-generator uses. The override keys are that
engine's five — ``style``, ``style_modifiers``, ``size``, ``quality``,
``model`` — so a block written here transfers unchanged if this site adopts
the engine, and ``collection_styles`` is spelled the way the engine spells it.
``section_styles`` is the axis the engine does not yet have.

Called by ``scripts/features/generate-preview-images`` once per file::

    python3 scripts/features/lib/preview_styles.py pages/_posts/erp/x.md

It prints one ``key<TAB>value`` line per override that applies, plus a
``_layers`` line naming the layers that contributed, and nothing at all when
nothing applies. Any failure — no PyYAML, unreadable config, malformed block —
exits 0 with no output, because a missing style override must degrade to the
global style rather than stop a generation run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]

#: The keys an override block may set, matching zer0-image-generator's
#: OVERRIDE_KEYS so blocks stay portable between the two implementations.
OVERRIDE_KEYS = ("style", "style_modifiers", "size", "quality", "model")


def collection_of(path: Path) -> str:
    """The file's collection: the nearest ``_<name>`` ancestor directory.

    ``pages/_posts/erp/x.md`` → ``posts``; a file outside any collection → ``""``.
    """
    for parent in path.resolve().parents:
        name = parent.name
        if name.startswith("_") and len(name) > 1:
            return name[1:]
    return ""


def section_of(path: Path) -> str:
    """The file's section: the directory immediately inside its collection.

    ``pages/_posts/erp/x.md`` → ``erp``; a collection holding its files flat
    → ``""``. Sites that fold several kinds of writing into one collection
    carry the editorial distinction here, which makes it the strongest single
    signal for what a banner should look like.
    """
    parts = path.resolve().parts
    for i, name in enumerate(parts):
        if name.startswith("_") and len(name) > 1:
            # parts[i + 1] is a directory only when something follows it.
            return parts[i + 1] if i + 2 < len(parts) else ""
    return ""


def filter_block(block: Any) -> dict[str, str]:
    """Keep only recognized override keys carrying a non-empty value."""
    if not isinstance(block, dict):
        return {}
    return {
        key: str(value).strip()
        for key, value in block.items()
        if key in OVERRIDE_KEYS and value is not None and str(value).strip()
    }


def load_preview_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    """The ``preview_images:`` block of ``_config.yml``, or an empty mapping."""
    try:
        import yaml  # noqa: PLC0415 - optional; absence must not be fatal
    except ImportError:
        return {}
    path = config_path or (REPO_ROOT / "_config.yml")
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, Exception):  # noqa: B014 - yaml errors vary
        return {}
    block = config.get("preview_images") if isinstance(config, dict) else None
    return block if isinstance(block, dict) else {}


def resolve(path: Path, preview_config: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    """Overrides for *path*, and the names of the layers that contributed.

    Later layers win key by key, so a section may override a single key and
    inherit the rest from its collection and from the global block.
    """
    collection = collection_of(path)
    section = section_of(path)
    layers: list[str] = []
    merged: dict[str, str] = {}

    for label, styles_key, name in (
        ("collection", "collection_styles", collection),
        ("section", "section_styles", section),
    ):
        if not name:
            continue
        styles = preview_config.get(styles_key)
        if not isinstance(styles, dict):
            continue
        block = filter_block(styles.get(name))
        if block:
            merged.update(block)
            layers.append(f"{label}:{name}")

    return merged, layers


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in {"-h", "--help"}:
        print(__doc__, file=sys.stderr)
        return 0 if args and args[0] in {"-h", "--help"} else 2

    try:
        overrides, layers = resolve(Path(args[0]), load_preview_config())
    except Exception:
        # Never break a generation run over a style lookup.
        return 0

    for key, value in overrides.items():
        # Values are single-line style strings from a trusted config file;
        # collapse any stray newline so the TAB-delimited contract holds.
        print(f"{key}\t{' '.join(value.split())}")
    if layers:
        print(f"_layers\t{', '.join(layers)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
