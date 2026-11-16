"""Tests of immutable MiCall baseline with assembler-only exceptions."""
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from scripts.check_frozen_micall import allowed_path, violations


class FrozenMiCallPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_cwd = os.getcwd()
        self.addCleanup(os.chdir, self.old_cwd)
        os.chdir(self.temp.name)
        self.run_git("init", "-q")
        self.run_git("config", "user.email", "ci@example.invalid")
        self.run_git("config", "user.name", "Freeze Test")
        self.write("micall/drivers/sample.py", "baseline source")
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "baseline")
        self.run_git("tag", "-a", "baseline", "-m", "immutable baseline")

    def run_git(self, *args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    def write(self, filename, content):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self, filename, content):
        self.write(filename, content)
        self.run_git("add", "-A")
        self.run_git("commit", "-qm", "candidate change")

    def test_assembler_integration_paths_are_permitted(self):
        for name in ("micall/core/assembler_new.py",
                     "micall/core/assembler_commands.py",
                     "micall/core/assembler_dispatch.py",
                     "micall/tests/test_assembler_new.py",
                     "Dockerfile.assembler-new",
                     "assembler-bench/provenance.json",
                     "docs/assemblers/new/README.md"):
            with self.subTest(name=name):
                self.assertTrue(allowed_path(name))

    def test_non_assembler_changes_are_frozen(self):
        for name in ("micall/core/denovo.py",
                     "micall/core/remap.py",
                     "micall/utils/stitched_read_counts.py",
                     "micall/drivers/sample.py",
                     "micall/tests/test_stitched_read_counts.py",
                     "micall/core/plot_contigs.py",
                     "pyproject.toml", "uv.lock",
                     ".github/workflows/micall-freeze.yml",
                     "scripts/check_frozen_micall.py",
                     "docs/bench/experiments.md",
                     "micall/core/assembler_new.py/evil",
                     "micall/core/assembler_../sample.py"):
            with self.subTest(name=name):
                self.assertFalse(allowed_path(name))

    def test_assembler_only_addition_retains_frozen_core(self):
        self.commit("micall/core/assembler_new.py", "new tool integration")
        self.assertEqual(violations("refs/tags/baseline"), [])

    def test_modifying_micall_driver_fails_after_freeze(self):
        self.commit("micall/drivers/sample.py", "revised MiCall stage")
        self.assertEqual(violations("refs/tags/baseline"),
                         ["micall/drivers/sample.py"])

    def test_modifying_ci_to_bypass_freeze_is_detected(self):
        self.commit(".github/workflows/micall-freeze.yml", "bypass")
        self.assertEqual(violations("refs/tags/baseline"),
                         [".github/workflows/micall-freeze.yml"])

    def test_untrusted_missing_baseline_tag_fails_closed(self):
        with self.assertRaises(subprocess.CalledProcessError):
            violations("refs/tags/unknown-baseline")

    def test_unrelated_history_cannot_substitute_frozen_baseline(self):
        self.run_git("checkout", "--orphan", "unrelated")
        self.run_git("rm", "-rfq", ".")
        self.commit("micall/core/assembler_new.py", "standalone tool")
        with self.assertRaises(subprocess.CalledProcessError):
            violations("refs/tags/baseline")


if __name__ == "__main__":
    unittest.main()
