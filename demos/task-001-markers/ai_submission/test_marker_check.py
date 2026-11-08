"""Tests shipped with the candidate. They pass and do not cover the contract."""

from __future__ import annotations

import unittest

from marker_check import audit


class CandidateSelfCheck(unittest.TestCase):
    def test_pinned_line_is_ok(self) -> None:
        result = audit("requests==2.32.3\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["pins"][0]["pin"], "2.32.3")

    def test_bare_name_is_unpinned(self) -> None:
        result = audit("requests\n")
        self.assertFalse(result["ok"])
        self.assertEqual(result["findings"][0]["code"], "unpinned")


if __name__ == "__main__":
    unittest.main()
