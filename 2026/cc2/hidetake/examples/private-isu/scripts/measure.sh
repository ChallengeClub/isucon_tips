#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/config.sh"
export TARGET_HOST
exec python3 "$script_dir/measurement.py" "$@"
