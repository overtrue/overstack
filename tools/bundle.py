"""Build device-specific downloads with their shared components."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('bundle_variants.py')),run_name='__main__')
