#!/usr/bin/env bash
# Explicit approval required: log rename/recreate/reopen and read-only OS samplers.
# No benchmark, restart, configuration repair, or restore is performed here.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 2 ]]; then echo 'Usage: bash target/scripts/measure.sh RUN_ID MYSQL_PREPARATION_ID' >&2; exit 2; fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
exec python3 "$script_dir/lib/measurement.py" "$@"
