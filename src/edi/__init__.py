"""
EDI (Electronic Data Interchange) module
Handles EDI file generation and parsing

Supports two output formats:
- X12: Standard EDI X12 format
- CSV: Structured CSV format for data analysis and ETL
"""

from .generator import generate_edi_834, generate_edi_837, generate_edi_835, generate_edi_files

# Lazy import for parser to avoid mysql.connector dependency if not needed
try:
    from .parser import EDIParser
    __all__ = [
        'generate_edi_834',
        'generate_edi_837',
        'generate_edi_835',
        'generate_edi_files',
        'EDIParser'
    ]
except ImportError:
    __all__ = [
        'generate_edi_834',
        'generate_edi_837',
        'generate_edi_835',
        'generate_edi_files'
    ]

