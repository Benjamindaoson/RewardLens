#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.runner_lib import main_with_stage  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main_with_stage("gqa_downstream"))
