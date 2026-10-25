#!/usr/bin/env bash
# Runs one ISUCON13 benchmark. Explicit benchmark approval is required.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/example-guard.sh"
if [[ $# != 1 || ! $1 =~ ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ ]]; then
  echo 'Usage: bash target/scripts/benchmark.sh RUN_ID' >&2
  exit 2
fi
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(cd -- "$script_dir/../.." && pwd)
run_id=$1
result_dir="$workspace/artifacts/$run_id"
umask 077
mkdir -- "$result_dir"
# No source deployment is performed; local HEAD is tooling provenance only.
git -C "$script_dir/.." rev-parse HEAD > "$result_dir/tooling-head.txt"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes isucon-target 'set -eu
  for service in isupipe-go nginx mysql pdns; do systemctl is-active "$service"; done
  if pgrep -x bench >/dev/null; then exit 1; fi
  sha256sum /home/isucon/webapp/go/isupipe
  date -u +%FT%TZ' > "$result_dir/preflight-target.txt"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes isucon-benchmark 'set -eu
  if pgrep -x bench >/dev/null; then exit 1; fi
  for name in pipe.u.isucon.local test001.u.isucon.local; do
    test "$(dig @192.0.2.10 "$name" A +short +time=2 +tries=1)" = 192.0.2.10
  done
  test "$(curl --insecure --silent --show-error --max-time 5 --output /dev/null --write-out "%{http_code}" --resolve pipe.u.isucon.local:443:192.0.2.10 https://pipe.u.isucon.local/)" = 200
  sha256sum /home/isucon/bench
  date -u +%FT%TZ' > "$result_dir/preflight-benchmark.txt"
# Fresh remote result directory prevents confusing an old result with this run.
# No automatic retry: SSH loss or failure requires inspecting remote state.
set +e
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes isucon-benchmark \
 "sudo -n -u isucon -H bash -lc 'umask 077
  cd /home/isucon || exit 1
  run_dir=/tmp/isucon13-$run_id
  mkdir \"\$run_dir\" || exit 1
  date -u +%FT%TZ > \"\$run_dir/start.txt\"
  ./bench run --target https://pipe.u.isucon.local --nameserver 192.0.2.10 --dns-port 53 --enable-ssl --staff-log-path \"\$run_dir/staff.log\" --contestant-log-path \"\$run_dir/contestant.log\" --result-path \"\$run_dir/result.json\" > \"\$run_dir/stdout.log\" 2> \"\$run_dir/stderr.log\"
  code=\$?
  echo \"\$code\" > \"\$run_dir/exit-code.txt\"
  date -u +%FT%TZ > \"\$run_dir/end.txt\"
  exit \"\$code\"'" > "$result_dir/ssh.stdout" 2> "$result_dir/ssh.stderr"
transport_code=$?
set -e
printf '%s\n' "$transport_code" > "$result_dir/ssh-exit-code.txt"
for name in start.txt end.txt exit-code.txt result.json staff.log contestant.log stdout.log stderr.log; do
  ssh -o BatchMode=yes -o StrictHostKeyChecking=yes isucon-benchmark \
    "sudo -n -u isucon cat /tmp/isucon13-$run_id/$name" \
    > "$result_dir/$name" 2> "$result_dir/$name.fetch.stderr" || true
done
printf 'run_id=%s ssh_exit_code=%s artifacts=%s\n' "$run_id" "$transport_code" "$result_dir"
# Do not print raw messages/logs: failure responses may contain sensitive data.
python3 - "$result_dir" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
try:
    result = json.loads((p / 'result.json').read_text())
    code = int((p / 'exit-code.txt').read_text())
    print(json.dumps({k: result.get(k) for k in ['pass', 'score', 'language', 'resolved_count']}))
    transport = int((p / 'ssh-exit-code.txt').read_text())
    sys.exit(0 if transport == 0 and code == 0 and result.get('pass') is True else 1)
except (ValueError, OSError):
    print('Result incomplete; inspect saved run without retrying.', file=sys.stderr)
    sys.exit(1)
PY
