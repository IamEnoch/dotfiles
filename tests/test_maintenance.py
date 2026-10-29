"""Exercise maintenance behavior without touching host packages or user data."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "system/.local/bin"


@unittest.skipIf(os.geteuid() == 0, "Maintenance scripts must run as a normal user")
class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.bin = self.home / "bin"
        self.bin.mkdir()
        self.trace = self.home / "commands.log"
        self.env = os.environ | {
            "HOME": str(self.home),
            "XDG_DATA_HOME": str(self.home / "data"),
            "XDG_CACHE_HOME": str(self.home / "cache"),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "TEST_TRACE": str(self.trace),
            "TEST_REAL_PYTHON": sys.executable,
        }
        # sudo never executes its arguments. All package managers are inert.
        stub = '''#!/usr/bin/env bash
name="${0##*/}"
printf '%s' "$name" >> "$TEST_TRACE"
printf ' %q' "$@" >> "$TEST_TRACE"
printf '\\n' >> "$TEST_TRACE"
if [[ "$name" == "python3" ]]; then
  if [[ "$*" == *"pip"*"--version"* ]]; then
    exit 0
  elif [[ "$*" == *"pip"*"list"* ]]; then
    [[ "${TEST_PIP_FAIL:-0}" == 0 ]] || exit 2
    printf '%s' "${TEST_PIP_JSON:-[]}"
    exit 0
  elif [[ "$*" == *"pip"*"install"* ]]; then
    exit 0
  fi
  exec "$TEST_REAL_PYTHON" "$@"
fi
if [[ "$name" == "brew" && "${TEST_BREW_FAIL:-0}" == 1 ]]; then
  exit 3
fi
'''
        for tool in ("sudo", "apt-get", "snap", "flatpak", "brew", "npm", "python3", "pop-upgrade"):
            target = self.bin / tool
            target.write_text(stub)
            target.chmod(0o755)
        self.trash = self.home / "data/Trash/files/keep.txt"
        self.metadata = self.home / "data/Trash/info/keep.trashinfo"
        self.thumbnail = self.home / "cache/thumbnails/test.png"
        for path in (self.trash, self.metadata, self.thumbnail):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test data")

    def run_script(self, name, *args, **env):
        return subprocess.run(
            ["bash", str(SCRIPTS / name), *args],
            env=self.env | env, text=True, capture_output=True,
        )

    def commands(self):
        return self.trace.read_text() if self.trace.exists() else ""

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dry_run_preserves_files_and_invokes_no_managers(self):
        result = self.run_script("update_system.sh", "--dry-run", "--include-pip", "--include-npm", "--release-upgrade")
        self.assert_ok(result)
        self.assertIn("brew upgrade", result.stdout)
        self.assertIn("apt-get upgrade -y", result.stdout)
        self.assertNotIn("apt-get full-upgrade", result.stdout)
        self.assertIn("Preserving Trash", result.stdout)
        # pip's local version probe is allowed; discovery/install are not.
        self.assertEqual(self.commands(), "python3 -m pip --version\n")
        for path in (self.trash, self.metadata, self.thumbnail):
            self.assertTrue(path.exists())

    def test_default_cleanup_preserves_trash(self):
        self.assert_ok(self.run_script("clean_system.sh"))
        self.assertTrue(self.trash.exists())
        self.assertTrue(self.metadata.exists())
        self.assertFalse(self.thumbnail.exists())
        self.assertIn("brew cleanup", self.commands())
        self.assertIn("sudo apt-get autoremove -y", self.commands())
        self.assertIn("journalctl --vacuum-time=7d", self.commands())

    def test_explicit_trash_cleanup_honors_xdg_paths(self):
        self.assert_ok(self.run_script("clean_system.sh", "--empty-trash", "--skip-thumbnails"))
        self.assertFalse(self.trash.exists())
        self.assertFalse(self.metadata.exists())
        self.assertTrue(self.thumbnail.exists())

    def test_dry_run_empty_trash_still_preserves_data(self):
        self.assert_ok(self.run_script("clean_system.sh", "--empty-trash", "--dry-run"))
        self.assertTrue(self.trash.exists())
        self.assertEqual(self.commands(), "")

    def test_no_clean_and_full_upgrade_are_respected(self):
        self.assert_ok(self.run_script("update_system.sh", "--no-clean", "--full-upgrade"))
        commands = self.commands()
        self.assertIn("sudo apt-get full-upgrade -y", commands)
        self.assertNotIn("autoremove", commands)
        self.assertNotIn("cleanup", commands)
        self.assertNotIn("journalctl", commands)
        self.assertTrue(self.thumbnail.exists())

    def test_skip_brew_applies_to_cleanup_too(self):
        self.assert_ok(self.run_script("update_system.sh", "--skip-brew"))
        self.assertNotIn("brew", self.commands())
        self.assertIn("autoremove", self.commands())

    def test_failed_pip_discovery_is_an_error(self):
        result = self.run_script("update_system.sh", "--include-pip", TEST_PIP_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Failed to list outdated pip packages", result.stderr)
        self.assertNotIn("up to date", result.stdout)
        self.assertNotIn("System update completed", result.stdout)
        self.assertNotIn("autoremove", self.commands())

    def test_malformed_pip_response_is_an_error(self):
        result = self.run_script("update_system.sh", "--include-pip", TEST_PIP_JSON="not json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Failed to parse", result.stderr)
        self.assertNotIn("up to date", result.stdout)

    def test_pip_and_npm_updates_are_opt_in(self):
        self.assert_ok(self.run_script("update_system.sh", "--no-clean", "--include-pip", "--include-npm", TEST_PIP_JSON='[{"name":"example-one"},{"name":"example-two"}]'))
        commands = self.commands()
        self.assertIn("python3 -m pip install --user --upgrade example-one", commands)
        self.assertIn("python3 -m pip install --user --upgrade example-two", commands)
        self.assertIn("npm update -g", commands)

    def test_manager_failure_stops_before_cleanup(self):
        result = self.run_script("update_system.sh", TEST_BREW_FAIL="1")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Update failed", result.stderr)
        self.assertNotIn("System update completed", result.stdout)
        self.assertTrue(self.thumbnail.exists())

    def test_symlinked_updater_finds_sibling_cleanup(self):
        link = self.home / "update_system.sh"
        link.symlink_to(SCRIPTS / "update_system.sh")
        result = subprocess.run([str(link), "--dry-run"], env=self.env, capture_output=True, text=True)
        self.assert_ok(result)
        self.assertIn("Starting system cleanup", result.stdout)

    def test_invalid_options_fail_before_actions(self):
        for name, args in (
            ("clean_system.sh", ["--journal-age"]),
            ("clean_system.sh", ["--journal-age", "0d"]),
            ("clean_system.sh", ["--journal-age", "garbage"]),
            ("clean_system.sh", ["--unknown"]),
            ("update_system.sh", ["--unknown"]),
        ):
            with self.subTest(name=name, args=args):
                result = self.run_script(name, *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.commands(), "")
                self.assertTrue(self.trash.exists())

    def test_all_cleanup_skips(self):
        self.assert_ok(self.run_script("clean_system.sh", "--skip-apt", "--skip-journal", "--skip-flatpak", "--skip-snap", "--skip-brew", "--skip-thumbnails"))
        self.assertEqual(self.commands(), "")
        self.assertTrue(self.thumbnail.exists())

    def test_relative_xdg_paths_fail_before_actions(self):
        result = self.run_script("clean_system.sh", "--empty-trash", XDG_DATA_HOME="relative")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("absolute paths", result.stderr)
        self.assertEqual(self.commands(), "")
        self.assertTrue(self.trash.exists())

    def test_cli_help_version_and_invalid_commands(self):
        self.assertIn("doctor", self.run_script("zotu", "--help").stdout)
        self.assertIn("zotu 0.1.0", self.run_script("zotu", "--version").stdout)
        self.assertIn("--empty-trash", self.run_script("zotu", "help", "clean").stdout)
        self.assert_ok(self.run_script("zotu", "doctor", "--help"))
        self.assertNotEqual(self.run_script("zotu", "unknown").returncode, 0)
        self.assertNotEqual(self.run_script("zotu", "status", "unexpected").returncode, 0)
        self.assertEqual(self.commands(), "")

    def test_cli_update_forwards_dry_run_and_no_clean(self):
        result = self.run_script("zotu", "update", "--dry-run", "--no-clean", "--skip-brew")
        self.assert_ok(result)
        self.assertIn("apt-get upgrade", result.stdout)
        self.assertNotIn("brew upgrade", result.stdout)
        self.assertNotIn("Starting system cleanup", result.stdout)
        self.assertEqual(self.commands(), "")
        self.assertTrue(self.thumbnail.exists())

    def test_cli_clean_forwards_explicit_trash_option(self):
        self.assert_ok(self.run_script("zotu", "clean", "--empty-trash", "--skip-thumbnails"))
        self.assertFalse(self.trash.exists())
        self.assertTrue(self.thumbnail.exists())

    def test_cli_status_reports_links_without_changing_them(self):
        shell_link = self.home / ".zshrc"
        shell_link.symlink_to(REPO / "zsh/.zshrc")
        result = self.run_script("zotu", "status")
        self.assert_ok(result)
        self.assertIn("linked", result.stdout)
        self.assertIn(str(shell_link), result.stdout)
        self.assertIn("missing", result.stdout)
        self.assertEqual(self.commands(), "")
        self.assertFalse((self.home / ".local/bin/zotu").exists())

    def test_cli_doctor_reports_missing_requirements(self):
        for tool in ("bash", "readlink", "dirname"):
            (self.bin / tool).symlink_to(shutil.which(tool))
        result = self.run_script("zotu", "doctor", PATH=str(self.bin))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MISSING stow", result.stdout)
        self.assertIn("required tool(s) missing", result.stdout)
        self.assertEqual(self.commands(), "")

    def test_cli_install_rejects_unsupported_dry_run_before_actions(self):
        result = self.run_script("zotu", "install", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dependency installation has no dry-run", result.stderr)
        self.assertEqual(self.commands(), "")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow is required")
    def test_cli_link_dry_run_does_not_create_links(self):
        self.assert_ok(self.run_script("zotu", "link", "--dry-run"))
        self.assertFalse((self.home / ".zshrc").exists())
        self.assertFalse((self.home / ".local/bin/zotu").exists())
        self.assertEqual(self.commands(), "")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow is required")
    def test_installer_stow_only(self):
        result = subprocess.run(
            ["bash", str(REPO / "install.sh"), "--stow-only"],
            env=self.env, capture_output=True, text=True,
        )
        self.assert_ok(result)
        self.assertTrue((self.home / ".local/bin/clean_system.sh").is_file())
        self.assertEqual(self.commands(), "")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow is required")
    def test_installer_conflicts_preserve_existing_files(self):
        private_file = self.home / ".zshrc"
        private_file.write_text("existing shell settings")
        result = subprocess.run(
            ["bash", str(REPO / "install.sh"), "--stow-only"],
            env=self.env, capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(private_file.read_text(), "existing shell settings")
        self.assertFalse((self.home / ".local/bin/update_system.sh").exists())
        self.assertEqual(self.commands(), "")

    @unittest.skipUnless(shutil.which("stow"), "GNU Stow is required")
    def test_stow_installs_public_packages_without_git_config(self):
        packages = ["agents", "claude", "copyq", "hokum", "nvim", "omp", "system", "wezterm", "zsh"]
        result = subprocess.run(
            ["stow", f"--dir={REPO}", f"--target={self.home}", *packages],
            capture_output=True, text=True,
        )
        self.assert_ok(result)
        self.assertTrue((self.home / ".local/bin/update_system.sh").is_file())
        self.assertTrue((self.home / ".zshrc").is_file())
        self.assertTrue((self.home / ".local/bin/cosmic-notifications").is_file())
        self.assertFalse((self.home / ".gitconfig").exists())


if __name__ == "__main__":
    unittest.main()
