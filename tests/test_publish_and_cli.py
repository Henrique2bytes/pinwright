"""Report publication and the local command line."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from pinwright.audit import publish_report

ROOT = Path(__file__).resolve().parents[1]


class PublishTests(unittest.TestCase):
    def test_replace_failure_keeps_the_previous_report(self) -> None:
        path = Path(self.id().replace(".", "-") + "-unused")
        directory = Path(self._tmp())
        target = directory / "report.json"
        target.write_text("OLD\n", encoding="utf-8")

        with mock.patch("pinwright.audit.os.replace", side_effect=OSError("replace failed")):
            with self.assertRaises(OSError):
                publish_report(target, '{"ok": true}\n')
        self.assertEqual(target.read_text(encoding="utf-8"), "OLD\n")
        self.assertEqual(list(directory.glob(".pinwright-*")), [])

    def test_publish_replaces_a_complete_document(self) -> None:
        directory = Path(self._tmp())
        target = directory / "report.json"
        publish_report(target, '{"ok": true}\n')
        self.assertEqual(target.read_text(encoding="utf-8"), '{"ok": true}\n')
        self.assertEqual(list(directory.glob(".pinwright-*")), [])

    def _tmp(self) -> str:
        import tempfile

        path = tempfile.mkdtemp(prefix="pinwright-publish-")
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path


class CliTests(unittest.TestCase):
    def test_check_writes_stdout_and_atomic_out(self) -> None:
        import tempfile

        directory = Path(tempfile.mkdtemp(prefix="pinwright-cli-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        pinfile = directory / "requirements.pins"
        pinfile.write_text("requests==2.32.3\n", encoding="utf-8")
        out = directory / "out.json"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        done = subprocess.run(
            [sys.executable, "-m", "pinwright", "check", str(pinfile), "--out", str(out)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["ok"], True)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["digest"], json.loads(done.stdout)["digest"])

    def test_rejected_pinfile_exits_2(self) -> None:
        import tempfile

        directory = Path(tempfile.mkdtemp(prefix="pinwright-cli-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        pinfile = directory / "requirements.pins"
        pinfile.write_text("requests>=1\n", encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT / "src")
        done = subprocess.run(
            [sys.executable, "-m", "pinwright", "check", str(pinfile)],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(done.returncode, 2)
        self.assertEqual(json.loads(done.stdout)["ok"], False)


if __name__ == "__main__":
    unittest.main()
