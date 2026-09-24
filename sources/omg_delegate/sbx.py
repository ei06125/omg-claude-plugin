"""A thin wrapper over the sbx CLI. Every call goes through here, so tests can replace the program."""

import json
import subprocess

from .models import Volume


class SbxError(Exception):
    pass


class Sbx:
    def __init__(self, executable: str, env: dict, log):
        self.executable = executable
        self.env = env
        self.log = log

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        try:
            done = subprocess.run(
                [self.executable, *args],
                capture_output=True,
                text=True,
                env=self.env,
                check=False,
            )
        except FileNotFoundError as error:
            raise SbxError(
                f"sbx is not installed: {self.executable!r} was not found"
            ) from error
        if check and done.returncode != 0:
            raise SbxError(
                f"sbx {args[0]} failed ({done.returncode}): {done.stderr.strip()[:300]}"
            )
        return done

    def sandboxes(self) -> list[str]:
        return [
            box["name"]
            for box in json.loads(self.run("ls", "--json").stdout)["sandboxes"]
        ]

    def create(
        self, name: str, volumes: list[Volume], image: str, cpus: int, memory_mib: int
    ) -> None:
        paths = [v.host_path + (":ro" if v.mode == "ro" else "") for v in volumes]
        args = ["create", "opencode", *paths, "--name", name, "-t", image]
        args += ["--cpus", str(cpus), "-m", f"{memory_mib}m", "--skills", "off"]
        if volumes[0].mode == "clone":
            args.append("--clone")
        self.run(*args)

    def kit_hosts(self, name: str) -> list[str]:
        """The hosts the agent kit allows by default for this sandbox."""
        rules = json.loads(self.run("policy", "ls", name, "--json").stdout)["rules"]
        return [
            host
            for rule in rules
            if (rule.get("name") or "").startswith("kit:")
            and rule["decision"] == "allow"
            for host in rule["resources"]
        ]

    def deny(self, name: str, hosts: list[str]) -> None:
        if hosts:
            self.run("policy", "deny", "network", "--sandbox", name, ",".join(hosts))

    def allow(self, name: str, hosts: list[str]) -> None:
        if hosts:
            self.run("policy", "allow", "network", "--sandbox", name, ",".join(hosts))

    def allowed(self, name: str, target: str) -> bool:
        """What sbx would decide for `target`. It exits 1 for a denied target, with the JSON still on stdout."""
        done = self.run(
            "policy",
            "check",
            "network",
            "--sandbox",
            name,
            "--json",
            target,
            check=False,
        )
        try:
            return bool(json.loads(done.stdout)["allowed"])
        except (ValueError, KeyError) as error:
            detail = done.stderr.strip()[:200]
            raise SbxError(
                f"sbx policy check gave no decision for {target}: {detail}"
            ) from error

    def stop(self, name: str) -> None:
        self.run("stop", name, check=False)

    def remove(self, name: str) -> None:
        self.run("rm", "--force", name, check=False)
