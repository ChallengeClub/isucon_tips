#!/usr/bin/env bash
# Read-only remote inventory. No package installs, configuration writes or log data.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 1 || ! $1 =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ ]]; then
  echo 'Usage: bash target/scripts/inspect-measurement.sh RUN_ID' >&2; exit 2
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(cd -- "$script_dir/../.." && pwd)
umask 077
folder="$workspace/artifacts/$1"
mkdir -- "$folder"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10 isucon-target \
  'sudo -n python3 -' < "$script_dir/lib/inspect_measurement_remote.py" \
  > "$folder/inventory.json" 2> "$folder/ssh.stderr"
python3 -m json.tool "$folder/inventory.json" > /dev/null
printf 'Read-only inventory saved: %s\n' "$folder"
