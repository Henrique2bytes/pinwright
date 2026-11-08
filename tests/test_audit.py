"""Reference audit: pins, markers, duplicates, and a stable digest."""

from __future__ import annotations

import unittest

from pinwright.audit import audit_text
from pinwright.markers import marker_holds

SHA = "0123456789abcdef01230123456789abcdef0123"


class AuditTests(unittest.TestCase):
    def test_exact_pin_and_comment_do_not_change_digest(self) -> None:
        first = audit_text("requests==2.32.3\n")
        second = audit_text("\n# note\nrequests==2.32.3  # inline\n\n")
        self.assertTrue(first.ok)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.pins[0].name, "requests")
        self.assertEqual(first.pins[0].version, "2.32.3")

    def test_names_and_extras_are_canonical(self) -> None:
        audit = audit_text("Requests[Security,socks]==2.32.3\n")
        self.assertTrue(audit.ok)
        self.assertEqual(audit.pins[0].name, "requests")
        self.assertEqual(audit.pins[0].extras, ("security", "socks"))
        swapped = audit_text("requests[socks,security]==2.32.3\n")
        self.assertEqual(audit.digest, swapped.digest)

    def test_pep503_duplicates_are_rejected(self) -> None:
        audit = audit_text("Foo_Bar==1.0.0\nfoo-bar==1.2.0\n")
        self.assertFalse(audit.ok)
        self.assertEqual(audit.digest, None)
        self.assertEqual(audit.findings[0].code, "duplicate-name")
        self.assertEqual(audit.findings[0].line, 2)

    def test_git_commit_is_canonical_and_host_is_lowered(self) -> None:
        audit = audit_text(f"Tool @ git+https://Example.COM/Org/Tool.git@{SHA}\n")
        self.assertTrue(audit.ok)
        self.assertEqual(audit.pins[0].git, f"git+https://example.com/Org/Tool.git@{SHA}")
        self.assertIsNone(audit.pins[0].version)

    def test_marker_is_normalized_and_evaluated_without_exec(self) -> None:
        audit = audit_text(
            "flask==3.0.3 ; sys_platform == 'linux' and python_version >= \"3.11\"\n"
        )
        self.assertTrue(audit.ok)
        marker = audit.pins[0].marker
        self.assertEqual(marker, 'sys_platform == "linux" and python_version >= "3.11"')
        self.assertTrue(marker_holds(marker, {"sys_platform": "linux", "python_version": "3.13"}))
        self.assertFalse(marker_holds(marker, {"sys_platform": "darwin", "python_version": "3.13"}))

    def test_rejects_unpinned_mutable_git_credentials_and_disallowed_marker(self) -> None:
        cases = {
            "requests>=2.32.3\n": "unpinned",
            "requests\n": "unpinned",
            "requests==latest\n": "invalid-version",
            "pkg[]==1.0.0\n": "invalid-extra",
            "pkg[a,a]==1.0.0\n": "invalid-extra",
            f"tool @ git+https://example.com/org/tool.git@main\n": "mutable-vcs",
            f"tool @ git+https://user:token@example.com/org/tool.git@{SHA}\n": "mutable-vcs",
            "requests==2.32.3 ; python_version >= '3.11' or sys_platform == 'linux'\n": "invalid-marker",
            "requests==2.32.3 ;\n": "invalid-marker",
            "requests==2.32.3 --hash=sha256:abcd\n": "invalid-requirement",
        }
        for text, code in cases.items():
            with self.subTest(text=text):
                audit = audit_text(text)
                self.assertFalse(audit.ok)
                self.assertIn(code, [finding.code for finding in audit.findings])
                self.assertIsNone(audit.digest)


if __name__ == "__main__":
    unittest.main()
