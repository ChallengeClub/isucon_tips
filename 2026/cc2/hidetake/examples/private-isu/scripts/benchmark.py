#!/usr/bin/env python3
"""Run the remote benchmark explicitly; retain output and execution metadata locally."""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from urllib.parse import urlsplit


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description="Run benchmark after team declaration and approval.")
    parser.add_argument("--run-id", required=True, help="Unique measurement ID (letters, digits, - and _)")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", args.run_id):
        parser.error("Invalid run ID")

    host = os.environ["BENCHMARK_HOST"]
    user = os.environ["BENCHMARK_USER"]
    binary = os.environ["BENCHMARK_BINARY"]
    userdata = os.environ["BENCHMARK_USERDATA"]
    target_url = os.environ["BENCHMARK_TARGET_URL"]
    try:
        parsed = urlsplit(target_url)
        valid_url = (
            parsed.scheme in ("http", "https") and parsed.hostname
            and parsed.username is None and parsed.password is None
            and parsed.path in ("", "/") and not parsed.query and not parsed.fragment
        )
        parsed.port  # Validate the optional port.
    except ValueError:
        valid_url = False
    if not valid_url:
        parser.error("Set BENCHMARK_TARGET_URL to the target HTTP origin, without credentials")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", host) or not user or not binary.startswith("/") or not userdata.startswith("/"):
        parser.error("Configure the approved SSH alias, user, binary and userdata paths in config.sh")

    if not (Path(__file__).resolve().parents[1] / '.git').exists():
        parser.error('Copy this example into a private target repository before execution')
    workspace = Path(__file__).resolve().parents[2]
    output = workspace / "artifacts" / args.run_id
    output.parent.mkdir(exist_ok=True)
    try:
        output.mkdir()  # Never overwrite an existing run.
    except FileExistsError:
        parser.error("Run ID already exists; choose another ID")

    argv = [binary, "-target", target_url, "-userdata", userdata]
    metadata = {
        "run_id": args.run_id,
        "started_at_utc": now(),
        "benchmark_host": host,
        "benchmark_user": user,
        "target_url": target_url,
        "argv": argv,
        "mode": "initial-uninstrumented",
        "deployed_revision": None,
        "deployed_revision_note": "Not verified; local HEAD is not the deployed revision",
        "binary_sha256": None,
        "ssh_exit_code": None,
        "benchmark_pass": None,
        "score": None,
        "status": "started",
    }

    def save():
        (output / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        )

    def remote(command):
        inner = 'cd -- "$HOME" && ' + command
        return ["ssh", "-o", "BatchMode=yes", host,
                "sudo -n -u " + shlex.quote(user) + " -H bash -lc " + shlex.quote(inner)]

    save()
    exit_code = 1
    with (output / "benchmark.stdout.json").open("wb") as stdout, \
            (output / "benchmark.stderr.log").open("wb") as stderr:
        try:
            checksum = subprocess.run(
                remote("sha256sum -- " + shlex.quote(binary)),
                stdout=subprocess.PIPE, stderr=stderr, check=False,
            )
            digest = checksum.stdout.decode(errors="replace").split()
            if checksum.returncode != 0 or not digest or not re.fullmatch(r"[0-9a-f]{64}", digest[0]):
                raise RuntimeError("Binary hash check failed; benchmark was not started")
            metadata["binary_sha256"] = digest[0]
            metadata["status"] = "running"
            save()
            result = subprocess.run(remote("exec " + shlex.join(argv)), stdout=stdout, stderr=stderr)
            metadata["ssh_exit_code"] = result.returncode
            stdout.flush()
            try:
                report = json.loads((output / "benchmark.stdout.json").read_text())
            except (ValueError, UnicodeError):
                report = None
            if isinstance(report, dict) and isinstance(report.get("pass"), bool):
                metadata["benchmark_pass"] = report["pass"]
                metadata["score"] = report.get("score")
            success = result.returncode == 0 and metadata["benchmark_pass"] is True
            metadata["status"] = "passed" if success else "failed"
            exit_code = 0 if success else 1
        except (OSError, RuntimeError) as error:
            metadata["status"] = "error"
            metadata["error"] = str(error)
        except KeyboardInterrupt:
            metadata["status"] = "interrupted"
            exit_code = 130
        finally:
            metadata["finished_at_utc"] = now()
            save()

    print(f"{metadata['status']}: {output}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
