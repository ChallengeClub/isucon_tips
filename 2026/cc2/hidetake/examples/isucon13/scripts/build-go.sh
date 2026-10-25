#!/usr/bin/env bash
# Local build only. COMMIT is a full 40-character SHA.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $# != 3 ]]; then echo 'Usage: bash target/scripts/build-go.sh COMMIT BUILD_ID ORIGINAL_BINARY_SHA256' >&2; exit 2; fi
umask 077
exec python3 "$script_dir/lib/build_go.py" "$1" "$2" "$3"
