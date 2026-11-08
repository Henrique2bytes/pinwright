"""The candidate's own checks pass. The maintainer contract does not."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

from pinwright.audit import audit_text, publish_report

ROOT = Path(__file__).resolve().parents[1]
SHA = "0123456789abcdef01230123456789abcdef0123"


def load_candidate():
    path = ROOT / "demos" / "task-001-markers" / "ai_submission" / "marker_check.py"
    spec = importlib.util.spec_from_file_location("ai_marker_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("candidate module is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CandidateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ai = load_candidate()

    def test_candidate_self_check_accepts_a_simple_pin(self) -> None:
        result = self.ai.audit("requests==2.32.3\n")
        self.assertTrue(result["ok"])
        self.assertEqual(result["pins"][0]["pin"], "2.32.3")

    def test_comment_changes_candidate_digest_only(self) -> None:
        plain = "requests==2.32.3\n"
        commented = "requests==2.32.3\n# note\n"
        self.assertNotEqual(self.ai.audit(plain)["digest"], self.ai.audit(commented)["digest"])
        self.assertEqual(audit_text(plain).digest, audit_text(commented).digest)

    def test_candidate_accepts_defects_the_reference_rejects(self) -> None:
        samples = [
            f"tool @ git+https://example.com/org/tool.git@main\n",
            f"tool @ git+https://user:token@example.com/org/tool.git@{SHA}\n",
            "Requests==1.0.0\nrequests==1.2.0\n",
            "requests==2.32.3 ; python_version >= '3.11' or sys_platform == 'linux'\n",
            "requests==latest\n",
        ]
        for text in samples:
            with self.subTest(text=text):
                self.assertTrue(self.ai.audit(text)["ok"])
                self.assertFalse(audit_text(text).ok)

    def test_extra_order_changes_candidate_identity_only(self) -> None:
        left = self.ai.audit("pkg[b,a]==1.0.0\n")
        right = self.ai.audit("pkg[a,b]==1.0.0\n")
        self.assertNotEqual(left["digest"], right["digest"])
        self.assertNotEqual(left["pins"][0]["name"], right["pins"][0]["name"])
        self.assertEqual(audit_text("pkg[b,a]==1.0.0\n").digest, audit_text("pkg[a,b]==1.0.0\n").digest)

    def test_candidate_report_truncates_when_the_write_fails(self) -> None:
        import tempfile

        directory = Path(tempfile.mkdtemp(prefix="pinwright-ai-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        target = directory / "report.json"
        target.write_text("OLD\n", encoding="utf-8")
        real = Path.write_text

        def truncated(self, data, encoding=None, errors=None, newline=None):
            del data, errors, newline
            real(self, "", encoding=encoding)
            raise OSError("full")

        with mock.patch.object(Path, "write_text", truncated):
            with self.assertRaises(OSError):
                self.ai.write_report(target, '{"ok": true}\n')
        self.assertEqual(target.read_text(encoding="utf-8"), "")

        restored = directory / "reference.json"
        restored.write_text("OLD\n", encoding="utf-8")
        with mock.patch("pinwright.audit.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                publish_report(restored, '{"ok": true}\n')
        self.assertEqual(restored.read_text(encoding="utf-8"), "OLD\n")


if __name__ == "__main__":
    unittest.main()
