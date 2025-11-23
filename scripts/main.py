#!/usr/bin/env python3
"""
Main entry point for the claim data generator
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.edi.generator import generate_edi_files

if __name__ == "__main__":
    print("Starting EDI file generation...")
    generate_edi_files()
    print("Done!")

