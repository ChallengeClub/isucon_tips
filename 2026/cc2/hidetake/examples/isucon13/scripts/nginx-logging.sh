#!/usr/bin/env bash
# Explicit approval required: modifies nginx configuration and reloads nginx.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 3 || ! $1 =~ ^(enable|restore)$ ]]; then echo 'Usage: bash target/scripts/nginx-logging.sh enable|restore OPERATION_ID PREPARATION_ID' >&2; exit 2; fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
exec python3 "$script_dir/lib/measurement_ansible.py" "$@"
