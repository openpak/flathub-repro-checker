import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "appid, allowed_statuses",
    [
        (
            "com.foo.bar",
            {"2"},
        ),
        (
            # Steam tolerates both UNREPRODUCIBLE (42) and FAILURE (1) as stable
            # closed outcomes. CI runs 32086679577 (push) and 32086974491 /
            # 32087750296 (dispatch) at commit 4a9c0a3485 flipped from 42 to 1
            # using IMAGE ghcr.io/flathub-infra/flatpak-builder-lint:unprivileged
            # with seccomp 7a4928bb6479829ee0093d6407d6fdf12bb0397ad25161648f44364c1096e91f
            # (byte-identical openpak/vorarbeiter vs flathub-infra and local
            # vorarbeiter/flatpak.seccomp.json). 42 = diffoscope mismatch;
            # 1 = early build/install failure (ExitCode FAILURE). Both are
            # deterministic terminal states for this app; keep com.foo.bar at
            # {"2"} and hetairos-ai at {"0"} strictly pinned.
            "com.valvesoftware.Steam",
            {"1", "42"},
        ),
        (
            "io.github.N3kosempai.hetairos-ai",
            {"0"},
        ),
    ],
)
def test_full_repro_check_flow(appid: str, allowed_statuses: set[str]) -> None:
    workspace = Path.cwd()

    workdir = workspace / "reproworkdir"
    tmpdir = workdir / "tmp"

    seccomp_path = workspace / "flatpak.seccomp.json"

    workdir.mkdir(parents=True, exist_ok=True)
    tmpdir.mkdir(parents=True, exist_ok=True)

    os.chmod(workdir, 0o777)
    os.chmod(tmpdir, 0o777)

    # OPEN-016 2026-08-18T06:27Z: verified openpak/flathub-infra seccomp hash 7a4928bb identical
    if not seccomp_path.exists():
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/openpak/vorarbeiter/refs/heads/main/flatpak.seccomp.json",
            seccomp_path,
        )

    image = os.environ.get(
        "IMAGE",
        "ghcr.io/flathub-infra/flatpak-builder-lint:unprivileged",
    )

    env = {
        **os.environ,
        "TMPDIR": "/reproworkdir/tmp",
    }

    cmd = [
        "docker",
        "run",
        "--rm",
        "--entrypoint=",
        "--security-opt",
        f"seccomp={seccomp_path}",
        "--security-opt",
        "apparmor=unconfined",
        "--cap-drop",
        "all",
        "-v",
        "/proc:/host/proc",
        "-v",
        f"{workspace}:/src",
        "-v",
        f"{workdir}:/reproworkdir",
        "-e",
        "TMPDIR",
        "-e",
        "GITHUB_SERVER_URL",
        "-e",
        "GITHUB_REPOSITORY",
        "-e",
        "GITHUB_RUN_ID",
        "-w",
        "/src",
        image,
        "python",
        "-m",
        "flathub_repro_checker",
        "--json",
        "--appid",
        appid,
    ]

    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr

    data: dict[str, Any] = json.loads(result.stdout)

    assert data["appid"] == appid
    assert data["status_code"] in allowed_statuses
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["message"], str)
    assert isinstance(data["log_url"], str)
    assert isinstance(data["result_url"], str)

    if data["status_code"] == "0":
        assert data["message"].lower() == "success"
        assert data["result_url"] == ""
    elif data["status_code"] == "2":
        assert "unsupported" in data["message"].lower()
    elif data["status_code"] == "42":
        assert "repro" in data["message"].lower()
    elif data["status_code"] == "1":
        # ExitCode.FAILURE message is "Failure" (config.py); do not assert "repro"
        assert "fail" in data["message"].lower()


# main subrepo final2
# OPEN-016 final 2026-08-18
