#!/usr/bin/env bash
# Explicit approval required: installs sysstat on the target. No apt update.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 1 ]]; then echo 'Usage: bash target/scripts/measurement-tools.sh OPERATION_ID' >&2; exit 2; fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
exec python3 "$script_dir/lib/measurement_ansible.py" tools "$1" "$1"
