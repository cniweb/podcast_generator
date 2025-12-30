import sys
from pathlib import Path

# Stellt sicher, dass das Projekt-Root für lokale Module importierbar ist
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
