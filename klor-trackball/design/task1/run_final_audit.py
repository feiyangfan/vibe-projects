#!/usr/bin/env python3
import json
import sys
import numpy as np
import mechanical_reference_audit_v2 as audit

_original = json.dumps

def _default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

def dumps(obj, *args, **kwargs):
    kwargs.setdefault("default", _default)
    return _original(obj, *args, **kwargs)

audit.json.dumps = dumps
sys.exit(audit.main())
