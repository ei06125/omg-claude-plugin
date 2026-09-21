"""Test-side handle on the fake sbx program: install it, script it, and read back what it saw."""

import json
import stat
import sys
from pathlib import Path

PROGRAM = Path(__file__).resolve().with_name("fake_sbx_program.py")
CANARY_HOST = "example.com:443"


class FakeSbx:
    def __init__(self, base: Path):
        self.dir = base / "fake-sbx"
        self.dir.mkdir()
        self.state_path = self.dir / "state.json"
        self.calls_path = self.dir / "calls.jsonl"
        self.release_file = self.dir / "release"
        self.executable = self.dir / "sbx"
        self.executable.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{PROGRAM}" "$@"\n'
        )
        self.executable.chmod(self.executable.stat().st_mode | stat.S_IXUSR)
        self.calls_path.touch()
        (self.dir / "clones").mkdir()
        self.state_path.write_text(
            json.dumps(
                {
                    "sandboxes": {},
                    "kit_allow": [],
                    "faults": [],
                    "global_default": "deny-all",
                    "canary": CANARY_HOST,
                    "backend_endpoints": [],
                    "agent": {},
                    "release_file": str(self.release_file),
                    "clone_dir": str(self.dir / "clones"),
                }
            )
        )

    def env(self):
        return {
            "OMG_DELEGATE_SBX": str(self.executable),
            "FAKE_SBX_STATE": str(self.state_path),
        }

    def state(self):
        return json.loads(self.state_path.read_text())

    def update(self, **changes):
        state = self.state()
        state.update(changes)
        self.state_path.write_text(json.dumps(state))

    def add_fault(self, fault):
        self.update(faults=[*self.state()["faults"], fault])

    def script_agent(self, **behaviour):
        self.update(agent={**self.state()["agent"], **behaviour})

    def release(self):
        self.release_file.touch()

    def calls(self):
        return [
            json.loads(line)
            for line in self.calls_path.read_text().splitlines()
            if line
        ]

    def commands(self, name):
        return [c for c in self.calls() if c.get("command") == name]

    def events(self, name):
        return [c for c in self.calls() if c.get("event") == name]

    def sandbox(self, name):
        return self.state()["sandboxes"].get(name)

    def running(self):
        return (self.dir / "agent.running").exists()
