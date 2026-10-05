"""Isolated work directories; Docker required for untrusted submitted code."""
from dataclasses import dataclass, asdict
from pathlib import Path
import os
import signal
import subprocess
import sys
import tempfile
import time

@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    seconds: float
    def dict(self):
        return asdict(self)
    @property
    def passed(self):
        return self.returncode == 0 and not self.timed_out

def run_code(source, tests=None, *, backend="docker", timeout=8, test_framework="pytest"):
    if backend not in {"docker", "trusted"}:
        raise ValueError("Runner must be docker or trusted")
    with tempfile.TemporaryDirectory(prefix="pyfix-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        (root / "candidate.py").write_text(source, encoding="utf-8")
        if tests is not None:
            (root / "test_candidate.py").write_text(tests, encoding="utf-8")
        if test_framework not in {"pytest", "unittest"}:
            raise ValueError("Unknown test framework")
        args = (["-m", "pytest", "-q", "-p", "no:cacheprovider", "test_candidate.py"] if test_framework == "pytest" else ["-m", "unittest", "-v", "test_candidate"]) if tests is not None else ["candidate.py"]
        env = {k: v for k, v in os.environ.items() if k in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        container = "pyfix-" + os.path.basename(directory)
        if backend == "docker":
            cmd = ["docker", "run", "--rm", "--name", container, "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit=32", "--memory=256m", "--cpus=1", "--user=65534:65534", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "-v", f"{root.resolve()}:/work:ro", "-w", "/work", "pyfix-runner:1", "python", *args]
        else:
            cmd = [sys.executable, *args]
        started = time.monotonic()
        # File-backed capture avoids unlimited in-memory pipe accumulation.
        with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
            try:
                process = subprocess.Popen(cmd, cwd=root, env=env, stdout=out, stderr=err, start_new_session=os.name != "nt")
            except FileNotFoundError as exc:
                raise RuntimeError("Docker runner unavailable. Install Docker and build Dockerfile.runner.") from exc
            timed_out = False
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                if os.name != "nt":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                process.wait()
                if backend == "docker":
                    subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10)
            out.seek(0); err.seek(0)
            stdout, stderr = out.read(64000).decode(errors="replace"), err.read(64000).decode(errors="replace")
            if backend == "docker" and process.returncode in {125,126,127}:
                raise RuntimeError("Docker could not start the runner. Build Dockerfile.runner and check Docker is running.")
            code = process.returncode
            if tests is not None and test_framework == "unittest" and "Ran 0 tests" in stderr:
                code = 5
            return RunResult(code, stdout, stderr, timed_out, round(time.monotonic()-started, 4))
