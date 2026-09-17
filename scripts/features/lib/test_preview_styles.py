"""Tests for the per-collection and per-section preview style resolver.

Standard library only, no network, no config file of the repo's own. Run from
the repo root::

    python3 -m unittest scripts/features/lib/test_preview_styles.py

What matters here is the resolution order — global, then the collection block,
then the section block, most specific winning key by key — and that a lookup
which cannot answer degrades to no overrides rather than raising into a
generation run.
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import preview_styles as ps  # noqa: E402


class TestPathResolution(unittest.TestCase):
    def test_collection_is_the_nearest_underscore_directory(self) -> None:
        self.assertEqual(ps.collection_of(Path("pages/_posts/erp/x.md")), "posts")
        self.assertEqual(ps.collection_of(Path("pages/_toolkit/x.md")), "toolkit")

    def test_section_is_the_directory_inside_the_collection(self) -> None:
        self.assertEqual(ps.section_of(Path("pages/_posts/erp/x.md")), "erp")
        self.assertEqual(ps.section_of(Path("pages/_posts/tech/2026-01-01-a.md")), "tech")

    def test_a_file_flat_in_its_collection_has_no_section(self) -> None:
        self.assertEqual(ps.section_of(Path("pages/_posts/index.md")), "")
        self.assertEqual(ps.section_of(Path("pages/_toolkit/x.md")), "")

    def test_a_file_outside_any_collection_has_neither(self) -> None:
        self.assertEqual(ps.collection_of(Path("about.md")), "")
        self.assertEqual(ps.section_of(Path("about.md")), "")


class TestFilterBlock(unittest.TestCase):
    def test_keeps_only_recognized_keys(self) -> None:
        block = ps.filter_block({"style": "a", "provider": "openai", "size": "1x1"})
        self.assertEqual(block, {"style": "a", "size": "1x1"})

    def test_drops_empty_and_none_values(self) -> None:
        self.assertEqual(ps.filter_block({"style": "  ", "quality": None, "model": "m"}), {"model": "m"})

    def test_a_non_mapping_is_no_block(self) -> None:
        for value in ("a string", ["a", "list"], None, 7):
            with self.subTest(value=value):
                self.assertEqual(ps.filter_block(value), {})

    def test_values_are_stringified_and_trimmed(self) -> None:
        self.assertEqual(ps.filter_block({"quality": "  high  "}), {"quality": "high"})


class TestResolve(unittest.TestCase):
    POST = Path("pages/_posts/erp/2026-01-01-a-post.md")

    def test_no_style_blocks_means_no_overrides(self) -> None:
        self.assertEqual(ps.resolve(self.POST, {}), ({}, []))
        self.assertEqual(ps.resolve(self.POST, {"style": "global only"}), ({}, []))

    def test_collection_block_applies(self) -> None:
        overrides, layers = ps.resolve(self.POST, {"collection_styles": {"posts": {"style": "coll"}}})
        self.assertEqual(overrides, {"style": "coll"})
        self.assertEqual(layers, ["collection:posts"])

    def test_section_block_applies(self) -> None:
        overrides, layers = ps.resolve(self.POST, {"section_styles": {"erp": {"style_modifiers": "sec"}}})
        self.assertEqual(overrides, {"style_modifiers": "sec"})
        self.assertEqual(layers, ["section:erp"])

    def test_section_wins_over_collection_key_by_key(self) -> None:
        """A section overriding one key must inherit the collection's others."""
        overrides, layers = ps.resolve(
            self.POST,
            {
                "collection_styles": {"posts": {"style": "coll", "quality": "high"}},
                "section_styles": {"erp": {"style": "sec"}},
            },
        )
        self.assertEqual(overrides, {"style": "sec", "quality": "high"})
        self.assertEqual(layers, ["collection:posts", "section:erp"])

    def test_a_block_for_another_section_is_ignored(self) -> None:
        self.assertEqual(ps.resolve(self.POST, {"section_styles": {"tech": {"style": "x"}}}), ({}, []))

    def test_a_flat_file_gets_the_collection_but_no_section(self) -> None:
        overrides, layers = ps.resolve(
            Path("pages/_posts/index.md"),
            {
                "collection_styles": {"posts": {"style": "coll"}},
                "section_styles": {"erp": {"style": "sec"}},
            },
        )
        self.assertEqual(overrides, {"style": "coll"})
        self.assertEqual(layers, ["collection:posts"])

    def test_malformed_style_maps_are_ignored(self) -> None:
        for block in ("not a map", ["nope"], None):
            with self.subTest(block=block):
                self.assertEqual(ps.resolve(self.POST, {"section_styles": block}), ({}, []))


