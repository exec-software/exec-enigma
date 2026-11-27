"""Restart and filesystem checks for synthetic handoffs and work attempts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_records import manifest


ROOT = Path(__file__).resolve().parent.parent
SDK = Path(os.environ.get("NIL_SDK", ROOT / ".sdk"))
ROUTES = tuple(os.environ.get("ENIGMA_TEST_TARGETS", "vm,native").split(","))
ENABLED = os.environ.get("ENIGMA_WORK_TESTS") == "1"
HANDOFF = "work/42/handoff"
ATTEMPT = "work/42/attempt/native"


@unittest.skipUnless(ENABLED, "run scripts/test-work.sh to build the work probe")
class WorkTests(unittest.TestCase):
    def run_fixture(self, route: str, mode: str, directory: Path, output: bytes) -> None:
        artifact = ROOT / "build/work-probe/enigma-work-probe"
        command = (
            [str(SDK / "nilinterpreter"), str(artifact.with_suffix(".nil"))]
            if route == "vm"
            else [str(artifact)]
        )
        completed = subprocess.run(
            [*command, mode, str(directory)], capture_output=True, check=False, timeout=30
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout, output)

    def test_persisted_handoff_and_attempt_are_rechecked_after_restart(self) -> None:
        for route in ROUTES:
            with self.subTest(route=route), tempfile.TemporaryDirectory(prefix="enigma-work-") as temporary:
                directory = Path(temporary) / "work"
                self.run_fixture(route, "create", directory, b"handoff saved\n")
                _, before, rows = manifest(directory)
                self.assertEqual(before["sequence"], 4)
                handoff_bytes = rows[HANDOFF][2].read_bytes()
                attempt_bytes = rows[ATTEMPT][2].read_bytes()
                handoff = json.loads(handoff_bytes)
                attempt = json.loads(attempt_bytes)
                self.assertEqual(handoff["schema"], "enigma.work.v1")
                self.assertEqual(handoff["kind"], "handoff")
                self.assertEqual(attempt["kind"], "attempt")
                self.assertEqual(handoff["inputs"], attempt["inputs"])
                self.assertEqual(attempt["inputs"]["database_id"], before["database_id"])
                self.assertEqual(attempt["inputs"]["versions"], [1, 0, 2])

                self.run_fixture(route, "resume", directory, b"handoff needs review\n")
                _, after, observed = manifest(directory)
                self.assertEqual(before["database_id"], after["database_id"])
                self.assertNotEqual(before["incarnation"], after["incarnation"])
                self.assertEqual(after["authority"]["retired_through"], 1)
                self.assertEqual(after["sequence"], 7)
                self.assertEqual(observed["sdk/current"][2].read_bytes(), b"SDK B")
                self.assertEqual(observed["test/result"][2].read_bytes(), b"Native build passed")
                self.assertEqual(observed[HANDOFF][0], 3)
                self.assertEqual(observed[ATTEMPT][0], 4)
                self.assertEqual(observed[HANDOFF][2].read_bytes(), handoff_bytes)
                self.assertEqual(observed[ATTEMPT][2].read_bytes(), attempt_bytes)
