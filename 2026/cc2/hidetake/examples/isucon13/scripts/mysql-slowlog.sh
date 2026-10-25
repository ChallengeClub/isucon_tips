#!/usr/bin/env bash
# Explicit approval required: MySQL logging settings plus Go/PowerDNS restart.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 3 || ! $1 =~ ^(prepare|restore)$ ]]; then echo 'Usage: bash target/scripts/mysql-slowlog.sh prepare|restore OPERATION_ID PREPARATION_ID' >&2; exit 2; fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
umask 077
exec python3 "$script_dir/lib/slowlog.py" "$@"
