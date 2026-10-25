#!/usr/bin/env bash
# Explicit approval required. Binary-only deployment; build records the live source baseline.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $# != 1 ]]; then echo 'Usage: bash target/scripts/deploy.sh BUILD_ID' >&2; exit 2; fi
umask 077
exec python3 "$script_dir/lib/go_release.py" deploy "$1"
