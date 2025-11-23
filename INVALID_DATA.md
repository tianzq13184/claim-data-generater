# Invalid Data Generation

## Overview

The EDI generators support intentional generation of invalid data for testing data quality validation systems. This feature allows you to control the rate of invalid records statistically.

## Usage

### Basic Usage

```python
from src.edi.generator import generate_edi_834, generate_edi_837, generate_edi_835

# Generate with 5% invalid data
result = generate_edi_834(
    business_size="small",
    invalid_rate=0.05,  # 5% invalid records
    format="csv"
)

# Result includes metadata
print(f"Total records: {result['total_records']}")
print(f"Invalid records: {result['invalid_records']}")
print(f"Invalid rate: {result['invalid_rate']:.3f}")
```

### Default Behavior

If `invalid_rate` is not specified or set to 0.0, all generated data will be valid:

```python
# All data is valid (default)
result = generate_edi_834(100, format="csv")
# result['invalid_records'] will be 0
```

## Invalid Data Types

### EDI 834 (Enrollment)

1. **Missing DOB**: Date of birth field is empty
2. **Invalid Effective Date**: Effective date is in the future
3. **Start After End**: Membership start date is after termination date
4. **Invalid Gender Code**: Gender code is invalid (X, U, O, or empty)
5. **Wrong Plan ID**: Plan ID doesn't exist in the system

### EDI 837 (Claims)

1. **Charge Mismatch**: Total charge is less than sum of service line charges
2. **Invalid Diagnosis Code**: Diagnosis code format is invalid (e.g., "INVALID.999")
3. **Future Service Date**: Service date is in the future
4. **Invalid NPI Length**: NPI has wrong length (should be 10 digits)
5. **Negative Amount**: Billed amount is negative

### EDI 835 (Payments)

1. **Negative Payment**: Payment amount is negative
2. **Mismatched IDs**: Claim ID doesn't match the payment
3. **Invalid Adjustment Code**: Adjustment code is invalid
4. **Payment Exceeds Billed**: Payment amount exceeds billed amount

## Statistical Control

Invalid records are generated using statistical control, not random noise:

- Each record has a `invalid_rate` probability of being invalid
- If selected, one invalid data type is randomly chosen from the available types
- The actual invalid rate may vary slightly due to randomness, but will be close to the requested rate

## Return Format

When using CSV format, the generator returns a dictionary with metadata:

```python
{
    "output_file": "path/to/output.csv",
    "total_records": 1000,
    "invalid_records": 50,
    "invalid_rate": 0.050,
    "data": [...]  # List of CSV row dictionaries
}
```

## Examples

### Generate Test Data with Invalid Records

```python
# 10% invalid enrollment records
result_834 = generate_edi_834(
    num_members=500,
    invalid_rate=0.10,
    format="csv"
)

# 5% invalid claims
result_837 = generate_edi_837(
    num_claims=200,
    invalid_rate=0.05,
    format="csv"
)

# 15% invalid payments
result_835 = generate_edi_835(
    num_payments=100,
    invalid_rate=0.15,
    format="csv"
)
```

### Validate Data Quality

```python
result = generate_edi_834(1000, invalid_rate=0.05, format="csv")

# Check if invalid rate is within acceptable range
if result['invalid_rate'] > 0.06:
    print("Warning: Invalid rate exceeds expected threshold")
else:
    print(f"Data quality check passed: {result['invalid_rate']:.1%} invalid")
```

## Use Cases

1. **Data Quality Testing**: Test validation systems with known invalid data
2. **ETL Pipeline Testing**: Verify error handling in data pipelines
3. **Data Lake Validation**: Test data quality checks before ingestion
4. **Compliance Testing**: Ensure systems properly reject invalid EDI transactions

