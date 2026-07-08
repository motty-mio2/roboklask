import sys
from pathlib import Path

# Add src/ to Python path so that 'viewer' package imports work correctly
sys.path.insert(0, str(Path(__file__).parent / "src"))

from python.main import main  # type: ignore

if __name__ == "__main__":
    main()
