"""Independent process and filesystem checks for the embedded Lite profile."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_durable_client import RunningApp
from test_records import manifest


ROOT = Path(__file__).resolve().parent.parent
SDK = Path(os.environ.get("NIL_SDK", ROOT / ".sdk"))
ROUTES = tuple(os.environ.get("ENIGMA_TEST_TARGETS", "vm,native").split(","))
ENABLED = os.environ.get("ENIGMA_LITE_TESTS") == "1"
BODY_LIMIT = 65536


@unittest.skipUnless(ENABLED, "run scripts/test-lite.sh to build Enigma Lite")
class LiteTests(unittest.TestCase):
    def command(self, route: str, mode: str, directory: Path) -> list[str]:
        if mode in {"create", "reopen"}:
            artifact = ROOT / "build/lite-example/enigma-lite-example"
        else:
            artifact = ROOT / "build/lite-probe/enigma-lite-probe"
        executable = (
            [str(SDK / "nilinterpreter"), str(artifact.with_suffix(".nil"))]
            if route == "vm"
            else [str(artifact)]
        )
        return [*executable, mode, str(directory)]

    def run_example(self, route: str, mode: str, directory: Path, expected: str) -> None:
        completed = subprocess.run(
            self.command(route, mode, directory), capture_output=True, check=False, timeout=30
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, (expected + "\n").encode("utf-8"))

    def seed_bodies(self, route: str, directory: Path, bodies: dict[str, bytes]) -> bytes:
        """Encode a valid record store independently of Lite's put checks."""
        self.run_example(route, "empty", directory, "created")
        _, state, rows = manifest(directory)
        self.assertFalse(rows)
        entries = []
        for version, (key, body) in enumerate(sorted(bodies.items()), start=1):
            body_id = f"{version:032x}"
            path = directory / "objects" / body_id
            path.touch(mode=0o600, exist_ok=False)
            path.write_bytes(body)
            entries.append([key, version, len(body), body_id, hashlib.sha256(body).hexdigest()])
        state["index"] = [entries[index:index + 32] for index in range(0, len(entries), 32)]
        state["generation"] += len(entries)
        state["sequence"] = len(entries)
        state["live_bytes"] = sum(map(len, bodies.values()))
        payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
        envelope = {
            "format": "enigma.checkpoint.v1",
            "payload": payload,
            "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        }
        encoded = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
        (directory / "manifest.json").write_bytes(encoded)
        return encoded

    def test_text_settings_survive_restart_and_keep_record_compatibility(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-") as temporary:
                path = Path(temporary) / "settings"
                self.run_example(route, "create", path, "lite create ok")
                _, before, rows = manifest(path)
                self.assertEqual(before["scope"], "enigma.lite.v1")
                self.assertEqual(before["sequence"], 2)
                self.assertEqual(rows["ui/theme"][2].read_bytes(), "night Ω雪".encode("utf-8"))
                self.assertEqual(rows["ui/label"][:2], (2, 0))

                self.run_example(route, "reopen", path, "lite reopen ok")
                _, after, rows = manifest(path)
                self.assertEqual(after["database_id"], before["database_id"])
                self.assertNotEqual(after["incarnation"], before["incarnation"])
                self.assertEqual(after["authority"]["retired_through"], before["authority"]["next_grant_id"] - 1)
                self.assertGreater(after["authority"]["clock_floor"], before["authority"]["clock_floor"])
                self.assertEqual(after["sequence"], 3)
                self.assertEqual(rows["ui/theme"][0], 3)
                self.assertEqual(rows["ui/theme"][2].read_bytes(), "dawn é".encode("utf-8"))
                self.assertEqual(rows["ui/label"][:2], (2, 0))
                self.assertEqual(len(list((path / "objects").iterdir())), 3)

                self.run_example(route, "open-full", path, "ready")
                _, full, full_rows = manifest(path)
                self.assertEqual(full["database_id"], before["database_id"])
                self.assertEqual(full["sequence"], 3)
                self.assertEqual(full_rows, rows)

    def test_lite_write_limits_refuse_without_publishing_a_body(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-limits-") as temporary:
                keys = Path(temporary) / "keys"
                self.run_example(route, "key-limit", keys, "lite key limit ok")
                _, state, rows = manifest(keys)
                self.assertEqual(len(rows), 16)
                self.assertEqual(state["sequence"], 17)
                self.assertEqual(rows["slot:0"][2].read_bytes(), b"kept")
                self.assertEqual(len(list((keys / "objects").iterdir())), 17)

                bodies = Path(temporary) / "bodies"
                self.seed_bodies(route, bodies, {f"block:{index}": b"x" * BODY_LIMIT for index in range(4)})
                self.run_example(route, "body-limits", bodies, "lite body limits ok")
                _, state, rows = manifest(bodies)
                self.assertEqual(len(rows), 4)
                self.assertEqual(state["sequence"], 5)
                self.assertEqual(state["live_bytes"], 4 * BODY_LIMIT)
                self.assertEqual(rows["block:0"][:2], (5, BODY_LIMIT))
                self.assertEqual(rows["block:0"][2].read_bytes(), b"u" * BODY_LIMIT)
                self.assertEqual(len(list((bodies / "objects").iterdir())), 5)

    def test_over_limit_record_stores_fail_lite_open_before_recovery(self) -> None:
        cases = {
            "keys": {f"slot:{index}": b"" for index in range(17)},
            "body": {"setting": b"v" * (BODY_LIMIT + 1)},
            "aggregate": {f"block:{index}": b"x" * BODY_LIMIT for index in range(5)},
        }
        for route in ROUTES:
            for case, bodies in cases.items():
                with self.subTest(route=route, case=case), tempfile.TemporaryDirectory(
                    prefix="enigma-lite-over-limit-"
                ) as temporary:
                    path = Path(temporary) / "settings"
                    original = self.seed_bodies(route, path, bodies)
                    self.run_example(route, "open-code", path, "limit")
                    self.assertEqual((path / "manifest.json").read_bytes(), original)
                    self.run_example(route, "open-full", path, "ready")

    def test_foreign_missing_and_corrupt_stores_are_not_recovered_as_lite(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-fail-") as temporary:
                root = Path(temporary)
                foreign = root / "foreign"
                self.run_example(route, "foreign", foreign, "created")
                original, _, _ = manifest(foreign)
                self.run_example(route, "open-code", foreign, "scope_mismatch")
                self.assertEqual((foreign / "manifest.json").read_bytes(), original)

                absent = root / "absent"
                self.run_example(route, "open-code", absent, "unsafe_directory")
                self.assertFalse(absent.exists())

                damaged = root / "damaged"
                self.run_example(route, "create", damaged, "lite create ok")
                original, _, rows = manifest(damaged)
                rows["ui/theme"][2].unlink()
                self.run_example(route, "open-code", damaged, "corrupt")
                canonical = damaged / "manifest.json"
                self.assertEqual(canonical.read_bytes(), original)
                bad_manifest = b'{"not":"an Enigma manifest"}'
                canonical.write_bytes(bad_manifest)
                self.run_example(route, "open-code", damaged, "corrupt")
                self.assertEqual(canonical.read_bytes(), bad_manifest)


    def test_reads_within_one_session_leave_the_manifest_in_place(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-read-") as temporary:
                path = Path(temporary) / "settings"
                self.run_example(route, "create", path, "lite create ok")
                with RunningApp(self.command(route, "reads", path)) as process:
                    self.assertEqual(process.line(), "lite read ready")
                    original, state, rows = manifest(path)
                    canonical = path / "manifest.json"
                    original_file = canonical.stat()
                    self.assertEqual(state["sequence"], 2)
                    self.assertEqual(len(rows), 2)
                    process.send("read")
                    self.assertEqual(process.line(), "lite reads complete")
                    current = canonical.stat()
                    self.assertEqual(current.st_ino, original_file.st_ino)
                    self.assertEqual(current.st_mtime_ns, original_file.st_mtime_ns)
                    self.assertEqual(canonical.read_bytes(), original)
                    process.send("close")
                    process.finish()

    def test_nul_in_an_ordinary_record_is_refused_as_lite_text(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-nul-") as temporary:
                path = Path(temporary) / "settings"
                self.seed_bodies(route, path, {"setting": b"raw\x00body", "ui/theme": b"plain"})
                self.run_example(route, "nul", path, "lite refused nontext")
                _, state, rows = manifest(path)
                self.assertEqual(state["sequence"], 2)
                self.assertEqual(rows["setting"][2].read_bytes(), b"raw\x00body")

    def test_uncertain_publication_disables_the_lite_owner(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-lite-fault-") as temporary:
                path = Path(temporary) / "settings"
                self.run_example(route, "create", path, "lite create ok")
                canonical = path / "manifest.json"
                backup = path.parent / "interrupted"
                objects = path / "objects"
                with RunningApp(self.command(route, "fault", path)) as process:
                    self.assertEqual(process.line(), "lite write ready")
                    original, state, rows = manifest(path)
                    before = set(objects.iterdir())
                    canonical.rename(backup)
                    canonical.mkdir(mode=0o700)
                    process.send("write")
                    self.assertEqual(process.line(), "lite publication uncertain")
                    orphans = set(objects.iterdir()) - before
                    self.assertEqual(len(orphans), 1)
                    self.assertEqual(next(iter(orphans)).read_bytes(), b"unpublished")
                    canonical.rmdir()
                    backup.rename(canonical)
                    process.send("again")
                    self.assertEqual(process.line(), "lite owner closed")
                    process.finish()
                self.assertEqual(canonical.read_bytes(), original)
                self.run_example(route, "open-code", path, "ready")
                _, recovered, current_rows = manifest(path)
                self.assertEqual(recovered["sequence"], state["sequence"])
                self.assertEqual(current_rows, rows)


if __name__ == "__main__":
    unittest.main()
