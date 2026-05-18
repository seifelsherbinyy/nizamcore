"""pytest configuration — ensures 'radar' package is importable from test runs."""
import sys
from pathlib import Path

# Add MARSAD__flight_radar/ to sys.path so 'import radar.*' works
sys.path.insert(0, str(Path(__file__).parent))
