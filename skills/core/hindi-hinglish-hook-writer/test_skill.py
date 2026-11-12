"""Tests for hindi-hinglish-hook-writer skill."""

import importlib.util
import unittest
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent / "skill.py"
spec = importlib.util.spec_from_file_location("hindi_hinglish_hook_writer", SKILL_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class TestHindiHinglishHookWriter(unittest.TestCase):
    def test_generates_hinglish_hooks(self) -> None:
        res = mod.run({"topic": "YouTube Shorts viral growth", "language": "hinglish", "count": 4})
        self.assertEqual(res["language"], "hinglish")
        self.assertEqual(len(res["hooks"]), 4)
        self.assertTrue(all("YouTube Shorts viral growth" in h["text"] for h in res["hooks"]))

    def test_generates_devanagari_hindi_hooks(self) -> None:
        res = mod.run({"topic": "AI वीडियो एडिटिंग", "language": "hindi", "count": 3})
        self.assertEqual(res["language"], "hindi")
        self.assertEqual(len(res["hooks"]), 3)
        self.assertTrue(any("AI वीडियो एडिटिंग" in h["text"] for h in res["hooks"]))

    def test_rejects_blank_topic(self) -> None:
        with self.assertRaises(ValueError):
            mod.run({"topic": ""})


if __name__ == "__main__":
    unittest.main()
