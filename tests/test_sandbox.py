"""Containment is proven, not assumed: the same probes are run on the bare host (they
must succeed there — that is the 'fail first' baseline) and inside the sandbox (refused)."""
import json
import subprocess
from pathlib import Path

import pytest

from harness.sandbox import SandboxSpec, make_throwaway_home, run_in_sandbox

pytestmark = pytest.mark.needs_bwrap

PROBE_SSH = "ls ~/.ssh >/dev/null 2>&1 && echo VISIBLE || echo REFUSED"
PROBE_NET = (
    "python3 -c 'import socket; socket.create_connection((\"1.1.1.1\", 53), timeout=3)' "
    ">/dev/null 2>&1 && echo VISIBLE || echo REFUSED"
)


def test_baseline_bare_host_can_see_ssh() -> None:
    """Fail-first baseline: on the bare host the probe sees ~/.ssh. If this fails, the probe is broken."""
    out = subprocess.run(["bash", "-c", PROBE_SSH], capture_output=True, text=True)
    assert out.stdout.strip() == "VISIBLE"


def test_sandbox_hides_home_and_check_dir(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    secret = tmp_path / "check"
    secret.mkdir()
    (secret / "check.sh").write_text("exit 0\n")
    home = make_throwaway_home(Path.home(), tmp_path)
    spec = SandboxSpec(work_dir=work, ro_binds=(), network=False, timeout_s=30, env={})
    probe = f"{PROBE_SSH}; ls {secret} >/dev/null 2>&1 && echo VISIBLE || echo REFUSED; ls /work"
    res = run_in_sandbox(spec, ["bash", "-c", probe], home=home)
    lines = res.stdout.split()
    assert lines[0] == "REFUSED", res
    assert lines[1] == "REFUSED", res
    assert res.exit_code == 0


def test_sandbox_network_off_and_on(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    home = make_throwaway_home(Path.home(), tmp_path)
    off = run_in_sandbox(SandboxSpec(work, (), False, 30, {}), ["bash", "-c", PROBE_NET], home=home)
    on = run_in_sandbox(SandboxSpec(work, (), True, 30, {}), ["bash", "-c", PROBE_NET], home=home)
    assert off.stdout.strip() == "REFUSED"
    assert on.stdout.strip() == "VISIBLE"
    dns = run_in_sandbox(SandboxSpec(work, (), True, 30, {}), ["getent", "hosts", "api.anthropic.com"], home=home)
    assert dns.exit_code == 0 and "api.anthropic.com" in dns.stdout, "DNS must resolve inside the sandbox when network is on"


def test_sandbox_timeout_kills(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    home = make_throwaway_home(Path.home(), tmp_path)
    res = run_in_sandbox(SandboxSpec(work, (), False, 2, {}), ["sleep", "30"], home=home)
    assert res.timed_out and res.exit_code is None and res.wall_ms < 10_000


def test_throwaway_home_has_only_two_entries(tmp_path: Path) -> None:
    home = make_throwaway_home(Path.home(), tmp_path)
    assert sorted(p.name for p in home.iterdir()) == [".claude", ".claude.json"]
    assert not (home / ".claude" / ".credentials.json").exists()  # bound at run time, not copied
    cfg = json.loads((home / ".claude.json").read_text())
    assert cfg["hasCompletedOnboarding"] is True and "oauthAccount" in cfg


def test_work_dir_is_writable_and_home_is_sandbox_home(tmp_path: Path) -> None:
    work = tmp_path / "w"
    work.mkdir()
    home = make_throwaway_home(Path.home(), tmp_path)
    res = run_in_sandbox(SandboxSpec(work, (), False, 30, {}), ["bash", "-c", "echo hi > /work/f && echo $HOME"], home=home)
    assert (work / "f").read_text() == "hi\n"
    assert res.stdout.strip() == "/home/agent", "host path of the throwaway home must not be visible"
    assert str(home) not in res.stdout
