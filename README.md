# Claim Data Generator

A Python tool for generating EDI (Electronic Data Interchange) files and populating insurance databases with sample data.

## Features

- **EDI File Generation**: Generate EDI 834 (Enrollment), 837 (Claims), and 835 (Payment) files
- **Database Population**: Generate and insert sample data into insurance databases
- **EDI Parsing**: Parse EDI files and import data into database

## Project Structure

```
claim-data-generater/
├── src/
│   ├── edi/              # EDI generation and parsing
│   │   ├── generator.py  # EDI file generation
│   │   └── parser.py     # EDI file parsing
│   ├── database/         # Database operations
│   │   └── generator.py # Database data generation
│   └── models/           # Data models
├── data/
│   ├── samples/          # Sample EDI files
│   └── output/           # Generated output files
├── config/               # Configuration files
├── scripts/              # Utility scripts
└── tests/                # Test files
```

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config/config.py` to configure:
- Database connection settings
- EDI sender/receiver IDs
- File output paths

## Usage

### Generate EDI Files with Business Size Profiles

```python
from src.edi.generator import generate_edi_files, generate_edi_834, generate_edi_837, generate_edi_835

# Generate based on business size (automatic volume)
generate_edi_834(business_size="small")    # 50-200 members
generate_edi_834(business_size="medium")    # 500-3,000 members (default)
generate_edi_834(business_size="large")     # 10,000-50,000 members

# Generate all files for a business size
generate_edi_files(format="csv", business_size="medium")

# Manual override (exact counts)
generate_edi_834(num_members=500)
generate_edi_837(num_claims=1000)
```

### Output Formats

```python
# X12 format (default)
generate_edi_834(1000, format="x12")

# CSV format
generate_edi_834(1000, format="csv")
```

### Parse EDI Files

```python
from src.edi.parser import EDIParser

parser = EDIParser()
parser.connect_db()
parser.parse_edi_834('data/samples/edi_834_large_sample.txt')
parser.parse_edi_837('data/samples/edi_837_large_sample.txt')
parser.parse_edi_835('data/samples/edi_835_large_sample.txt')
parser.close_db()
```

### Generate Database Data

```python
from src.database.generator import generate_and_insert_data
import mysql.connector
from config.config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
generate_and_insert_data(conn, count=5)
conn.close()
```

## EDI Standards

This tool generates EDI files compliant with:
- **EDI 834**: Benefit Enrollment and Maintenance (X12 004010X095A1)
- **EDI 837**: Health Care Claim (X12 004010X098A1)
- **EDI 835**: Health Care Claim Payment/Advice (X12 004010X091A1)

## License

MIT License

