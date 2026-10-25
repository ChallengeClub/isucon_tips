#!/usr/bin/env bash
# Changes remote build directories and caches. Explicit approval is required.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ $# != 3 && $# != 4 ]]; then
  echo 'Usage: bash target/scripts/build-go-remote.sh COMMIT BUILD_ID ORIGINAL_BINARY_SHA256 [LIVE_SOURCE_COMMIT]' >&2
  exit 2
fi
umask 077
exec python3 "$script_dir/lib/build_go_remote.py" "$@"
