#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/config.sh"
export BENCHMARK_HOST BENCHMARK_USER BENCHMARK_BINARY BENCHMARK_USERDATA BENCHMARK_TARGET_URL
exec python3 "$script_dir/benchmark.py" "$@"