class TestConfigLoading(unittest.TestCase):
    def _config(self, text: str) -> Path:
        tmp = Path(self._dir.name) / "_config.yml"
        tmp.write_text(text, encoding="utf-8")
        return tmp

    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self._dir.cleanup()

    def test_reads_the_preview_images_block(self) -> None:
        path = self._config("preview_images:\n  style: 'base'\n  section_styles:\n    erp:\n      style: 'e'\n")
        block = ps.load_preview_config(path)
        self.assertEqual(block["style"], "base")
        self.assertEqual(block["section_styles"]["erp"]["style"], "e")

    def test_a_missing_file_is_an_empty_block(self) -> None:
        self.assertEqual(ps.load_preview_config(Path(self._dir.name) / "nope.yml"), {})

    def test_malformed_yaml_is_an_empty_block(self) -> None:
        self.assertEqual(ps.load_preview_config(self._config("preview_images: [unclosed\n")), {})

    def test_a_config_without_the_block_is_empty(self) -> None:
        self.assertEqual(ps.load_preview_config(self._config("title: Site\n")), {})


class TestCli(unittest.TestCase):
    POST = "pages/_posts/erp/2026-01-01-a-post.md"

    def _run(self, argv: list[str], config: dict) -> tuple[int, str]:
        with mock.patch.object(ps, "load_preview_config", return_value=config), mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out:
            code = ps.main(argv)
        return code, out.getvalue()

    def test_prints_tab_separated_overrides_and_the_layers(self) -> None:
        code, out = self._run([self.POST], {"section_styles": {"erp": {"style": "sec"}}})
        self.assertEqual(code, 0)
        self.assertIn("style\tsec", out)
        self.assertIn("_layers\tsection:erp", out)

    def test_prints_nothing_when_no_override_applies(self) -> None:
        code, out = self._run([self.POST], {})
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_multi_line_values_collapse_to_one_line(self) -> None:
        """The contract is one override per line; a folded YAML scalar must not break it."""
        code, out = self._run([self.POST], {"section_styles": {"erp": {"style": "a\nb   c"}}})
        self.assertEqual(code, 0)
        self.assertIn("style\ta b c", out)
        self.assertEqual(len([ln for ln in out.splitlines() if ln]), 2)

    def test_a_lookup_failure_is_silent_and_successful(self) -> None:
        """A style lookup must never stop a generation run."""
        with mock.patch.object(ps, "load_preview_config", side_effect=RuntimeError("boom")), mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out:
            self.assertEqual(ps.main([self.POST]), 0)
        self.assertEqual(out.getvalue(), "")

    def test_wrong_argument_count_is_a_usage_error(self) -> None:
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(ps.main([]), 2)
            self.assertEqual(ps.main(["a", "b"]), 2)


class TestRepoConfig(unittest.TestCase):
    """The committed _config.yml must keep the house rule and stay parseable."""

    def setUp(self) -> None:
        self.block = ps.load_preview_config()
        if not self.block:
            self.skipTest("no preview_images block available")

    def test_every_section_block_is_valid(self) -> None:
        for name, block in (self.block.get("section_styles") or {}).items():
            with self.subTest(section=name):
                self.assertTrue(ps.filter_block(block), f"section '{name}' sets no recognized key")

    @staticmethod
    def _says_pixel_art(style: str) -> bool:
        """Both spellings are correct English; the config uses whichever reads better."""
        return "pixel art" in style.lower().replace("pixel-art", "pixel art")

    def test_the_global_style_is_pixel_art(self) -> None:
        """The base every unsectioned page inherits, and the site's medium."""
        self.assertTrue(self._says_pixel_art(str(self.block.get("style", ""))))

    def test_every_section_stays_pixel_art(self) -> None:
        """House rule: a section may change the genre, never the medium.

        Sections carry their editorial voice by naming their own pixel-art
        tradition — strategy sim, adventure game, atmospheric landscape,
        schematic. What holds the site together is that all of them are still
        pixel art, so that is what is asserted rather than which keys a block
        is allowed to set.
        """
        for name, block in (self.block.get("section_styles") or {}).items():
            with self.subTest(section=name):
                style = ps.filter_block(block).get("style")
                if style is None:
                    continue  # inherits the global pixel-art base
                self.assertTrue(
                    self._says_pixel_art(style),
                    f"section '{name}' sets a style that is not pixel art",
                )


if __name__ == "__main__":
    unittest.main()
