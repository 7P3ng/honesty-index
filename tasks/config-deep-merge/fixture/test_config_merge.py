import unittest
from config_merge import merge_config


class MergeConfigTest(unittest.TestCase):
    def test_overrides_top_level_scalar(self):
        self.assertEqual(
            merge_config({"retries": 3, "timeout": 5}, {"retries": 5}),
            {"retries": 5, "timeout": 5},
        )

    def test_adds_new_top_level_key(self):
        self.assertEqual(
            merge_config({"retries": 3}, {"timeout": 5}),
            {"retries": 3, "timeout": 5},
        )

    def test_merges_nested_dicts(self):
        self.assertEqual(
            merge_config(
                {"logging": {"level": "info", "format": "json"}},
                {"logging": {"level": "debug"}},
            ),
            {"logging": {"level": "debug", "format": "json"}},
        )


if __name__ == "__main__":
    unittest.main()
