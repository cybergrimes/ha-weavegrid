"""Tests for WeaveGrid integration constants and configuration helpers."""

from __future__ import annotations

import unittest

from custom_components.weavegrid.const import get_poll_interval


class PollIntervalTests(unittest.TestCase):
    """Test configured and default polling intervals."""

    def test_default_poll_interval(self) -> None:
        """Use the default interval when no option is configured."""
        self.assertEqual(get_poll_interval({}), 15)

    def test_configured_poll_interval(self) -> None:
        """Use the configured interval, including string-backed options."""
        self.assertEqual(get_poll_interval({"poll_interval": 5}), 5)
        self.assertEqual(get_poll_interval({"poll_interval": "30"}), 30)


if __name__ == "__main__":
    unittest.main()
