# CSV Format Documentation

## Overview

The EDI generators now support two output formats:
- **X12**: Standard EDI X12 format (default)
- **CSV**: Structured CSV format for easy data analysis and ETL pipelines

## Usage

### Basic Usage

```python
from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835

# Generate X12 format (default)
generate_edi_834(num_members=1000, output_file="output.edi", format="x12")

# Generate CSV format
generate_edi_834(num_members=1000, output_file="output.csv", format="csv")
```

## CSV Schemas

### EDI 834 (Enrollment) CSV Schema

**One row per member enrollment**

| Column | Description | Example |
|--------|-------------|---------|
| member_id | Unique member identifier | SUBMKX3RAT9 |
| subscriber_id | Subscriber ID (usually same as member_id) | SUBMKX3RAT9 |
| policy_number | Policy number | POL56699945 |
| ssn | Social Security Number | 375-62-9804 |
| last_name | Member last name | Vasquez |
| first_name | Member first name | Tesha |
| middle_initial | Middle initial | |
| date_of_birth | Date of birth (YYYY-MM-DD) | 1946-09-20 |
| gender | Gender (M/F) | M |
| street_address | Street address | 303 Austin Turnpike |
| city | City | McAllen |
| state | State abbreviation | MO |
| zip_code | ZIP code | 18741 |
| country | Country code | US |
| phone | Phone number | +1-843-324-1430 |
| email | Email address | assure2072@duck.com |
| coverage_status | Coverage status code | A |
| medicare_plan | Medicare plan code (if applicable) | |
| plan_id | Health plan ID | DH-P3109C |
| plan_name | Health plan name | Catastrophic Plan |
| plan_type | Plan type (PPO/HMO/HDHP/EPO) | HDHP |
| effective_date | Coverage effective date (YYYY-MM-DD) | 2024-11-09 |
| termination_date | Coverage termination date (YYYY-MM-DD) | |
| termination_reason | Termination reason code | |
| relationship_code | Relationship code (18=self) | 18 |
| transaction_type | Transaction type code | 024 |
| action_code | Action code | 2 |
| sponsor_id | Sponsor ID | SPON735884 |
| insurance_line | Insurance line code | HLT |

### EDI 837 (Claims) CSV Schema

**One row per claim**

| Column | Description | Example |
|--------|-------------|---------|
| claim_id | Unique claim identifier | CLM2025123456 |
| member_id | Member ID | SUBMKX3RAT9 |
| provider_id | Provider ID | PROVABC123 |
| provider_npi | Provider NPI | 1234567890 |
| provider_tax_id | Provider tax ID | TAX987654321 |
| provider_last_name | Provider last name | Smith |
| provider_first_name | Provider first name | John |
| provider_specialty | Provider specialty | Cardiology |
| provider_street | Provider street address | 123 Main St |
| provider_city | Provider city | New York |
| provider_state | Provider state | NY |
| provider_zip | Provider ZIP code | 10001 |
| member_last_name | Member last name | Vasquez |
| member_first_name | Member first name | Tesha |
| member_dob | Member date of birth (YYYY-MM-DD) | 1946-09-20 |
| member_gender | Member gender (M/F) | M |
| service_date | Service date (YYYY-MM-DD) | 2024-11-15 |
| billed_amount | Total billed amount | 1250.50 |
| claim_status | Claim status code | 1 |
| claim_frequency_code | Claim frequency code | 1 |
| claim_source_code | Claim source code | 01 |
| facility_type_code | Facility type code | 11 |
| location_type | Location type | OFFICE |
| procedure_code | Procedure code | 99213 |
| procedure_description | Procedure description | Office/outpatient visit est |
| diagnosis_codes | Diagnosis codes (pipe-separated) | J18.9\|E11.65 |
| submission_date | Submission date (YYYY-MM-DD) | 2024-11-20 |
| enrollment_id | Enrollment ID | ENR123456 |

### EDI 835 (Payment/Remittance) CSV Schema

**One row per payment**

| Column | Description | Example |
|--------|-------------|---------|
| payment_id | Unique payment identifier | PAY20241120123456 |
| claim_id | Claim ID | CLM2025123456 |
| member_id | Member ID | SUBMKX3RAT9 |
| provider_id | Provider ID | PROVABC123 |
| provider_npi | Provider NPI | 1234567890 |
| member_last_name | Member last name | Vasquez |
| member_first_name | Member first name | Tesha |
| billed_amount | Original billed amount | 1250.50 |
| paid_amount | Amount paid | 875.35 |
| allowed_amount | Allowed amount | 1000.00 |
| patient_responsibility | Patient responsibility | 124.65 |
| claim_status | Claim status code | 1 |
| claim_code | Claim code | A |
| adjustment_code | Adjustment code (if any) | CO |
| adjustment_amount | Adjustment amount (if any) | 50.00 |
| procedure_code | Procedure code | 99213 |
| service_date | Service date (YYYY-MM-DD) | 2024-11-15 |
| adjudication_date | Adjudication date (YYYY-MM-DD) | 2024-11-20 |
| check_number | Check/transaction number | CHK123456 |
| payment_date | Payment date (YYYY-MM-DD) | 2024-11-20 |
| payment_method | Payment method | ACH |
| payer_id | Payer ID | PAYER123 |
| transaction_reference | Transaction reference | REF987654321 |

## Data Consistency

- CSV data is generated using the **same logic** as X12 generation
- All dates are in ISO format (YYYY-MM-DD)
- Monetary amounts are formatted as strings with 2 decimal places
- Empty fields are represented as empty strings
- Diagnosis codes in 837 are pipe-separated (|)

## Use Cases

### Data Analysis
```python
import pandas as pd

# Load CSV for analysis
df = pd.read_csv('output.csv')
print(df.describe())
print(df.groupby('plan_type')['member_id'].count())
```

### ETL Pipelines
```python
# Generate CSV for data warehouse
generate_edi_834(10000, 'data/warehouse/enrollments.csv', format='csv')
generate_edi_837(claims_per_member=5, output_file='data/warehouse/claims.csv', format='csv')
generate_edi_835(5000, 'data/warehouse/payments.csv', format='csv')
```

### Testing
```python
# Generate test data in CSV for easy validation
generate_edi_834(100, 'tests/fixtures/test_enrollments.csv', format='csv')
```

## Examples

### Generate All Formats
```python
from src.edi.generator import generate_edi_files

# Generate X12 files
generate_edi_files(format="x12")

# Generate CSV files
generate_edi_files(format="csv")
```

### Custom Output Paths
```python
# Generate to custom location
generate_edi_834(
    num_members=500,
    output_file="data/export/enrollments_2024.csv",
    format="csv"
)
```

