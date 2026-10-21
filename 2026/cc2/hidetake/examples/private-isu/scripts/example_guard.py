"""Require placement at the root of the private target checkout before CLI execution."""
from pathlib import Path


def require_target_checkout(parser):
    if not (Path(__file__).resolve().parents[1] / '.git').exists():
        parser.error('Copy this example into a private target repository before execution')
