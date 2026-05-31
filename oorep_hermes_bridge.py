#!/usr/bin/env python3
"""
OOREP-Hermes Bridge: Natural-language interface for homeopathic repertory.

Place this in your Hermes project root (e.g., ~/projects/homeopathic-rpg/ or
any Hermes-aware directory) and run:

    from oorep_bridge import OOREPBridge
    bridge = OOREPBridge()
    result = bridge.handle("repertorize dry cough, hoarseness")
    print(result['formatted'])

Or run directly:
    python oorep_bridge.py "repertorize dry cough, hoarseness"
"""

# This is a thin launcher that delegates to the skill-bridge implementation.
# The canonical implementation lives at:
#   ~/.hermes/skills/clinic/oorep-hermes-bridge/scripts/oorep_bridge.py

import sys
from pathlib import Path

_SKILL_DIR = Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"
sys.path.insert(0, str(_SKILL_DIR))
sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))

try:
    from oorep_bridge import OOREPBridge, quick_handle
except ImportError as e:
    print(f"ERROR: Could not import oorep_bridge. Ensure OOREP is installed at ~/projects/oorep-local-repertory/")
    print(f"       and the skill bridge is at {_SKILL_DIR}")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = "repertorize dry cough, hoarseness"
    print(quick_handle(msg))
