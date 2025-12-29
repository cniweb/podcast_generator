import sys
from pathlib import Path

# Ensure project root is importable for local modules
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
