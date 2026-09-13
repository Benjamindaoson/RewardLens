#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute_audit_metrics import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "specificity", *sys.argv[1:]]
    raise SystemExit(main())
