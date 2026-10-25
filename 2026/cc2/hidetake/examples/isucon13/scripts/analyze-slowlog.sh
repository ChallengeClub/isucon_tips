#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 1 ]]; then echo 'Usage: bash target/scripts/analyze-slowlog.sh RUN_ID' >&2; exit 2; fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
exec python3 "$script_dir/lib/analyze_slowlog.py" --run-id "$1"
