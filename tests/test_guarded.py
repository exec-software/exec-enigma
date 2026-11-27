"""Process and filesystem checks for guarded record writes."""

from __future__ import annotations

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
ENABLED = os.environ.get("ENIGMA_GUARDED_TESTS") == "1"
HANDOFF = "work/42/handoff"
DECISION = "release/decision"


def command(route: str, mode: str, directory: Path) -> list[str]:
    artifact = ROOT / "build/guarded-probe/enigma-guarded-probe"
    executable = (
        [str(SDK / "nilinterpreter"), str(artifact.with_suffix(".nil"))]
        if route == "vm"
        else [str(artifact)]
    )
    return [*executable, mode, str(directory)]


@unittest.skipUnless(ENABLED, "run scripts/test-guarded.sh to build the guarded probe")
class GuardedTests(unittest.TestCase):
    def run_fixture(self, route: str, mode: str, path: Path, message: bytes) -> None:
        completed = subprocess.run(
            command(route, mode, path), capture_output=True, check=False, timeout=30
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, message + b"\n")

    def test_guarded_versions_survive_recovery_and_refusals_publish_no_body(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-guarded-") as temporary:
                path = Path(temporary) / "store"
                self.run_fixture(route, "create", path, b"guarded writes committed")
                _, before, initial = manifest(path)
                self.assertEqual(before["sequence"], 3)
                self.assertEqual(before["authority"]["clock_floor"], 2)
                self.assertEqual({key: row[0] for key, row in initial.items()},
                                 {DECISION: 2, "sdk/current": 1, HANDOFF: 3})
                self.assertEqual(initial[DECISION][2].read_bytes(), b"Native check pending.")
                handoff = json.loads(initial[HANDOFF][2].read_bytes())
                inputs = handoff["inputs"]
                self.assertEqual(inputs["database_id"], before["database_id"])
                self.assertEqual(inputs["keys"], ["sdk/current", "test/result"])
                self.assertEqual(inputs["versions"], [1, 0])
                self.assertEqual(len(list((path / "objects").iterdir())), 3)

                self.run_fixture(route, "resume", path, b"guarded refusals preserved records")
                _, after, observed = manifest(path)
                self.assertEqual(after["database_id"], before["database_id"])
                self.assertNotEqual(after["incarnation"], before["incarnation"])
                self.assertEqual(after["authority"]["retired_through"], 1)
                self.assertEqual(after["authority"]["clock_floor"], 6)
                self.assertEqual(after["sequence"], 7)
                self.assertEqual(
                    {key: row[0] for key, row in observed.items()},
                    {"activity/ping": 4, DECISION: 2, "sdk/current": 6,
                     "test/result": 7, HANDOFF: 5},
                )
                self.assertEqual(observed[DECISION], initial[DECISION])
                self.assertEqual(observed["sdk/current"][2].read_bytes(), b"SDK B")
                self.assertEqual(observed["test/result"][2].read_bytes(), b"Native check passed.")
                updated = json.loads(observed[HANDOFF][2].read_bytes())
                self.assertEqual(updated["summary"], "Native check still pending on SDK A.")
                self.assertEqual(updated["inputs"], inputs)
                self.assertEqual(len(list((path / "objects").iterdir())), 7)

    def test_matched_guards_still_propagate_uncertain_publication(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-guarded-fault-") as temporary:
                path = Path(temporary) / "store"
                self.run_fixture(route, "create", path, b"guarded writes committed")
                canonical = path / "manifest.json"
                objects = path / "objects"
                backup = path.parent / "interrupted"
                with RunningApp(command(route, "fault", path)) as process:
                    self.assertEqual(process.line(), "guarded publication ready")
                    raw, before, rows = manifest(path)
                    previous_bodies = set(objects.iterdir())
                    canonical.rename(backup)
                    canonical.mkdir(mode=0o700)
                    process.send("write")
                    self.assertEqual(process.line(), "guarded outcome uncertain")
                    orphans = set(objects.iterdir()) - previous_bodies
                    self.assertEqual(len(orphans), 1)
                    candidate = json.loads(next(iter(orphans)).read_bytes())
                    self.assertEqual(candidate["summary"], "Matching inputs, publication interrupted.")
                    canonical.rmdir()
                    backup.rename(canonical)
                    process.send("again")
                    self.assertEqual(process.line(), "guarded owner closed")
                    process.finish()
                restored, after, observed = manifest(path)
                self.assertEqual(restored, raw)
                self.assertEqual(after["sequence"], before["sequence"])
                self.assertEqual(observed, rows)
                self.assertEqual(set(objects.iterdir()) - previous_bodies, orphans)


if __name__ == "__main__":
    unittest.main()
