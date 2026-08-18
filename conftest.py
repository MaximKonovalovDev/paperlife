import sys
import pathlib

# Make `import paperlife` work when pytest runs from the repo root.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
