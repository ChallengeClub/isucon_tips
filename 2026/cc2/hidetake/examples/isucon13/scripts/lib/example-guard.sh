# Sourced by shell entries. This is a review gate, not a settings abstraction.
example_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)
example_git_root=$(git -C "$example_root" rev-parse --show-toplevel 2>/dev/null || true)
if [[ $example_git_root != "$example_root" ]]; then
  echo 'Reference only: copy this example into the root of a private target repository first.' >&2
  exit 2
fi
python3 - "$example_root/example-review.json" <<'PY'
import json
from pathlib import Path
import sys

try:
    reviewed = json.loads(Path(sys.argv[1]).read_text()).get('reviewed_for_target') is True
except (OSError, ValueError):
    reviewed = False
if not reviewed:
    sys.exit('Review ADAPTATION.md and set example-review.json reviewed_for_target=true in the private target. Remote approval is still separate.')
PY
