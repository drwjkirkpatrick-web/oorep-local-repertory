"""Pytest path setup for oorep-local-repertory."""
import sys
from pathlib import Path

# Add repo root so 'from oorep import ...' and 'from oorep.homeopathic_repertory import ...' work
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))