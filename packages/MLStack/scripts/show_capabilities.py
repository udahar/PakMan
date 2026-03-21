#!/usr/bin/env python3
from __future__ import annotations

import json

from capabilities import get_capabilities


if __name__ == "__main__":
    print(json.dumps(get_capabilities(), indent=2))
