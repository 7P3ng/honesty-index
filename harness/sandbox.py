"""One bubblewrap wrapper for every agent run and every hidden check.

Layout inside the sandbox:
  /work        the task working copy, read-write (the only writable host path)
  $HOME        a throwaway directory (make_throwaway_home) whose .claude/.credentials.json
               is the real file bind-mounted read-write so token refreshes persist
  /usr /lib /lib64 /bin /sbin /etc   read-only from the host
  claude       the real binary's version directory, read-only, at its host path
  /tmp         private tmpfs
Nothing else from the host is visible. Network is a per-call switch.

Why not --bare: `claude --bare` skips reading .credentials.json (measured 2026-09-19), so
the throwaway HOME is how the agent is kept stock — no global CLAUDE.md, skills, hooks,
MCP servers, or settings — while still being logged in.
"""
from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

CLAUDE_BIN = Path("/home/tpeng/.local/bin/claude")


@dataclass(frozen=True)
class SandboxSpec:
    work_dir: Path
    ro_binds: tuple[tuple[Path, str], ...]
    network: bool
    timeout_s: int
    env: dict[str, str]


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    wall_ms: int


def make_throwaway_home(real_home: Path, parent: Path) -> Path:
    """Create <parent>/home-<random>/ holding only .claude.json (oauthAccount + onboarding
    flag) and an empty .claude/ directory. The credentials file is bound at run time, not
    copied. Side effect: creates files. Raises ValueError if the real ~/.claude.json lacks
    oauthAccount (the box has never logged in)."""
    home = parent / f"home-{secrets.token_hex(4)}"
    (home / ".claude").mkdir(parents=True)
    real_cfg = json.loads((real_home / ".claude.json").read_text())
    if "oauthAccount" not in real_cfg:
        raise ValueError(f"{real_home / '.claude.json'} has no oauthAccount; run `claude` interactively once")
    (home / ".claude.json").write_text(
        json.dumps({"oauthAccount": real_cfg["oauthAccount"], "hasCompletedOnboarding": True})
    )
    return home


def _bwrap_argv(spec: SandboxSpec, home: Path | None, argv: list[str]) -> list[str]:
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise RuntimeError("bwrap not installed: run `sudo apt install bubblewrap` (spec §2)")
    cmd: list[str] = [
        bwrap, "--die-with-parent", "--new-session",
        "--unshare-all", *(["--share-net"] if spec.network else []),
        "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
        "--ro-bind", "/usr", "/usr", "--ro-bind", "/etc", "/etc",
    ]
    for d in ("/lib", "/lib64", "/bin", "/sbin"):
        if Path(d).exists():
            cmd += ["--ro-bind", d, d]
    if spec.network:
        # /etc/resolv.conf is a symlink into /run/systemd/resolve on this box; without
        # the target, DNS fails silently and claude hangs until the timeout.
        resolver_dir = Path("/run/systemd/resolve")
        if resolver_dir.is_dir():
            cmd += ["--ro-bind", str(resolver_dir), str(resolver_dir)]
    cmd += ["--tmpfs", "/home", "--bind", str(spec.work_dir), "/work"]
    if home is not None:
        real_creds = Path.home() / ".claude" / ".credentials.json"
        claude_real = CLAUDE_BIN.resolve()
        cmd += ["--bind", str(home), str(home),
                "--bind", str(real_creds), str(home / ".claude" / ".credentials.json"),
                "--ro-bind", str(claude_real.parent), str(claude_real.parent),
                "--ro-bind", str(claude_real), str(CLAUDE_BIN)]
    for host_path, sandbox_path in spec.ro_binds:
        cmd += ["--ro-bind", str(host_path), sandbox_path]
    cmd += ["--clearenv",
            "--setenv", "PATH", f"{CLAUDE_BIN.parent}:/usr/local/bin:/usr/bin:/bin",
            "--setenv", "HOME", str(home) if home else "/tmp",
            "--setenv", "LANG", "C.UTF-8",
            "--setenv", "TERM", "dumb",
            "--chdir", "/work"]
    for key, value in spec.env.items():
        cmd += ["--setenv", key, value]
    return cmd + ["--", *argv]


def _text(data: bytes | str | None) -> str:
    if data is None:
        return ""
    return data.decode(errors="replace") if isinstance(data, bytes) else data


def run_in_sandbox(spec: SandboxSpec, argv: list[str], *, home: Path | None) -> SandboxResult:
    """Run argv inside bubblewrap with stdin closed. Side effects: writes under spec.work_dir
    and, when home is given, token refreshes land in the real credentials file via the bind."""
    cmd = _bwrap_argv(spec, home, argv)
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=spec.timeout_s)
    except subprocess.TimeoutExpired as exc:
        return SandboxResult(None, _text(exc.stdout), _text(exc.stderr), True, int((time.monotonic() - started) * 1000))
    return SandboxResult(proc.returncode, proc.stdout, proc.stderr, False, int((time.monotonic() - started) * 1000))
