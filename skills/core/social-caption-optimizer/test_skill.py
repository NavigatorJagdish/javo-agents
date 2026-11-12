"""Tests for social-caption-optimizer skill."""

import unittest
from pathlib import Path
import importlib.util

SKILL_PATH = Path(__file__).resolve().parent / "skill.py"
spec = importlib.util.spec_from_file_location("social_caption_optimizer", SKILL_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class TestSocialCaptionOptimizer(unittest.TestCase):
    def test_optimizes_instagram_caption_with_deduped_hashtags(self) -> None:
        result = mod.run(
            {
                "draft_caption": "5 AI tools that save 10 hours a week!\n\n#AI #ai #Creators",
                "platform": "instagram",
                "hashtags": ["Creators", "Productivity", "JavoAgents"],
            }
        )
        self.assertTrue(result["within_limit"])
        self.assertEqual(result["hashtags"], ["#Creators", "#Productivity", "#JavoAgents", "#AI"])
        self.assertIn("Save this for later", result["optimized_caption"])
        self.assertGreaterEqual(result["score"], 85)

    def test_respects_twitter_character_limit(self) -> None:
        long_text = "A" * 400
        result = mod.run({"draft_caption": long_text, "platform": "twitter"})
        self.assertLessEqual(result["character_count"], 280)
        self.assertTrue(result["within_limit"])

    def test_rejects_empty_caption(self) -> None:
        with self.assertRaises(ValueError):
            mod.run({"draft_caption": "   ", "platform": "youtube"})


if __name__ == "__main__":
    unittest.main()
