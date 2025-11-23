# Project Structure

## Directory Layout

```
claim-data-generater/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── PROJECT_STRUCTURE.md     # This file
│
├── config/                  # Configuration files
│   ├── __init__.py
│   └── config.py           # Database and EDI configuration
│
├── src/                     # Source code
│   ├── __init__.py
│   ├── edi/                 # EDI generation and parsing
│   │   ├── __init__.py
│   │   ├── generator.py    # EDI file generation (834, 837, 835)
│   │   └── parser.py        # EDI file parsing to database
│   ├── database/            # Database operations
│   │   ├── __init__.py
│   │   └── generator.py    # Database data generation
│   └── models/              # Data models (future)
│       └── __init__.py
│
├── data/                    # Data files
│   ├── samples/             # Sample EDI files
│   │   ├── .gitkeep
│   │   ├── edi_834_large_sample.txt
│   │   ├── edi_837_large_sample.txt
│   │   └── edi_835_large_sample.txt
│   └── output/              # Generated output files
│       └── .gitkeep
│
├── scripts/                 # Utility scripts
│   └── main.py              # Main entry point
│
└── tests/                   # Test files (future)
    └── __init__.py
```

## File Descriptions

### Configuration
- `config/config.py`: Contains all configuration settings including database connection, EDI sender/receiver IDs, and file paths.

### Source Code
- `src/edi/generator.py`: Generates EDI 834, 837, and 835 files with proper segment counting and control numbers.
- `src/edi/parser.py`: Parses EDI files and imports data into the database.
- `src/database/generator.py`: Generates sample data for database tables.

### Scripts
- `scripts/main.py`: Main entry point for running the EDI generation.

## Migration Notes

The original files have been reorganized:
- `generate_edi_data.py` → `src/edi/generator.py`
- `parse_edi_to_db.py` → `src/edi/parser.py`
- `generate_empty_data.py` → `src/database/generator.py`
- Sample EDI files → `data/samples/`

## Usage

After restructuring, import paths have changed:

**Before:**
```python
from generate_edi_data import generate_edi_834
```

**After:**
```python
from src.edi.generator import generate_edi_834
```

Or use the package imports:
```python
from src.edi import generate_edi_834
```

